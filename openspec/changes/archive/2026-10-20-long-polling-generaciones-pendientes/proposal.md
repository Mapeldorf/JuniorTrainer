# Proposal

## Why

`/ejercicios` sondea `GET /generations` cada 3 s mientras haya alguna generación `generating`, y además consulta `GET /generations/{id}` de cada generación rastreada en cada ciclo (`frontend/src/app/tech-lead/ejercicios/ejercicios.ts`). Eso puede acercarse o superar el límite de frecuencia por defecto (30/min, `backend/app/rate_limit.py`), que se aplica a todos los endpoints autenticados; cuando un poll puntual recibe un `429` (u otro fallo transitorio), la pantalla lo muestra como si la carga hubiera fallado de verdad, aunque la generación siga en curso o ya haya terminado con normalidad. El sondeo frecuente es, además, trabajo de servidor y de red que casi siempre no tiene nada que reportar.

## What Changes

- Nuevo endpoint de espera larga, `GET /generations/pending/wait`, que responde en cuanto cambia el conjunto de generaciones pendientes (alguna pasa a `ready`/`error`/`done`) o, si no cambia nada, al cabo de un tiempo de espera acotado (p. ej. 25 s); en ambos casos devuelve el listado actual de pendientes, con el mismo contrato que `GET /generations`.
- El orquestador (`_mark_status` en `app/orchestrator.py`) señaliza, al cambiar el estado de una generación, a quien esté esperando ese cambio.
- El frontend sustituye el `setInterval` de 3 s por llamadas sucesivas a este endpoint: pide, espera la respuesta (ya sea por cambio o por timeout) y vuelve a pedir inmediatamente. El numero de peticiones por minuto baja a, como mucho, una cada ~25 s mientras no haya cambios.
- El sondeo adicional de `GET /generations/{id}` por cada generación rastreada (`checkTrackedGenerations`) deja de hacer falta en cada ciclo: se resuelve con la misma respuesta de espera larga, que ya refleja los cambios de estado.

## Capabilities

### Modified Capabilities

- `exercise-generation`: el requisito "Listar las generaciones pendientes" se amplía con un mecanismo de espera larga para detectar cambios sin sondeo frecuente; el comportamiento observable del listado (qué generaciones aparecen) no cambia.

## Impact

- Backend: nuevo endpoint en `app/routers/generations.py`; nuevo mecanismo de notificación en memoria (por `generation_id` o compartido) en `app/orchestrator.py` o un módulo propio; sigue sujeto al límite de frecuencia por defecto (ninguna excepción nueva en `app/rate_limit.py`).
- Frontend: `frontend/src/app/tech-lead/ejercicios/ejercicios.ts` (sustituye el polling por espera larga) y `frontend/src/app/core/generations-api.service.ts` (nuevo método de cliente); `GenerationTrackerService` puede simplificarse si la espera larga ya informa de las generaciones rastreadas que terminan en `error`.
- Sin cambios de esquema de base de datos ni de contrato de `GET /generations` o `GET /generations/{id}` (se mantienen para la carga inicial y para consultar una generación concreta).
