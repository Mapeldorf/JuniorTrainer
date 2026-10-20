# Design

## Context

Ver `proposal.md` - Why. Puntos de partida relevantes:

- El backend corre como un único proceso uvicorn sin `--workers` (`backend/Dockerfile`), igual que ya asume `POST /generations` al lanzar la orquestación con `BackgroundTasks` en el mismo proceso (`app/orchestrator.run_generation`, `app/routers/generations.py`): no hace falta coordinar entre procesos, un estado en memoria del propio proceso basta.
- `_mark_status(generation_id, status, error_message=None)` (`app/orchestrator.py`) es el único punto que escribe el cambio de estado de una generación a `ready`/`error` en Supabase; es una llamada síncrona (cliente `service_role`), sin await.
- `GET /generations` (`list_pending_generations`) ya consulta `generation` filtrando por `status in (generating, ready)`, ordenado por `created_at desc`; esa misma consulta es la que debe repetirse al final de la espera larga, cambie algo o no.
- El límite de frecuencia por defecto (30/min por usuario, `app/rate_limit.py`, aplicado globalmente por `SlowAPIMiddleware`) sigue aplicando sin excepción (requisito "Limite por defecto en endpoints autenticados" de `api-rate-limiting`); el diseño tiene que funcionar dentro de ese límite, no esquivarlo.
- El frontend (`frontend/src/app/tech-lead/ejercicios/ejercicios.ts`) hoy gestiona el polling con `setInterval`/`clearInterval` (`pollHandle`) y además, por cada id rastreado en `GenerationTrackerService` (sesión que lanzó esa generación), hace un `GET /generations/{id}` en cada ciclo (`checkTrackedGenerations`) para detectar las que terminan en `error` (ocultas del listado).
- `GenerationsApiService` es un servicio Angular fino, un método HTTP por endpoint, sin lógica de reintento ni de temporizado (eso vive en el componente).

## Goals / Non-Goals

**Goals:**

- Que `/ejercicios` deje de generar una petición cada 3 s mientras haya una generación en curso, sustituyéndolo por, como mucho, una petición cada ~25 s sin cambios, más una inmediata en cuanto algo cambia.
- Que un único mecanismo (la respuesta de la espera larga) baste para detectar tanto que una generación pasa a `ready`/`done` como que pasa a `error` (hoy repartido entre el listado y `checkTrackedGenerations`).
- Mantener intacto el contrato de `GET /generations` y `GET /generations/{id}` (la carga inicial de `/ejercicios` sigue usando el primero; el detalle de una generación concreta, el segundo).

**Non-Goals:**

- No se introduce WebSocket, SSE ni ningún bus de mensajería entre procesos (Redis, Supabase Realtime): el proceso único en memoria basta (ver Context) y es explícitamente la alternativa descartada en la conversación que origina este cambio.
- No se cambia el límite de frecuencia por defecto ni se exime a este endpoint de él.
- No se añade un historial ni una pantalla nueva: la UI sigue siendo la lista de pendientes existente, solo cambia cómo se mantiene actualizada.
- No se rediseña `GenerationTrackerService`; si la espera larga vuelve redundante alguna de sus consultas, se simplifica como efecto colateral, pero su propósito (distinguir las generaciones lanzadas por esta sesión) no cambia.

## Decisions

### Decisión 1: Un `asyncio.Event` por `generation_id` activo, en un registro en memoria del propio proceso

Un módulo nuevo (p. ej. `app/generation_events.py`) mantiene un `dict[str, asyncio.Event]` protegido por las garantías de un único hilo del event loop (no hace falta `Lock`: todo el acceso ocurre en coroutines del mismo loop). `_mark_status` publica el cambio con `notify_status_change(generation_id)`, que marca (`.set()`) el evento de esa generación si existe y lo retira del registro. El endpoint de espera larga crea un evento para cada generación que esté en `generating` en el momento de empezar a esperar, y espera con `asyncio.wait(..., timeout=...)` a que cualquiera de ellos se active o se agote el tiempo.

- Alternativas consideradas: un único `asyncio.Event` global que se reinicia cada vez que cambia cualquier generación. Descartado: una generación que cambia justo después de que el endpoint ya ha leído el listado pero antes de empezar a esperar el evento se perdería (condición de carrera); por generación, el endpoint comprueba el listado actual y solo espera las que sigan en `generating`, cerrando esa ventana.
- Alternativas consideradas: sondear la base de datos cada N segundos dentro del propio endpoint (polling del lado servidor en vez de notificación). Descartado: cambia la latencia de detección de "inmediata" a "cada N segundos" sin ahorrar carga real sobre Supabase, y no usa la ventaja de que `_mark_status` ya sabe en el instante exacto en que algo cambia.

### Decisión 2: Un único endpoint, `GET /generations/pending/wait`, que reconsulta el listado completo al final

El endpoint:
1. Ejecuta la misma consulta que `list_pending_generations` (listado de `generating`/`ready`).
2. Si no hay ninguna en `generating`, no hay nada que esperar: responde de inmediato con ese listado (igual que hoy sin generaciones en curso).
3. Si hay alguna en `generating`, espera (con `asyncio.wait_for` o `asyncio.wait` con `timeout`) a que se active el evento de cualquiera de ellas, hasta el tiempo de espera acotado (mismo orden de magnitud que otros timeouts del sistema; propuesto 25 s, por debajo de timeouts típicos de proxy/navegador de 30 s).
4. Tanto si hubo cambio como si se agotó el tiempo, vuelve a ejecutar la consulta y la devuelve — nunca devuelve el listado "antes" de refrescarlo, para no arrastrar un estado obsoleto tras detectar el cambio.

La ruta es nueva (`/generations/pending/wait`, bajo el mismo prefijo que el resto de `generations.py`) y no sustituye a `GET /generations`, que sigue existiendo para la carga inicial y para cualquier consumidor que solo quiera el estado actual sin esperar.

- Alternativas consideradas: parametrizar `GET /generations` con `?wait=true`. Descartado: mezclaría dos semánticas muy distintas (responder ya / esperar hasta 25 s) en el mismo endpoint, complicando su documentación y su comportamiento ante clientes que no esperan una espera larga.
- Alternativas consideradas: que el endpoint reciba la lista de ids a vigilar (en vez de recalcularla él mismo). Descartado: el frontend no necesita decidir qué vigilar — las reglas de qué es "pendiente" ya viven en el backend (`list_pending_generations`), y pasarlas por parámetro duplicaría esa lógica sin necesidad.

### Decisión 3: El frontend sustituye `setInterval` por una cadena de peticiones autoiniciada

`EjerciciosComponent` reemplaza `loadPending()` (llamada en bucle por `setInterval`) por un bucle de petición-respuesta: tras recibir la respuesta de `GET /generations/pending/wait` (por cambio o por timeout), si sigue habiendo alguna generación `generating`, lanza inmediatamente la siguiente llamada; si no, se detiene (igual que hoy `updatePolling()` decide si seguir sondeando). No hace falta `pollHandle`/`clearInterval`: el propio flujo de peticiones encadenadas termina cuando no hay nada que esperar.

- Por qué no mantener el `setInterval` y simplemente apuntarlo al endpoint nuevo: el objetivo es que cada petición ya lleve implícita la espera (hasta 25 s) — un timer de 3 s seguiría generando peticiones de sobra mientras la de espera larga sigue abierta, duplicando carga sin motivo.
- `checkTrackedGenerations()` deja de necesitar su propio ciclo de `GET /generations/{id}`: en cuanto una generación rastreada deja de estar en `generating`, la respuesta de la espera larga ya lo refleja (aparece en `ready`, o desaparece por pasar a `error`, igual que hoy distingue el listado). Solo hace falta seguir distinguiendo "desapareció por `error`" de "desapareció por otra causa" con una consulta puntual a `GET /generations/{id}` de los ids que desaparecen, no en cada ciclo sino solo cuando eso ocurre.
- El manejo de errores de red/HTTP de cada llamada se mantiene conceptualmente igual que hoy (banner de carga si la primera llamada falla); una llamada de espera larga que falla (p. ej. un `429` si, por lo que sea, se encadenan más peticiones de las esperadas) se reintenta igual que cualquier petición fallida, sin diseñar aquí ningún backoff especial.

### Decisión 4: El timeout del lado servidor queda por debajo del timeout HTTP del cliente

El timeout de espera del endpoint (propuesto 25 s) se fija explícitamente por debajo de cualquier timeout de proxy/navegador razonable (típicamente ≥30s), para que el endpoint responda siempre por sí mismo antes de que el cliente lo corte, y porque convertir esto en una conexión "casi persistente" (varios minutos) no es el objetivo — sigue siendo una petición HTTP normal de corta duración, solo que puede tardar hasta 25 s en responder si no hay cambios.

## Risks / Trade-offs

- [El registro en memoria de eventos no sobrevive a un reinicio del proceso] → Aceptado, mismo supuesto que ya asume `BackgroundTasks` para la propia generación: una petición en espera que coincide con un reinicio simplemente no recibe respuesta y el cliente la reintenta (mismo comportamiento que un timeout de red cualquiera).
- [Varias pestañas/sesiones del mismo tech lead esperando la misma generación] → Cada petición de espera larga crea su propia espera sobre el mismo evento; `asyncio.Event` admite múltiples esperas concurrentes sin problema, y cada una se resuelve de forma independiente.
- [Una petición de espera larga que se corta del lado del cliente (el tech lead cierra la pestaña) deja una tarea esperando en el servidor] → FastAPI/Starlette cancela la corutina del handler cuando el cliente se desconecta; la espera (`asyncio.wait_for`) se cancela con ella, sin dejar nada pendiente.
- [Seguir sujeto al límite de 30/min de todas formas] → Aceptado y buscado (ver Non-Goals): con como mucho una petición cada ~25 s por generación en curso, el volumen queda muy por debajo del límite incluso sumando el resto de tráfico normal de la pantalla.

## Open Questions

Ninguna.
