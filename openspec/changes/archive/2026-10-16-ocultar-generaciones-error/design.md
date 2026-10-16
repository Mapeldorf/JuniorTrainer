# Design

## Context

Ver `proposal.md` - Why. Puntos de partida relevantes:

- `GET /generations` (`backend/app/routers/generations.py`) hoy devuelve todas las generaciones con `status != 'done'`, es decir incluye `error`. El contrato (`GenerationSummary`) expone `error_message`, que en el listado pasa a ser siempre `null` una vez excluidas las fallidas.
- El frontend (`frontend/src/app/tech-lead/ejercicios/ejercicios.ts`) hace polling de `listPending()` cada 3 s mientras alguna generación esté en `generating`, y ya tiene una señal `error` que pinta un `alert-error` para fallos de carga.
- `POST /generations` responde de inmediato con `{ id }`, pero `GenerarComponent` descarta hoy ese `id` (solo navega a `/ejercicios`). La generación se sabe fallida únicamente consultando `GET /generations/{id}` (`getDetail`), que sigue devolviendo `status` y `error_message`.
- No existe ningún mecanismo que asocie a la persona con las generaciones que lanzó: `GET /generations` es global para tech leads (design.md decision 2 de `frontend-tech-lead-ejercicios`).

## Goals / Non-Goals

**Goals:**

- El listado de `/ejercicios` no contiene nunca generaciones en `error`.
- Cuando una generación lanzada desde la sesión del tech lead falla, aparece un aviso de error agregado en la interfaz, sin exponer detalles técnicos ni bloquear el resto de la pantalla.
- Mantener el contrato de `GET /generations/{id}` intacto (sigue devolviendo el estado y el mensaje de causa).

**Non-Goals:**

- No se añade una pantalla ni un historial para consultar las generaciones fallidas (siguen solo en la base de datos).
- No se cambia qué marca una generación como `error` (orquestador/agentes).
- No se persiste el aviso entre recargas ni se sincroniza entre pestañas/dispositivos.

## Decisions

### Decisión 1: El backend excluye `error` en el listado

`list_pending_generations` filtra por estado `generating` o `ready` (`.in_("status", ["generating", "ready"])`) en vez de `neq("status", "done")`. Se mantiene `error_message` en `GenerationSummary` para no ampliar el contrato más de lo necesario; en la práctica siempre será `null` en este listado.

- Alternativas consideradas: devolver las fallidas en un campo aparte (`{ pending, failed_count }`) para que el frontend contara sin rastrear nada. Descartada: cambia la forma de la respuesta y la decisión del usuario es que el listado nunca traiga las fallidas y que el aviso salga del propio frontend.

### Decisión 2: El frontend rastrea las generaciones que lanza la sesión

`GenerarComponent`, tras un `POST /generations` correcto, registra el `id` devuelto en un servicio ligero `GenerationTrackerService` que persiste el conjunto de ids sin resolver en `sessionStorage` (clave propia, p. ej. `pendingGenerationIds`). En `/ejercicios`, además del listado, el componente consulta `getDetail(id)` de cada id rastreado:

- `error` → incrementa el recuento de fallos, muestra el aviso agregado y deja de rastrear ese id.
- `ready` → deja de rastrear el id (aparecerá en el listado de pendientes).
- `generating` → lo mantiene rastreado.
- `404`/error de red → deja de rastrear el id para no reintentar indefinidamente.

El polling cada 3 s se mantiene mientras haya alguna generación en `generating` **o** queden ids rastreados por resolver.

- Por qué `sessionStorage`: la generación pertenece a la sesión de navegador que la lanzó (los escenarios del requisito hablan de "una generación lanzada desde la sesión"); sobrevive a una recarga de `/ejercicios` sin obligar a registrar a la persona ni a cambiar el backend.
- Alternativas consideradas: deducir el fallo porque un id `generating` desaparece del listado. Descartada: falla si la generación cae antes del primer `listPending()` y no distingue la causa de la desaparición.

### Decisión 3: Aviso agregado como banner no bloqueante y descartable

El aviso es un banner `role="alert"` en la parte superior de `/ejercicios`, con el recuento ("N generación(es) ha(n) fallado...") y un botón para descartarlo. Reutiliza el estilo `alert-error` ya presente en la plantilla para fallos de carga, pero en una señal propia (`generationFailures` / `failureNotice`) separada de la señal `error` existente, para no mezclar el aviso de fallo de generación con errores de carga de datos.

- Por qué un banner y no un toast/diálogo: el fallo no requiere una acción inmediata del tech lead (no hay nada que resolver en la propia pantalla) y un `role="alert"` es accesible, no modal y no interrumpe; encaja con el patrón de avisos ya usado en la aplicación (`alert-error`).
- Alternativas consideradas: incluir el `error_message` de cada fallo. Descartada por decisión del usuario (aviso general agregado) y para no exponer detalles técnicos.
- El aviso no se persiste: se muestra en el momento en que se detecta el fallo y desaparece al descartarlo o al recargar (los ids rastreados ya resueltos dejan de consultarse). Persistirlo queda fuera de alcance.

### Decisión 4: Servicio dedicado para el rastreo

`core/generation-tracker.service.ts` (inyectable, `providedIn: 'root'`) con `add(id)`, `list()` y `remove(id)`, envolviendo `sessionStorage`. Se separa de `GenerationsApiService` (que habla con la API) y se puede sustituir en los tests sin tocar `sessionStorage`.

## Risks / Trade-offs

- [El aviso solo cubre generaciones lanzadas desde esta sesión de navegador] → Aceptado: el requisito se define así; las generaciones fallidas de otras personas/equipos no se anuncian, pero tampoco se muestran en el listado.
- [Una sesión con muchos ids rastreados añade llamadas a `GET /generations/{id}` en cada tick] → Los ids se eliminan en cuanto resuelven (listo/error/404); el volumen por sesión es bajo (lanzamientos manuales de un tech lead).
- [`sessionStorage` no disponible o bloqueado] → El servicio maneja el fallo degradando a un conjunto en memoria; como mucho se pierde el aviso tras una recarga, sin romper la pantalla.
- [Excluir `error` del listado quita visibilidad de diagnósticos] → Aceptado por el usuario: la causa sigue en `GET /generations/{id}` y en la base de datos.

## Open Questions

Ninguna.
