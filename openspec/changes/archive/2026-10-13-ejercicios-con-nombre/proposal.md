# Proposal

## Why

Hoy un ejercicio (candidato o definitivo) no tiene ningun campo que lo identifique de forma breve: en todos los listados, selectores y vistas de progreso de la aplicacion (tabla de "Ejercicios guardados", selector de ejercicios al componer un bloque, "Ejercicios del bloque" en el detalle de un bloque, progreso por alumno en el detalle de un bloque y en el detalle de un alumno) se usa el `enunciado` completo como identificador visual. Desde el change `ejercicios-nivel-junior` el enunciado es mas corto (hasta 50 palabras), pero sigue siendo una frase pensada para leerse como pregunta, no como etiqueta: en una tabla con columna de ancho fijo se trunca (`max-w-[360px] truncate`), y en una lista de checkboxes para componer un bloque obliga a leer la frase completa para distinguir un ejercicio de otro. Hace falta un campo corto y propio para eso -- un nombre -- que conviva con el enunciado sin sustituirlo (el enunciado sigue siendo el texto que resuelve el alumno).

## What Changes

- `public.exercise` gana una columna `name` (texto corto, obligatorio una vez guardado): el nombre del ejercicio, distinto del enunciado.
- El agente de ejercicios (`agents/exercises`) redacta tambien el nombre de cada candidato, dentro de la misma llamada al modelo que ya redacta enunciado/codigo/respuesta esperada; se limita a 8 palabras como maximo, garantizado en codigo con el mismo patron de reintento unico que ya usa el enunciado (ver change `ejercicios-nivel-junior`).
- El tech lead puede editar el nombre generado al revisar una generacion y guardar un candidato (`POST /exercises/{id}/save`), igual que ya puede editar la respuesta esperada; a partir de guardado, el nombre se vuelve inmutable junto con el resto del ejercicio.
- La busqueda de ejercicios definitivos (`GET /exercises?q=`) pasa a buscar por nombre o por enunciado, no solo por enunciado.
- El progreso de un bloque por alumno (`GET /blocks/{id}` y `GET /users/{id}/assignments`) informa tambien el nombre de cada ejercicio de la copia, junto al tipo y al enunciado que ya devuelve.
- **BREAKING** (interno, sin version publica de la API): el contrato A2A de salida del agente de ejercicios (`ExerciseCandidate`/`CandidateExercise`) anade el campo `name`, obligatorio. El orquestador del backend (`_insert_candidates`) empieza a exigirlo al insertar.
- Frontend del tech lead: las seis vistas que hoy usan `statement` como identificador visual (tabla de "Ejercicios guardados", selector de "Nuevo/editar bloque de ejercicios", "Ejercicios del bloque" en el detalle de bloque, progreso por ejercicio en el detalle de bloque, progreso por ejercicio en el detalle de alumno, y la tarjeta de cada candidato en "Revisar generacion") pasan a mostrar `name` como titulo/etiqueta; el enunciado completo se mantiene donde ya se mostraba integro (tarjeta de revision, bajo el nombre) o deja de mostrarse donde solo servia de identificador (tabla de guardados, selector, listas de progreso). La pantalla "Revisar generacion" anade un campo de texto editable para el nombre, igual que ya tiene uno para la respuesta esperada.
- Los ejercicios ya guardados antes de este change no tienen nombre: una migracion de base de datos les asigna uno derivado de su enunciado actual (las primeras palabras, acortadas con "…" si hace falta) antes de que la columna pase a ser obligatoria.
- Fuera de alcance: el enunciado (`statement`) sigue siendo el texto que ve y resuelve el alumno (pantalla "Ejercicio" y "Valoracion") -- no se toca esa vista ni el contrato de `student-assignments`, porque ahi el enunciado nunca se uso como identificador, sino como el contenido en si. Tampoco se anade busqueda de bloques por nombre de ejercicio (`GET /blocks` sigue sin ese filtro) ni se cambia el selector de pasos del alumno (ya usa el numero de posicion, no el enunciado).

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities
- `exercise-generation`: nuevo requisito -- el agente de ejercicios redacta tambien un nombre corto (hasta 8 palabras) para cada candidato, con la misma garantia de limite en codigo que ya tiene el enunciado.
- `exercise-catalog`: el requisito "Guardar un ejercicio candidato como definitivo" permite editar tambien el nombre al guardar (no solo la respuesta esperada); el requisito "Listar y buscar ejercicios definitivos" pasa a buscar por nombre o por enunciado.
- `data-authorization`: el requisito "Un ejercicio guardado es inmutable" anade el nombre a los campos protegidos.
- `block-assignment`: los dos requisitos de consulta de progreso ("Consultar el progreso de un bloque asignado" y "Consultar las asignaciones de un alumno a traves de sus bloques") anaden el nombre de cada ejercicio junto a su tipo y su enunciado.

## Impact

- `infra/supabase/migrations/`: nueva migracion `0006_exercise_name.sql` -- columna `name` en `public.exercise` (nullable al principio), backfill de los ejercicios existentes, columna `not null` despues, y ampliacion de la funcion `exercise_lock_after_saved()` para incluir `name` entre los campos inmutables.
- `agents/exercises/app/service.py`: `_SYSTEM_PROMPT` pide tambien `name`; nueva constante de limite de palabras del nombre y su propio reintento correctivo (mismo patron que `_MAX_STATEMENT_WORDS`).
- `agents/exercises/app/models.py`: `CandidateExercise` gana el campo `name`.
- `agents/exercises/scripts/`: el script de verificacion del limite de palabras se amplia para cubrir tambien el nombre (o se anade uno nuevo, a decidir en tasks.md).
- `backend/app/schemas/generation.py` (`ExerciseCandidate`) y `backend/app/schemas/exercise.py` (`SaveExerciseRequest`): nuevo campo `name`.
- `backend/app/schemas/block.py` (`ExerciseProgress` o equivalente): nuevo campo `name`.
- `backend/app/orchestrator.py` (`_insert_candidates`), `backend/app/routers/{exercises,generations,blocks,users}.py`: leen/escriben `name` junto a `statement`.
- `frontend/src/app/core/generations-api.model.ts`, `assignments-api.model.ts`, `blocks-api.model.ts`: nuevo campo `name` en las interfaces espejo.
- `frontend/src/app/tech-lead/{ejercicios,bloque-editar,bloque-detalle,alumno-detalle,revisar}/*.html`: sustituyen `statement` por `name` donde se usa como identificador; `revisar.html`/`.ts` anaden el campo editable de nombre.
- Sin cambios en `frontend/src/app/student/` ni en las specs `student-assignments`/`exercise-blocks` (este ultimo hereda el campo via el esquema compartido, sin requisito propio que tocar).
