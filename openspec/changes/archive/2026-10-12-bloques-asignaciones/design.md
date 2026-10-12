# Design

## Context

Ver `proposal.md` - Why. El esquema de Supabase ya tiene, desde `infra/supabase/migrations/0001_schema.sql`, las tablas `exercise` (con `saved`/`deleted_at`), `block`, `block_exercise`, `assignment` y `assignment_exercise`, con sus triggers de inmutabilidad y sus policies de RLS (tech lead gestiona, alumno solo lee lo suyo) ya aplicados. Nadie los escribe todavia: el backend FastAPI solo tiene auth (`backend/app/routers/users.py`, `health.py`) y generacion de candidatos (`generations.py`), que inserta `exercise` con `saved = false` por defecto y nunca lo cambia. Este change anade la capa de aplicacion (endpoints FastAPI) que falta sobre ese esquema, mas una migracion pequena para la unica regla de negocio que el esquema todavia no cubre (bloqueo de edicion de un bloque ya resuelto).

Patron ya establecido en el proyecto (`generations.py`, `users.py`, `deps.py`): los endpoints usan el cliente `service_role` (`get_admin_client()`) y hacen las comprobaciones de rol con `Depends(require_tech_lead)`; las invariantes de datos (inmutabilidad, relaciones validas) se aplican con triggers en Postgres, no en Python, para que valgan sin importar quien escriba en la tabla.

## Goals / Non-Goals

**Goals:**
- Exponer endpoints FastAPI para guardar/listar/eliminar ejercicios definitivos, y para crear/editar/listar/eliminar bloques y sus asignaciones, siguiendo el patron ya establecido (`Depends(require_tech_lead)`, cliente admin, schemas Pydantic).
- Anadir la unica regla de negocio que falta en base de datos: un bloque con alguna `answer` registrada en cualquiera de sus asignaciones se vuelve inmutable (nombre y composicion), igual que ya son inmutables `exercise` (al guardarse), `assignment_exercise` y `answer`.

**Non-Goals:**
- Paginacion u ordenacion avanzada en los listados (`GET /exercises`, `GET /blocks`): el volumen esperado (un bootcamp) no la justifica todavia; se puede anadir despues sin romper el contrato.
- Busqueda de texto mas alla de un `ILIKE` simple sobre el enunciado.
- Cualquier dato de valoracion/veredicto en el progreso de una asignacion (`GET /blocks/{id}/assignments`): el campo ya existe en `answer.verdict`, pero no se usa hasta "valoracion-respuestas".
- El endpoint de respuesta del alumno, los agentes evaluador/revisor, y frontend (ya excluidos en `proposal.md` - Impact).

## Decisions

**Guardar/eliminar un ejercicio y gestionar bloques van en dos routers nuevos, no en `generations.py`.** `backend/app/routers/exercises.py` (ciclo de vida de un ejercicio ya generado: guardar, listar definitivos, eliminar) y `backend/app/routers/blocks.py` (bloques y sus asignaciones). `generations.py` sigue siendo solo sobre generar candidatos; mezclar "guardar un candidato" ahi acoplaria dos capacidades (`exercise-generation` y `exercise-catalog`) que la spec ya separa.

**El bloqueo de edicion de un bloque resuelto se aplica con un trigger, igual que las demas inmutabilidades, no solo en el backend.** Alternativa descartada: comprobarlo unicamente en el endpoint FastAPI antes de actualizar. Se descarta porque el proyecto ya establecio el patron de que las invariantes de datos viven en Postgres (`exercise_lock_after_saved`, `block_exercise_requires_saved`, `reject_update` en `0001_schema.sql`) para que valgan sin importar quien escriba en la tabla; una comprobacion solo en Python se podria saltar con un acceso directo a la base de datos.

Implementacion concreta (migracion `0005_block_lock_after_answered.sql`):
- Funcion `public.block_has_answers(p_block_id uuid) returns boolean` (`stable`, `security invoker`): `EXISTS` que junta `assignment` (por `block_id`) con `answer` (por `assignment_id`).
- Trigger `block_lock_after_answered_trg` `BEFORE UPDATE ON block`: si `block_has_answers(old.id)` y `new.name` distinto de `old.name`, lanza excepcion (mismo patron que `exercise_lock_after_saved`: solo bloquea el campo que cambia, `deleted_at` sigue libre).
- Trigger `block_exercise_lock_after_answered_trg` `BEFORE INSERT OR DELETE ON block_exercise`: si `block_has_answers(new.block_id)` (insert) o `block_has_answers(old.block_id)` (delete), lanza excepcion.

**`PATCH /blocks/{id}` sobre la composicion es un reemplazo completo, no un diff de anadir/quitar.** El tech lead manda la lista completa de `exercise_id` que debe quedar en el bloque; el endpoint borra los `block_exercise` que ya no esten en esa lista e inserta los que falten, recalculando `position` segun el orden recibido. Alternativa descartada: aceptar listas separadas de `add`/`remove`. Se descarta por anadir complejidad (resolver conflictos de `position`) sin que la spec lo pida; el reemplazo completo es mas simple y de todas formas solo es posible mientras el bloque no tenga respuestas (el trigger anterior ya lo impide despues).

**La copia de `block_exercise` a `assignment_exercise` al asignar se hace en el backend con una lectura + una insercion por lotes, no con una funcion RPC en Postgres.** El endpoint `POST /blocks/{id}/assignments` lee los `block_exercise` del bloque (como mucho 100 filas) y hace una unica llamada `.insert()` del cliente Supabase con la lista completa de filas para `assignment_exercise` (un unico `INSERT ... VALUES` multi-fila en el servidor, atómico). Alternativa considerada: una funcion Postgres `assign_block_to_student(block_id, student_id)` llamada por RPC. Se descarta porque el proyecto no usa RPC para logica de negocio todavia (las funciones existentes son solo para triggers) y una insercion por lotes ya es atomica sin anadir ese patron nuevo.

**Asignar a varios alumnos en una sola peticion procesa cada alumno por separado, no todo-o-nada.** `POST /blocks/{id}/assignments` recibe una lista de `student_id`; por cada uno, si ya tiene el bloque asignado se omite (sin crear una segunda asignacion, segun la spec) y se informa en la respuesta cual se creo y cual ya existia, en vez de que un alumno ya asignado haga fallar la asignacion de los demas.

**`GET /exercises` y `GET /blocks` filtran en el backend con los mismos parametros que ya usa `generations.py` para construir queries (`eq`, `ilike`), no con busqueda de texto completo (`tsvector`).** No hay un requisito de rendimiento que lo justifique todavia.

## Risks / Trade-offs

[Riesgo] Reemplazar toda la composicion de un bloque en cada `PATCH` (borrar + insertar) podria interpretarse como una perdida de historial de que ejercicios tuvo antes → Mitigacion: no hace falta ese historial (la spec solo pide que la copia de una asignacion ya creada no cambie, y esa copia vive en `assignment_exercise`, no en `block_exercise`); el bloque en si no necesita conservar versiones anteriores de su composicion.

[Riesgo] `block_has_answers` hace un `JOIN` en cada `UPDATE`/`INSERT`/`DELETE` sobre `block`/`block_exercise` → Mitigacion: el volumen esperado (bloques y asignaciones de un bootcamp) es bajo y ambas tablas ya tienen los indices necesarios (`assignment_student_id_idx`, `answer_assignment_id_idx`) para que el `EXISTS` sea barato.

[Riesgo] Procesar la asignacion multiple sin todo-o-nada puede dejar una peticion con asignaciones parcialmente creadas si falla a mitad de lista (p. ej. un `student_id` invalido) → Mitigacion: validar que todos los `student_id` existen y tienen `role = student` antes de crear ninguna asignacion; solo se omiten (no se fallan) los que ya estaban asignados a ese bloque.
