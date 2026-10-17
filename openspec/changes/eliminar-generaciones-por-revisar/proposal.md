# Proposal

## Why

En el primer listado de `/ejercicios` (generaciones pendientes) el tech lead solo puede revisar una generación `ready`; si no le interesa ninguna de las que generó, no tiene forma de descartarlas y la lista se le va acumulando sin fin. Se necesita poder eliminar la generación por revisar junto con sus ejercicios candidatos.

## What Changes

- Añadir un botón "Eliminar" a la derecha de "Revisar" en cada generación `ready` del primer listado de `/ejercicios`.
- Al pulsarlo, mostrar el diálogo de confirmación propio de la app advirtiendo que se van a eliminar los ejercicios correspondientes a esa generación.
- Nuevo endpoint `DELETE /generations/{generation_id}` que elimina una generación `ready` y todos sus ejercicios candidatos (no guardados); se rechaza si la generación no está `ready` o si alguno de sus ejercicios ya se guardó como definitivo.
- Tras confirmar, la generación desaparece del listado de pendientes y sus candidatos dejan de existir.

## Capabilities

### New Capabilities
<!-- Ninguna: la eliminación es parte del ciclo de vida de una generación. -->

### Modified Capabilities
- `exercise-generation`: se añade el requisito de eliminar una generación por revisar (y sus candidatos) desde el listado de pendientes.

## Impact

- Backend: `backend/app/routers/generations.py` (nuevo `DELETE /generations/{generation_id}`) y el script de verificación de generaciones.
- Frontend: `generations-api.service.ts` (nuevo `deleteGeneration`), `tech-lead/ejercicios/ejercicios.{ts,html}` con sus tests, y reutilización de `core/confirm-dialog`.
- Base de datos: sin migraciones; se reutilizan `generation`, `exercise` y `repo_access_log` existentes.