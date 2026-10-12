# Proposal

## Why

Un alumno puede ver los bloques que tiene asignados (change `bloques-asignaciones`), pero todavia no existe forma de responder a ninguno de sus ejercicios, ni de que esa respuesta se evalue. Sin esto, el flujo central de la plataforma (el alumno responde, un agente la evalua, el tech lead ve el resultado en el progreso del bloque) no existe. El esquema de base de datos ya reserva columnas de verdict/justification en `answer` desde el change `esqueleto-monorepo-auth`, asi que la base para esto ya esta puesta; falta exponerla. Ademas, no existe hoy ningun endpoint de lectura para alumnos (ni para listar sus propias asignaciones ni para ver el detalle de una): sin eso, un alumno no tiene forma de llegar a un `assignment_id`/`exercise_id` que responder. Tambien falta `GET /users` (listar alumnos) para que un tech lead pueda elegir a quien asignar un bloque; `backend/app/main.py` ya anota ambos huecos como pendientes de este change.

## What Changes

- Nuevos endpoints para que un alumno liste sus propias asignaciones y consulte el detalle de una (los ejercicios de su copia y si cada uno ya tiene respuesta registrada).
- Nuevo endpoint para que un alumno envie su respuesta a un ejercicio de una de esas asignaciones.
- Dentro de la misma peticion HTTP de responder (sin `BackgroundTasks`, a diferencia de la generacion: `answer.verdict` es `NOT NULL`, asi que no puede insertarse la fila sin saberlo ya), se orquestan dos agentes A2A nuevos:
  - Agente evaluador: decide el `verdict` (`correct` / `incomplete` / `incorrect`) comparando la respuesta del alumno contra el ejercicio de su propia copia de asignacion (nunca contra el `exercise` original, que puede haber cambiado de `deleted_at` o ya no estar en ningun bloque activo).
  - Agente revisor: revisa la justificacion que propone el evaluador antes de persistirla (puede confirmarla o corregirla; no cambia el `verdict`).
- La fila de `answer` se inserta ya con `verdict` + `justification` resultantes, con el cliente admin del backend (mismo patron que `app/orchestrator.py` ya usa para `exercise`).
- Un alumno solo puede responder una vez por ejercicio de su asignacion. La base de datos ya lo impide (`answer` tiene `unique(assignment_id, exercise_id)` y el trigger `answer_immutable`); el endpoint debe traducir ese rechazo en un error HTTP claro (409) en vez de dejar pasar el error crudo de Postgres.
- **BREAKING**: `ExerciseProgress` (usado por `GET /blocks/{block_id}/assignments`) deja de limitarse a `answered: bool`; pasa a incluir el `verdict` de cada ejercicio ya respondido. El campo de valoracion que ese endpoint dejo preparado en el change anterior se completa aqui.
- Nuevo endpoint `GET /users` para que un tech lead liste los alumnos existentes (id, nombre, email), completando el "resto de /users" ya anotado como pendiente de este change en `backend/app/main.py`.

## Capabilities

### New Capabilities
- `student-assignments`: el alumno lista sus propias asignaciones y consulta el detalle de una (ejercicios de su copia y si cada uno ya tiene respuesta), como base para poder responderlos.
- `answer-evaluation`: el alumno envia una respuesta a un ejercicio de su asignacion, dos agentes A2A (evaluador y revisor) la evaluan de forma sincrona dentro de la misma peticion, y el resultado (verdict + justification) se persiste junto con la respuesta.

### Modified Capabilities
- `block-assignment`: el requisito "Consultar el progreso de un bloque asignado" cambia para informar, por ejercicio respondido, el `verdict` obtenido — ya no se queda en "sin ningun dato de valoracion".
- `user-auth`: se anade el requisito de que un tech lead pueda listar los alumnos existentes.

## Impact

- `backend/app/routers/`: nuevo router de asignaciones del alumno (listar + detalle + responder); `users.py` gana `GET /users`.
- `backend/app/deps.py`: nueva dependencia `require_student` (analoga a `require_tech_lead`).
- `backend/app/schemas/`: nuevos schemas para asignacion/detalle/respuesta del alumno; `ExerciseProgress` (en `block.py`) gana el campo `verdict`.
- `backend/app/orchestrator.py` o un modulo nuevo equivalente: orquestacion sincrona evaluador + revisor, reusando `app/a2a_client.py` tal cual (mismo `send_a2a_task`).
- `backend/app/config.py`: nuevas URLs de agente (`agent_evaluator_url`, `agent_reviewer_url`).
- `agents/`: dos nuevos servicios A2A (evaluador, revisor), siguiendo la misma estructura que `agents/exercises` (Dockerfile, `app/agent_card.py`, `app/executor.py`, `app/service.py`, `app/tracing.py`, etc.). Los modelos logicos `evaluator`/`reviewer` ya estan predefinidos como placeholder en `infra/litellm/config.yaml` y `.env.example` (comentario explicito: "llegan en el paso 2 del plan de trabajo"), asi que no hace falta tocar ninguno de los dos ficheros.
- `docker-compose.yml`: dos nuevos servicios para los agentes.
- `infra/supabase/migrations/`: de momento no se ha encontrado necesidad de una migracion nueva — `answer.verdict`/`answer.justification` ya existen desde `0001_schema.sql`, y las reglas de inmutabilidad/FK relevantes ya estan cubiertas por `data-authorization` ("La copia de una asignacion es inmutable", "Una respuesta no se modifica"). Se confirmara en `design.md` si investigar mas a fondo revela lo contrario.
