# Proposal

## Why

El perfil tech lead ya puede crear bloques de ejercicios y asignarlos, pero la pestaña "Alumnos" del nav sigue marcada "Próximamente": no hay forma, desde la aplicación, de dar de alta a un alumno ni de ver su progreso agregado a través de todos sus bloques asignados. El backend para dar de alta y listar alumnos (`POST /users`, `GET /users`) ya existe y está especificado; falta la pantalla que lo use, y falta por completo la vista de detalle de un alumno con su progreso.

## What Changes

- Activar la pestaña "Alumnos" del nav de tech lead (pantalla 5b): formulario para invitar un alumno por nombre y email, y tabla con los alumnos existentes y un enlace a su detalle. Usa los endpoints `POST /users` y `GET /users` ya implementados, sin cambios de backend.
- Nueva pantalla "Detalle de un alumno" (5c): cabecera con nombre/email del alumno y, para cada bloque que tiene asignado, un resumen expandible con su estado (sin empezar/en curso/completado), los contadores de veredictos, y el detalle ejercicio a ejercicio (enunciado, respuesta, veredicto, justificación) de esa asignación concreta.
- Nuevo endpoint de backend `GET /users/{student_id}/blocks`: dado un alumno, devuelve todas sus asignaciones con el mismo nivel de detalle por ejercicio que ya expone `GET /blocks/{id}/assignments`, pero organizado por alumno en vez de por bloque (simétrico al requisito ya existente de `block-assignment`).
- Nuevo cliente frontend para invitar alumnos (`UsersApiService.invite(...)`) y para el detalle de un alumno (`getBlocks(studentId)`), reutilizando `StudentSummary` ya existente.

## Capabilities

### New Capabilities

(ninguna: el alta/listado de alumnos ya vive en `user-auth` y la consulta de progreso por alumno se añade a `block-assignment`, ver abajo)

### Modified Capabilities

- `block-assignment`: nuevo requisito "Consultar las asignaciones de un alumno a través de sus bloques" — un tech lead puede consultar, para un alumno dado, todas sus asignaciones con el mismo detalle por ejercicio (tipo, enunciado, respuesta, verdict, justificación) que ya se expone por bloque.

## Impact

- Backend: nuevo endpoint `GET /users/{student_id}/blocks` en `backend/app/routers/users.py` (o `blocks.py`, a decidir en el diseño), reutilizando las mismas tablas y el mismo patrón de consulta batched que `get_block_progress` en `backend/app/routers/blocks.py`; nuevos esquemas Pydantic (reutilizando `ExerciseProgress` ya existente en `backend/app/schemas/block.py`).
- Frontend: nuevo cliente de invitación en `UsersApiService`; dos componentes nuevos (`tech-lead/alumnos` y `tech-lead/alumno-detalle`); activar el enlace "Alumnos" en `tech-lead-nav`; nuevas rutas guardadas por `authGuard` + `techLeadGuard`.
- Sin cambios en `data-authorization`: el nuevo endpoint es tech-lead-only (mismo patrón `require_tech_lead` + `get_admin_client()` que el resto de endpoints de bloques), sin reglas RLS nuevas.
