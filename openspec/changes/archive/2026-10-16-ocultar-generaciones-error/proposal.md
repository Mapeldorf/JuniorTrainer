# Proposal

## Why

En `/ejercicios`, la lista de generaciones pendientes incluye hoy las que están en estado `error` (el backend solo excluye `done`), mostrando una fila que el tech lead no puede accionar: no se puede revisar ni cerrar, y en la práctica solo añade ruido a la pantalla. Además, cuando una generación falla, el tech lead no recibe ninguna señal clara: la fila aparece (o desaparece) sin explicar que la generación no llegó a producir candidatos.

## What Changes

- El backend deja de devolver las generaciones en estado `error` en `GET /generations`: el listado pasa a incluir únicamente las que están en curso (`generating`) o listas para revisar (`ready`). Las generaciones fallidas se siguen guardando en la base de datos y siguen siendo consultables por `GET /generations/{id}`.
- El frontend nunca muestra una generación en error en la lista de `/ejercicios` (ya no las recibe).
- El frontend avisa cuando una generación lanzada desde este navegador termina en error, mediante un mensaje de error agregado en la interfaz (por ejemplo, "1 generación ha fallado"). El componente concreto se decide en design.md según buenas prácticas de UX/UI.
- Fuera de alcance: no se cambia el estado `error` en sí, ni el mensaje de la causa que devuelve `GET /generations/{id}`, ni la pantalla `/ejercicios/:generationId/revisar`, ni el mecanismo que marca una generación como fallida.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `exercise-generation`: cambia el requisito "Listar las generaciones pendientes" (excluye las generaciones en `error`) y se añade un requisito para el aviso en la interfaz cuando una generación falla.

## Impact

- `backend/app/routers/generations.py`: `list_pending_generations` filtra también el estado `error`.
- `backend/app/schemas/generation.py`: se actualiza la documentación de `GenerationSummary` (ya no describe filas en `error`).
- `backend/scripts/verify_ejercicios_tech_lead.py`: el caso que hoy espera ver `ready` y `error` en `GET /generations` pasa a esperar solo `ready`.
- `frontend/src/app/tech-lead/ejercicios/ejercicios.ts` y `.html`: seguimiento de las generaciones lanzadas y aviso agregado al fallar.
- `frontend/src/app/core/generations-api.service.ts` (si hace falta un método de consulta de estado puntual) y su modelo.
- `frontend/src/app/tech-lead/ejercicios/ejercicios.spec.ts`: nuevos casos para el aviso y para la ausencia de generaciones en error.
- `openspec/specs/exercise-generation/spec.md`: delta de los requisitos afectados.
