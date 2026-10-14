# Design

## Context

Precedentes ya establecidos en el proyecto:
- `agents/code/app/github_app.py:54` y `agents/code/app/tools/github_repo.py:87,120` ya usan `httpx.AsyncClient(..., timeout=10.0/20.0)` para las llamadas a la API de GitHub.
- `backend/app/a2a_client.py:82-90` documenta en un comentario que el timeout por defecto de `httpx` (5s) causo un bug real, encontrado "verificando 6.7 en vivo contra el agente web real" -- la tarea tardaba mas que el timeout por defecto.
- `backend/app/a2a_client.py::DEFAULT_TASK_TIMEOUT_SECONDS = 120.0` es el limite superior de toda una tarea A2A (requisito "Limites de tiempo de la generacion" de `specs/exercise-generation/spec.md`): si un agente no responde en 120s, el backend la da por fallida.
- `backend/app/rate_limit.py` (propuesta `rate-limiting-backend`, en curso) ya usa `slowapi` con `Limiter`, limites expresados como `"N/minute"`, y un exception handler propio para `RateLimitExceeded` que devuelve `429` con un cuerpo minimo.

Dentro de una misma tarea A2A, algunos agentes hacen varias llamadas externas secuenciales antes de responder:
- `agents/code`: hasta 2 llamadas al LLM (elegir ficheros, analizar) mas hasta 10 lecturas de fichero (cada una ya con su propio timeout de 20s en `github_repo.py`).
- `agents/evaluator`/`agents/reviewer`: 1 llamada al LLM, con hasta 1 reintento si la justificacion se pasa de palabras (hasta 2 llamadas en el peor caso).
- `agents/web`: hasta 5 busquedas Tavily (compartiendo un unico `SearchBudget(max_calls=5)`, sin importar cuantas tecnologias se pidan) mas 1 llamada al LLM para resumir.

Ver proposal.md - Why para la motivacion completa.

## Goals / Non-Goals

**Goals:**
- Un timeout por llamada individual (LLM, Tavily) claramente por debajo de los 120s del limite de tarea del backend, para que una llamada colgada falle por si misma en vez de depender de que el backend corte la tarea entera desde fuera.
- Un limite de peticiones por IP en cada agente, con valores que no interfieran con el uso legitimo esperado.
- Reutilizar `slowapi` (ya una dependencia probada en el backend) en vez de introducir una libreria nueva.

**Non-Goals:**
- No se garantiza matematicamente que la suma de todos los timeouts individuales en el peor caso absoluto quede por debajo de 120s en todos los agentes (ver Risks) -- seria sobre-ingenieria para un escenario de colapso simultaneo de todas las llamadas de una tarea, cuando el limite de 120s del backend ya actua como ultimo respaldo en cualquier caso.
- No se cambia el limite de tarea A2A del backend (120s) ni los "budgets" internos existentes (`FileBudget`, `SearchBudget`).
- No se anade rate limiting a nivel de infraestructura (proxy/red); es complementario, igual que ya asume `rate-limiting-backend` para el backend.

## Decisions

### Timeout del cliente LLM: 45 segundos

**Alternativas consideradas:** un valor cercano a 120s (el limite de tarea) deja casi sin margen para una segunda llamada secuencial en `agents/code`/`evaluator`/`reviewer` (2x120s excederia el limite de tarea con holgura de sobra); un valor muy bajo (p. ej. 15s, igual que una llamada HTTP simple) arriesga cortar una generacion de verdad que tarde mas en picos de carga del proveedor del LLM -- en las verificaciones en vivo de este mismo proyecto (changes anteriores) las llamadas reales tardaron tipicamente unos segundos, pero sin margen de sobra ni holgura para un pico.

**Elegido:** 45s por llamada. Deja margen amplio sobre la latencia observada en las verificaciones en vivo (tipicamente unos segundos), y dos llamadas secuenciales (`agents/code`, `evaluator`/`reviewer` con reintento) suman 90s, dentro de los 120s del limite de tarea con margen para el resto del trabajo (lecturas de GitHub, parseo).

### Timeout del cliente Tavily: 15 segundos, aplicado por llamada en `search()`

Mismo criterio que ya aplica el proyecto a sus llamadas HTTP a GitHub (10-20s en `github_app.py`/`github_repo.py`): una busqueda Tavily es tipicamente mas rapida que una llamada al LLM, asi que 15s es generoso sin acercarse al limite de tarea, incluso en el peor caso de 5 busquedas secuenciales (75s) mas la llamada de resumen (45s) -- 120s exactos, el mismo limite del backend; ver Risks sobre este caso extremo.

`AsyncTavilyClient.__init__` no acepta un `timeout` de constructor (solo un `client: httpx.AsyncClient` propio, que requeriria construir uno a mano); su metodo `search()` si acepta `timeout` por llamada (el default de la libreria es 60s, demasiado cercano al limite de tarea si se encadenan varias busquedas). Se fija ahi, en `agents/web/app/tools/tavily_search.py::tavily_search` -- el unico punto donde se llama a `search()` en el agente.

### Rate limiting: `slowapi`, clave por IP, `60/minute` por defecto

**Libreria:** `slowapi`, igual que el backend (`rate-limiting-backend`) -- evita introducir una libreria nueva para el mismo problema, y el equipo ya conoce su integracion con FastAPI/Starlette.

**Clave: `get_remote_address` (por IP), no por usuario.** A diferencia del backend, un agente no tiene ningun usuario final autenticado que distinguir -- su unico llamador legitimo es el backend, identificado por la credencial de servicio compartida (`agent-auth`), no por un `profile.id` individual. Limitar por IP es aqui el equivalente correcto: en uso normal, toda peticion legitima llega desde la misma IP (el contenedor del backend), asi que el limite por IP actua de facto como un limite global por agente; en el escenario que motiva este requisito (autenticacion comprometida, o un bug que dispare un bucle de llamadas), sigue acotando el dano con independencia de si la credencial es valida.

**Limite: `60/minute` por defecto en los 5 agentes.** El backend usa `30/minute` como limite general para un humano con un boton; el trafico hacia un agente es maquina-a-maquina a traves de una sola instancia de backend que puede atender a varios tech leads/alumnos a la vez (varias generaciones o evaluaciones concurrentes), asi que el limite debe ser mayor. 60/minuto cubre con holgura una clase con decenas de alumnos enviando respuestas en el mismo minuto (cada envio dispara como mucho 2 llamadas A2A, a `evaluator` y `reviewer`), sin dejar de acotar un bucle de reintentos descontrolado.

**Handler de `RateLimitExceeded` propio**, igual que el backend: `429` con un cuerpo minimo, para no exponer detalles de configuracion.

### Orden del middleware: rate limiting antes de `ServiceAuthMiddleware`

El middleware de `slowapi` se monta antes que `ServiceAuthMiddleware` (`autenticacion-backend-agentes`) en la cadena, de forma que una peticion que supere el limite de tasa se rechace sin ni siquiera llegar a comparar la credencial -- mismo principio que ya aplica `ServiceAuthMiddleware` frente al handler de negocio: rechazar lo mas barato posible, lo antes posible.

## Risks / Trade-offs

- **[Riesgo] El peor caso absoluto de `agents/web` (5 busquedas Tavily a 15s + 1 llamada LLM a 45s = 120s) coincide exactamente con el limite de tarea del backend.** Si ese peor caso ocurriera de verdad, el backend podria cortar la tarea una fraccion de segundo antes de que el propio timeout del agente actuara. → *Mitigacion*: es un escenario extremo (las 6 llamadas colgandose al maximo permitido simultaneamente), no el caso tipico; el backend sigue siendo el respaldo final en cualquier caso, con o sin este cambio. No se ajustan los valores para cubrir ese extremo exacto porque hacerlo penalizaria el caso normal (acortando el timeout del LLM o de Tavily por debajo de lo que la latencia real observada justifica).
- **[Riesgo] `60/minute` por IP es, de facto, un limite global por agente** (todo el trafico legitimo viene de la misma IP). → *Aceptado*: es la limitacion correcta para el modelo de un unico llamador; si en el futuro varios backends distintos llaman al mismo agente, este valor habria que revisarlo (igual que el backend documenta para su propio escalado horizontal).
- **[Trade-off] Rate limiting en memoria (`MemoryStorage` de `slowapi`), sin almacen compartido.** Cada agente es un unico proceso (ver `docker-compose.yml`, sin replicas), asi que es coherente con la misma decision ya tomada para el backend en `rate-limiting-backend`.
