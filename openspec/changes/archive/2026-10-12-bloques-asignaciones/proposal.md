# Proposal

## Why

El tech lead ya puede generar ejercicios candidatos, pero el sistema no tiene forma de convertir uno en definitivo, de agruparlos en bloques ni de asignarlos a sus alumnos: faltan los endpoints que implementan el paso 3 del plan de trabajo (seccion 13), sobre un modelo de datos de ejercicios/bloques/asignaciones que ya existe en la base de datos desde la migracion inicial (`exercise.saved`, `block`, `block_exercise`, `assignment`, `assignment_exercise`) pero que nadie escribe ni expone todavia. Sin esto, un ejercicio generado no llega nunca a un alumno.

## What Changes

- `POST /exercises/{id}/save` (solo tech lead): marca un ejercicio candidato (`saved = false`) como definitivo (`saved = true`); a partir de ahi la base de datos ya lo hace inmutable salvo `deleted_at` (regla existente desde la migracion inicial).
- `GET /exercises` (solo tech lead): lista los ejercicios guardados y no eliminados, filtrable por tipo y buscable por texto en el enunciado — es la fuente para componer un bloque.
- `PATCH /exercises/{id}` con `deleted_at` (borrado logico, solo tech lead): un ejercicio eliminado deja de poder anadirse a bloques nuevos (la base de datos ya rechaza esa insercion desde la migracion inicial; falta el endpoint que expone la accion), sin afectar a los bloques que ya lo contengan ni a copias de asignacion ya creadas.
- `POST /blocks`, `GET /blocks`, `GET /blocks/{id}`, `PATCH /blocks/{id}`, `DELETE /blocks/{id}` (solo tech lead): crear un bloque (nombre + de 1 a 100 ejercicios guardados), listarlo/verlo, editar su nombre y/o su composicion, y eliminarlo (borrado logico, pasa a "Bloques eliminados": ya no se puede asignar pero sigue en solo lectura con sus resultados, y los alumnos que ya lo tenian asignado no notan el cambio).
- Regla de negocio nueva: un bloque con al menos una `answer` registrada en cualquiera de sus asignaciones deja de poder editarse (nombre o composicion); se aplica con un trigger en base de datos, en el mismo estilo que las inmutabilidades ya existentes de `exercise`/`assignment_exercise`/`answer`, no solo como validacion en el backend.
- `POST /blocks/{id}/assignments` (solo tech lead): asigna un bloque a uno o varios alumnos. Cada asignacion copia en ese momento los `block_exercise` del bloque a `assignment_exercise` (la copia inmutable que el esquema ya soporta), de modo que una edicion o el borrado logico posterior del bloque, o de alguno de sus ejercicios, no afecta a lo que ya ve un alumno asignado.
- `GET /blocks/{id}/assignments` (solo tech lead): progreso por alumno asignado — de momento solo si cada ejercicio de su copia tiene o no una `answer` (el campo de valoracion/veredicto de `answer` queda sin usar hasta el cambio "valoracion-respuestas").
- Fuera de alcance (van en el cambio siguiente, "valoracion-respuestas"): el endpoint con el que un alumno envia su respuesta a un ejercicio, los agentes evaluador/revisor, y cualquier pantalla de frontend.

## Capabilities

### New Capabilities
- `exercise-catalog`: ciclo de vida de un ejercicio una vez generado — convertirlo en definitivo, listarlo/buscarlo entre los definitivos, y eliminarlo logicamente de la app sin afectar a donde ya se use.
- `exercise-blocks`: ciclo de vida de un bloque de ejercicios definitivos — crearlo, editar su nombre y su composicion mientras nadie lo haya resuelto, listarlo/verlo y eliminarlo logicamente sin afectar a quien ya lo tiene asignado.
- `block-assignment`: asignar un bloque a alumnos con copia inmutable de sus ejercicios en el momento de asignar, y consultar el progreso de respuesta (sin valoracion todavia) de cada alumno asignado.

### Modified Capabilities
- `data-authorization`: anade el requisito de que un bloque con alguna `answer` ya registrada en cualquiera de sus asignaciones se vuelve inmutable (nombre y composicion), junto a las inmutabilidades de `exercise`, `assignment_exercise` y `answer` que ya cubria.

## Impact

- Backend: nuevo `backend/app/routers/exercises.py` (guardar/listar/eliminar) y nuevo `backend/app/routers/blocks.py` (bloques y asignaciones), con sus schemas Pydantic en `backend/app/schemas/`.
- Base de datos: una migracion nueva en `infra/supabase/migrations/` que anade el trigger de bloqueo de edicion de `block`/`block_exercise` tras la primera respuesta; no se tocan las tablas ni los triggers existentes.
- Sin cambios de frontend ni de CI/CD (fuera de alcance de este change).
