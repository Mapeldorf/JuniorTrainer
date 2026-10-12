# Tasks

## 1. Migracion: bloqueo de edicion de un bloque ya resuelto

- [x] 1.1 Escribir `infra/supabase/migrations/0005_block_lock_after_answered.sql` con `block_has_answers(p_block_id uuid)`, el trigger `block_lock_after_answered_trg` en `block` (bloquea `name` si hay alguna `answer`) y `block_exercise_lock_after_answered_trg` en `block_exercise` (bloquea insert/delete si hay alguna `answer`), segun `design.md` - Decisions
- [x] 1.2 Aplicar la migracion al proyecto Supabase del change anterior (`uwgqxdfpkkbenmynwlmk`) con `apply_migration` y verificar con `execute_sql` que un `UPDATE` de `name` o un `INSERT`/`DELETE` en `block_exercise` fallan para un bloque con una `answer` de prueba, y que el mismo `UPDATE`/`INSERT`/`DELETE` funciona para un bloque sin respuestas
- [x] 1.3 Revisar `get_advisors` tras la migracion y corregir cualquier aviso nuevo de seguridad (mismo patron que `0002_harden_functions.sql`: `search_path` fijo en `block_has_answers`)

## 2. Ejercicios definitivos (exercise-catalog)

- [x] 2.1 `backend/app/schemas/exercise.py`: anadir los modelos de peticion/respuesta que falten para guardar, listar y eliminar ejercicios (reutilizar `ExerciseCandidate` de `schemas/generation.py` donde aplique)
- [x] 2.2 `backend/app/routers/exercises.py`: `POST /exercises/{id}/save` (solo tech lead); verificar con un ejercicio candidato real que pasa a `saved = true`, y que repetir la llamada o llamarla sobre uno eliminado responde con error sin cambiar el ejercicio
- [x] 2.3 Anadir a `exercises.py`: `GET /exercises` con filtros `type` y `q` (texto en `statement`); verificar que devuelve solo `saved = true` y `deleted_at` nulo, y que cada filtro reduce la lista como se espera
- [x] 2.4 Anadir a `exercises.py`: `PATCH /exercises/{id}` para marcar `deleted_at`; verificar que el ejercicio deja de aparecer en `GET /exercises` y que un intento posterior de anadirlo a un bloque nuevo falla por el trigger `block_exercise_requires_saved` ya existente
- [x] 2.5 Registrar el router en `backend/app/main.py` y verificar que `from app.main import app` sigue sin errores y que las tres rutas aparecen en `app.routes`

## 3. Bloques (exercise-blocks)

- [x] 3.1 `backend/app/schemas/block.py`: modelos para crear/editar/listar/ver un bloque (nombre + lista de `exercise_id` en orden)
- [x] 3.2 `backend/app/routers/blocks.py`: `POST /blocks` (solo tech lead); verificar que crea el bloque con sus `block_exercise` en el orden dado, y que falla sin crear nada si se piden 0, mas de 100, o algun ejercicio no definitivo
- [x] 3.3 Anadir `GET /blocks` (filtro `deleted` activo/eliminado) y `GET /blocks/{id}` (detalle con sus ejercicios en orden); verificar ambos listados con bloques de prueba activos y eliminados
- [x] 3.4 Anadir `PATCH /blocks/{id}` (reemplazo completo del nombre y/o la lista de ejercicios, segun `design.md` - Decisions); verificar que edita un bloque sin respuestas, y que un bloque con alguna `answer` responde con error (propagado desde el trigger de la tarea 1.1) sin cambiar nada
- [x] 3.5 Anadir `DELETE /blocks/{id}` (borrado logico); verificar que el bloque pasa a aparecer en `GET /blocks?deleted=true`, deja de poder asignarse (tarea 4.2) y sigue devolviendo su detalle y sus asignaciones existentes
- [x] 3.6 Registrar el router en `backend/app/main.py` y verificar que `from app.main import app` sigue sin errores

## 4. Asignaciones y progreso (block-assignment)

- [x] 4.1 `backend/app/schemas/block.py` (o un modulo propio): modelos para asignar y para el progreso por alumno
- [x] 4.2 `backend/app/routers/blocks.py`: `POST /blocks/{id}/assignments` (lista de `student_id`), con la lectura + insercion por lotes de `design.md` - Decisions; verificar que crea una asignacion y su copia de ejercicios por cada alumno nuevo, que omite (sin error) a quien ya estaba asignado, y que falla sin crear nada si el bloque esta eliminado o algun `student_id` no es un alumno valido
- [x] 4.3 Anadir `GET /blocks/{id}/assignments` (progreso por alumno: que ejercicios de su copia tienen `answer`); verificar con un alumno sin respuestas y, usando una `answer` insertada directamente para la prueba, con un alumno con alguna respuesta
- [x] 4.4 Verificar que editar o eliminar el bloque, o eliminar alguno de sus ejercicios, despues de asignarlo no cambia la copia ya devuelta por `GET /blocks/{id}/assignments` a un alumno ya asignado

## 5. Verificacion de extremo a extremo

- [x] 5.1 Ejecutar a mano, contra el backend real (`docker compose up` o `uvicorn` local) y el proyecto Supabase del change anterior, el flujo completo: generar un ejercicio, guardarlo (2.2), crear un bloque con el (3.2), asignarlo a un alumno de prueba (4.2), ver su progreso (4.3), editar el bloque antes de responder (3.4) y comprobar que falla tras insertar una `answer` de prueba (1.2/4.3), y eliminar el bloque (3.5) comprobando que la asignacion ya creada no cambia
- [x] 5.2 Revisar que las policies de RLS ya existentes (sin cambios en este change) siguen permitiendo lo esperado para un alumno autenticado de prueba: ve su propia asignacion y su copia de ejercicios, no ve bloques ni otras asignaciones

## Workflow follow-up

- Abrir una rama `change/bloques-asignaciones` (ya creada) y un PR hacia `develop` cuando los grupos 1-5 esten completos y verificados.
- Archivar el change (sincronizando `openspec/specs/exercise-catalog`, `openspec/specs/exercise-blocks`, `openspec/specs/block-assignment` como capacidades nuevas, y el delta de `data-authorization` en su spec existente) una vez el PR este aprobado.
