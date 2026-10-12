# Design

## Context

El alta y el listado de alumnos (`POST /users`, `GET /users`) ya existen y estan especificados en `user-auth`; esta parte del change solo necesita pantalla, sin tocar backend. Lo que falta de verdad es la vista "Detalle de un alumno" (pantalla 5c): un progreso agregado por alumno, a traves de todos sus bloques, simetrico al progreso por bloque que ya expone `GET /blocks/{id}/assignments` (`get_block_progress` en `backend/app/routers/blocks.py`, capacidad `block-assignment`). Ese endpoint ya hace el trabajo pesado -- join batched de `assignment_exercise`+`exercise` y de `answer`, por una lista de `assignment_id` -- y solo cambia el filtro de entrada (por `block_id` en vez de por `student_id`) y un dato mas por fila (el nombre del bloque, en vez del nombre del alumno).

## Goals / Non-Goals

**Goals:**
- Activar la pantalla "Alumnos" (5b) reusando `POST /users` y `GET /users` tal cual existen hoy.
- Anadir el endpoint y la pantalla de detalle de alumno (5c) con el mismo nivel de detalle por ejercicio que ya tiene la pantalla 7 (detalle de bloque), pero organizado por alumno.
- Reusar al maximo el patron de consulta ya probado de `get_block_progress`, no reinventar la forma de leer `assignment_exercise`/`answer`.

**Non-Goals:**
- No se cambia nada de `data-authorization` ni de las politicas RLS: el nuevo endpoint es tech-lead-only con el mismo patron `require_tech_lead` + `get_admin_client()` que el resto de endpoints de bloques, sin tocar la tabla `profile` ni los permisos de alumno.
- No se anade edicion ni baja de alumnos (solo alta por invitacion, ya existente, y listado/detalle de solo lectura) -- no esta en las pantallas 5b/5c del diseno.
- No se anade un endpoint dedicado para un solo alumno (`GET /users/{id}`): la cabecera de la pantalla 5c (nombre/email) se resuelve reusando `GET /users` ya cargado por la pantalla 5b, sin una llamada nueva.

## Decisions

**D1. Endpoint nuevo en `users.py`, no en `blocks.py`.** `GET /users/{student_id}/blocks` queda junto a `POST /users`/`GET /users` porque esta indexado por alumno, no por bloque; sigue el mismo patron (`require_tech_lead`, `get_admin_client()`). Alternativa descartada: ponerlo en `blocks.py` junto a `get_block_progress` -- se descarta porque el recurso de la URL es un alumno, no un bloque, y agruparlo con el resto de `/users` es mas consistente con como ya esta organizado el router.

**D2. Query: mismo patron que `get_block_progress`, filtrado por `student_id` en vez de `block_id`, con el nombre del bloque anadido via un join extra.** Primero `assignment.select("id, block_id, block:block_id(name)").eq("student_id", student_id)`; si no hay filas, devolver `[]`. Con los `assignment_id` resultantes, las mismas dos consultas batched a `assignment_exercise`+`exercise` y a `answer` que ya usa `get_block_progress`, reusando literalmente la misma forma de construir `ExerciseProgress` (incluyendo el mapeo `text` -> `answer_text`). Alternativa descartada: una vista SQL o funcion RPC dedicada -- no hace falta, el volumen por alumno es pequeno y el patron ya esta resuelto en Python.

**D3. Se incluyen las asignaciones de bloques ya eliminados.** El requisito ya existente "Eliminar un bloque sin afectar a quien lo tiene asignado" (`exercise-blocks`) exige que un alumno ya asignado siga viendo su copia igual; por simetria, el detalle de ese alumno para el tech lead tambien debe seguir mostrando esa asignacion tal cual, aunque el bloque de origen este en "Bloques eliminados". No se filtra por `block.deleted_at`.

**D4. 404 si el id no corresponde a un alumno existente.** Nuevo helper `_get_student_or_404(student_id)` (mismo patron que `_get_block_or_404`): consulta `profile` por id y `role = student`; si no existe o es un tech lead, 404. Alternativa descartada: devolver `[]` en silencio -- se descarta porque esconde errores de navegacion (id de bloque pegado donde iba un id de alumno, etc.) que un 404 deja ver de inmediato.

**D5. Esquema nuevo `StudentBlockAssignment` en `backend/app/schemas/block.py`, no en `schemas/profile.py`.** Campos: `assignment_id`, `block_id`, `block_name`, `exercises: list[ExerciseProgress]` -- reusa `ExerciseProgress` ya existente ahi mismo. Se importa en `users.py` igual que ya se importan `Profile`/`StudentSummary` desde `schemas/profile.py`; no hay import circular (`block.py` no importa de `profile.py`).

**D6. Orden de los bloques: por fecha de asignacion (`assigned_at` ascendente).** Es el orden mas natural para que el tech lead vea primero lo que el alumno lleva mas tiempo trabajando; no hay en el diseno visual un criterio de orden distinto especificado.

**D7. Frontend: `UsersApiService` gana dos metodos.** `invite(name, email)` (`POST /users`, propaga el 409 tal cual para que el componente lo distinga de otros errores) y `getBlocks(studentId)` (`GET /users/{id}/blocks`). Mismo servicio que ya tiene `listStudents()`, sin crear un servicio nuevo.

**D8. Dos componentes standalone nuevos: `tech-lead/alumnos` (5b) y `tech-lead/alumno-detalle` (5c).** La pantalla 5c resuelve nombre/email del alumno buscandolo en el resultado de `UsersApiService.listStudents()` (D no-goal anterior) y carga el progreso con `getBlocks(studentId)`; el renderizado de cada ejercicio (tipo, enunciado, respuesta, verdict, justificacion o "Sin responder") reusa el mismo patron visual que ya tiene `BloqueDetalleComponent`, pero no el componente en si -- son vistas distintas (una por bloque con todos sus alumnos, otra por alumno con todos sus bloques).

**D9. Rutas nuevas: `/alumnos` y `/alumnos/:studentId`.** Guardadas por `authGuard` + `techLeadGuard`, mismo patron que `/bloques` y `/bloques/:blockId`. "Ver detalle" en la tabla de la pantalla 5b enlaza a `/alumnos/:studentId`.

## Risks / Trade-offs

- [Reusar `listStudents()` para la cabecera de la pantalla 5c implica una llamada de red adicional (la lista completa de alumnos) solo para leer nombre/email de uno] → Mitigacion: el volumen de alumnos es pequeno (uso interno de una empresa formando a sus propios junior), y evita mantener un segundo endpoint `GET /users/{id}` solo para esto.
- [El 409 de `POST /users` ya existe pero el frontend nunca lo ha consumido hasta ahora] → Mitigacion: `UsersApiService.invite` deja que el error HTTP se propague sin envolverlo, y el componente de la pantalla 5b distingue 409 (banner de email duplicado, igual que el mockup `StudentsDuplicate.dc.html`) de cualquier otro error (banner generico).
- [Incluir bloques eliminados en el detalle del alumno (D3) podria confundir si no se marca visualmente] → Mitigacion: cada entrada expandible muestra el nombre del bloque tal cual viene en `StudentBlockAssignment.block_name`; si hace falta distinguir un bloque eliminado en esta vista no lo pide el diseno visual (`StudentDetail.dc.html` no lo marca), asi que se deja igual que los demas y se revisita si el usuario lo pide despues de ver la pantalla en uso.

## Migration Plan

- Sin migracion de base de datos: el nuevo endpoint solo lee tablas ya existentes (`assignment`, `assignment_exercise`, `exercise`, `answer`, `block`, `profile`), sin columnas nuevas.
- Despliegue como el resto de changes de este proyecto: rama `change/frontend-tech-lead-alumnos` desde `develop`, PR, merge, y archivado con sincronizacion de specs una vez verificado.
