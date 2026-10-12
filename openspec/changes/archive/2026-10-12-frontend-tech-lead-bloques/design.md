# Design

## Context

Backend ya expone `blocks.py` (crear/editar/eliminar/asignar bloques, con copia inmutable `assignment_exercise` al asignar) y `exercises.py` (catalogo `exercise-catalog`, ya con `SavedExerciseListItem` para el listado filtrable). Frontend ya tiene el patron de las pantallas de tech lead: un servicio HTTP por capacidad bajo `core/` con DTOs escritos a mano (`AssignmentsApiService`/`GenerationsApiService`, ver sus comentarios "Mismo patron... en un servicio aparte: capacidad distinta"), componentes standalone con signals bajo `tech-lead/<pantalla>/`, rutas protegidas por `techLeadGuard`, y una cabecera `tech-lead-nav` con las tres pestanas, dos de ellas todavia "Proximamente". Ver proposal.md - Why para la motivacion completa.

Los 4 gaps de backend (resumen de alumnos y flag de resuelto en `GET /blocks`, flag de eliminado y de resuelto en `GET /blocks/{id}`, conteo de bloques en `GET /exercises`, y tipo/enunciado/respuesta/justificacion por ejercicio en `GET /blocks/{id}/assignments`) se detectaron leyendo `backend/app/routers/blocks.py` y los esquemas reales, no asumiendo el disenio del canvas a ciegas.

## Goals / Non-Goals

**Goals:**
- Dar a las 4 pantallas (5, 6, 7, 7b) los datos que ya necesitan, ampliando los endpoints existentes sin romper a sus consumidores actuales (el alumno via `assignments.py` no toca `blocks.py`, asi que ampliar sus respuestas es seguro).
- Seguir el patron ya establecido: un servicio por capacidad, DTOs a mano, componentes standalone con signals.
- Reusar la logica de "resuelto" (`_block_has_answers`) que ya existe en el backend, solo exponiendola en vez de reimplementarla.

**Non-Goals:**
- No se toca el modelo de datos (tablas, columnas, triggers): todo lo que se expone ya existe en la base de datos.
- No se anade paginacion a ningun listado (bloques, alumnos asignados o ejercicios del catalogo): los volumenes esperados para esta cohorte son pequenios, igual que en las pantallas ya implementadas.
- No se construye un selector de alumnos con busqueda remota: la pantalla 7 ("Asignar a mas alumnos") y la pantalla 6 cargan sus listas completas de una vez, como ya hace `ejercicios`.

## Decisions

### D1. Resumen de alumnos en `BlockSummary` como lista embebida, no una llamada aparte
`GET /blocks` anade un campo `assigned_students: list[{id, name}]` (o vacio) a `BlockSummary`, calculado con una sola consulta adicional (`assignment.select("block_id, student_id, profile:student_id(name)")` filtrada por los ids de bloques devueltos) en vez de forzar a la pantalla 5 a pedir el detalle de cada bloque para pintar la columna. Alternativa descartada: que la pantalla 5 llame a `GET /blocks/{id}/assignments` por cada fila — N+1 llamadas innecesarias para un dato que ya se puede traer en la misma consulta del listado.

### D2. Flag "resuelto" expuesto en `BlockSummary` y `BlockDetail`, reusando `_block_has_answers`
`_block_has_answers(block_id)` ya existe y hoy solo se usa internamente para devolver 409 en `PATCH /blocks/{id}`. Se anade un campo `resolved: bool` a ambos esquemas, calculado con la misma funcion (sin duplicar la consulta: para el listado se adapta a comprobar todos los bloques de la pagina de una vez, no bloque a bloque). Alternativa descartada: inferir "resuelto" en el frontend comparando contadores de progreso — duplicaria una regla de negocio que ya vive en el backend y que puede cambiar (p. ej. si en el futuro "resuelto" pasara a requerir que TODOS los alumnos hayan completado, no solo uno).

### D3. Flag de ejercicio eliminado como campo nuevo junto a `SavedExercise`, nunca dentro de el
Siguiendo el precedente ya establecido por `SavedExerciseListItem` (que extiende `SavedExercise`/`ExerciseCandidate` sin tocarlo, por el comentario explicito en `exercise.py` de no romper la consulta de `BlockExerciseItem` que no une con `generation`), `BlockExerciseItem` pasa a incluir un campo propio `exercise_deleted: bool`, calculado comparando el `deleted_at` del ejercicio (una columna que ya existe en `exercise`, no en `SavedExercise`) en la misma consulta que ya hace el join `block_exercise.select("position, exercise:exercise_id(...)")|`, anadiendo `deleted_at` a esa proyeccion. `SavedExercise` sigue sin ese campo.

### D4. Conteo de uso en `SavedExerciseListItem`, no en `SavedExercise`
El selector de la pantalla 6 usa `GET /exercises` (que ya devuelve `SavedExerciseListItem`), asi que el conteo "en cuantos bloques esta" (`block_usage_count: int`) se anade ahi, con una consulta adicional que agrupa `block_exercise` por `exercise_id` sobre los ids de la pagina devuelta. No se toca `SavedExercise` por la misma razon que D3.

### D5. `ExerciseProgress`/`StudentProgress` se amplian leyendo la copia de la asignacion, nunca la composicion actual del bloque
Un bloque puede haberse editado entre dos asignaciones distintas, ambas antes de que existiera ninguna respuesta (las ediciones solo se bloquean cuando YA hay alguna respuesta en cualquier asignacion del bloque, globalmente). Por tanto el tipo y el enunciado de cada ejercicio de la pantalla 7, y la respuesta/veredicto/justificacion si esta respondido, se leen siempre desde `assignment_exercise` -> `exercise` y `answer` de esa asignacion concreta, nunca desde la composicion actual de `block_exercise`. Se amplian las consultas ya existentes en `get_block_progress` (que ya leen `assignment_exercise` y `answer`) para unir tambien `exercise.statement`/`exercise.type` y `answer.answer_text`/`answer.justification`, campos que ya existen en esas tablas (usados por `student-assignments` y `answer-evaluation`) y que esta vista solo necesita mostrar, no recalcular.

### D6. Un servicio nuevo `BlocksApiService` bajo `core/`, no una ampliacion de `GenerationsApiService`
Mismo patron que `AssignmentsApiService`/`GenerationsApiService`: un servicio por capacidad. `exercise-blocks` y `block-assignment` son capacidades distintas de `exercise-generation`/`exercise-catalog`, asi que se crea `core/blocks-api.model.ts` y `core/blocks-api.service.ts` nuevos. La unica llamada que toca `exercise-catalog` (el conteo de uso anadido a `GET /exercises`) sigue sirviendose desde `GenerationsApiService.listSaved`, solo ampliando su DTO existente `SavedExerciseListItem`.

### D7. Pantalla 6 unica para crear y editar
Un solo componente `tech-lead/bloque-editar/` recibe un `blockId` opcional por ruta (`/bloques/nuevo` y `/bloques/:blockId/editar`), precarga con `BlocksApiService.getDetail` cuando hay id, y decide "Crear bloque" vs "Guardar cambios" segun si hay id, igual que marca el canvas. Se reusa el mismo selector de ejercicios (checklist filtrable) para ambos casos.

### D8. Pantalla 7b como el mismo componente de detalle, no uno duplicado
`BlockDeleted.dc.html` es una variante de solo lectura de `BlockDetail.dc.html`/`BlockDetailResolved.dc.html`: mismo componente `tech-lead/bloque-detalle/`, que oculta "Editar"/"Eliminar"/"Asignar a mas alumnos" cuando `deleted_at` no es nulo (ya disponible en `BlockDetail`), en vez de una ruta y componente aparte.

## Risks / Trade-offs

- [Ampliar `GET /blocks` con una consulta extra de alumnos asignados en cada listado] -> Mitigacion: una sola consulta adicional filtrada por los ids ya devueltos (no N+1), igual de barata que la que ya calcula `exercise_count`.
- [Cambiar el significado de "resuelto" en el futuro (p. ej. a "todos los alumnos completaron") rompe cualquier cache en el frontend] -> Mitigacion: el frontend solo consume el booleano `resolved` tal cual lo da el backend, sin reglas propias; cualquier cambio de regla queda contenido en `_block_has_answers`.
- [Pantalla 7 con muchos alumnos asignados vuelve pesada la respuesta de `GET /blocks/{id}/assignments` al anadir enunciado/respuesta/justificacion por ejercicio] -> Mitigacion: aceptado como no-objetivo (ver Non-Goals): los volumenes de esta cohorte son pequenios y la pantalla ya pagina visualmente por alumno plegado/desplegado.

## Migration Plan

No hay migracion de datos (no se anaden columnas, todo lo expuesto ya existe). Despliegue en el orden habitual: backend primero (los campos nuevos son aditivos en las respuestas, no rompen a ningun consumidor existente, incluido el alumno via `assignments.py`), frontend despues. Sin bandera de features: se activa la pestana "Bloques de ejercicios" en el mismo cambio que el backend que la sirve. Rollback: revertir el commit del frontend no afecta al backend (los campos nuevos quedan sin usar); revertir el backend requiere revertir tambien el frontend, ya que las pantallas pasarian a fallar al leer campos ausentes.
