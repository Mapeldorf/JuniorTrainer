# Design

## Context

Lo que ya existe y condiciona este diseno (ver proposal.md - Why para la motivacion):

- `public.answer` ya tiene `verdict text not null check (verdict in ('correct','incomplete','incorrect'))` y `justification text` desde `0001_schema.sql`, mas `unique(assignment_id, exercise_id)`, FK compuesta a `assignment_exercise`, y el trigger `answer_immutable` (rechaza cualquier `UPDATE`). Es decir: la fila solo puede insertarse una vez, completa, con `verdict` ya resuelto.
- `public.assignment_exercise` no guarda una copia del contenido del ejercicio (enunciado/codigo/respuesta esperada); solo `(assignment_id, exercise_id, position)`. La "copia inmutable" (capacidad `block-assignment`) se sostiene en que `exercise_lock_after_saved` hace inmutable el contenido de un `exercise` guardado -- solo `deleted_at` puede cambiar despues -- asi que leer el contenido via `exercise_id` sigue siendo seguro aunque el ejercicio se elimine logicamente despues de asignar.
- No existe ningun endpoint de lectura para alumnos todavia (ni `require_student` en `app/deps.py`, ni ningun router que filtre por `student_id` de la sesion). Todo lo que hay bajo rol `student` en el backend es, hoy, inexistente: todos los endpoints actuales son `tech_lead`-only.
- El patron de orquestacion A2A sincrona ya existe en `app/a2a_client.py` (`send_a2a_task`, reusado tal cual) y en `app/orchestrator.py` (aunque ese corre en `BackgroundTasks`, a diferencia de este caso).
- `infra/litellm/config.yaml` y `.env.example` ya tienen los modelos logicos `evaluator`/`reviewer` como placeholder (comentario: "llegan en el paso 2 del plan de trabajo") -- no hace falta tocarlos.
- `agents/exercises` es la plantilla estructural a replicar para los dos agentes nuevos (Dockerfile, `app/{agent_card,config,executor,llm,models,service,tracing}.py`, `requirements.txt`, `run.py`, `scripts/verify_*.py`).

## Goals / Non-Goals

**Goals:**
- Que un alumno pueda, por API, ver sus asignaciones, verlas en detalle, responder un ejercicio, y que esa respuesta quede evaluada y persistida dentro de la misma peticion.
- Que el progreso que ya consulta el tech lead (`GET /blocks/{id}/assignments`) muestre el `verdict` real.
- Que un tech lead pueda listar alumnos para poder asignarles bloques.

**Non-Goals:**
- Reintento o edicion de una respuesta ya evaluada (la base de datos ya lo impide; no se anade ningun mecanismo para permitirlo).
- Cualquier pantalla de frontend.
- Mover la evaluacion a asincrono (p. ej. `BackgroundTasks` + polling). Se descarta explicitamente: `answer.verdict` es `NOT NULL`, asi que la fila no puede existir sin verdict; hacerlo asincrono exigiria o bien una tabla/estado intermedio (fuera de alcance: no se ha encontrado necesidad real todavia) o bloquear igual la respuesta HTTP hasta tener el resultado, que es lo que ya se hace aqui de forma sincrona.
- Cambiar el modelo de datos (`assignment_exercise` sigue sin copiar contenido; se sigue leyendo via `exercise_id`).

## Decisions

### Autorizacion de alumno: `require_student` + comprobacion de pertenencia por fila
Nueva dependencia `require_student` en `app/deps.py`, analoga a `require_tech_lead` (verifica `profile.role == "student"`). No basta con el rol: cada endpoint que opera sobre una asignacion concreta (detalle, responder) ademas comprueba que `assignment.student_id == profile.id` antes de hacer nada, devolviendo 404 (no 403) si la asignacion no es suya -- mismo criterio que ya usa `_get_block_or_404` en `blocks.py` para "no existe" vs "no autorizado": no se revela si una asignacion de otro alumno existe.

**Alternativa descartada**: delegar esto a RLS usando el JWT del alumno en vez del cliente admin. Se descarta por el mismo motivo que el resto del backend: `service_role` es exclusivo de FastAPI (decision ya establecida, ver `app/orchestrator.py`); las politicas RLS de `data-authorization` protegen el acceso directo a Supabase, no sustituyen la autorizacion en la API.

### Orquestacion de la evaluacion: sincrona, en un modulo nuevo `app/answer_orchestrator.py`
Analogo a `app/orchestrator.py` pero sin `BackgroundTasks`: el endpoint `await`-ea la orquestacion y responde con el resultado ya evaluado. Reusa `send_a2a_task` de `app/a2a_client.py` sin cambios.

Flujo: `evaluador(enunciado, codigo, respuesta_esperada, respuesta_alumno) -> {verdict, justification_draft}`, luego `revisor(enunciado, respuesta_alumno, verdict, justification_draft) -> {justification}` (el revisor solo puede ajustar la justificacion; el `verdict` que persiste es siempre el del evaluador, nunca el revisor -- decision explicita del proposal, evita que dos agentes compitan por la misma decision).

**Alternativa considerada**: un unico agente que evalua y revisa en la misma llamada. Se descarta porque el proposal (y el placeholder ya existente de `evaluator`/`reviewer` como dos modelos logicos distintos en `infra/litellm/config.yaml`) especifica dos agentes separados -- permite usar modelos distintos para cada rol (p. ej. un modelo mas barato para revisar que para evaluar).

### Si un agente falla: no se persiste nada, el alumno puede reintentar
Si `send_a2a_task` lanza `A2ATaskError`/`A2ATaskTimeout` en cualquiera de las dos llamadas, el endpoint responde 502 sin insertar ninguna fila en `answer`. A diferencia de `generation` (que tiene `status`/`error_message` para registrar un fallo persistente), `answer` no tiene esas columnas y no se anaden aqui (no se ha encontrado necesidad: al no haberse creado la fila, un segundo intento del alumno es indistinguible de un primer intento).

### "Ya respondido": comprobacion explicita antes de llamar a los agentes, mas captura en el insert
Antes de invocar a los agentes, el endpoint comprueba si ya existe una fila de `answer` para `(assignment_id, exercise_id)`: si existe, responde 409 sin gastar las dos llamadas A2A. Ademas, el `INSERT` final tambien captura el error de restriccion `unique` de la base de datos y lo traduce al mismo 409 -- cubre la carrera de dos peticiones simultaneas para el mismo ejercicio, donde ambas pasarian la comprobacion previa pero solo una puede insertar.

### Progreso con verdict: una sola consulta mas en `get_block_progress`
`backend/app/routers/blocks.py::get_block_progress` ya hace una consulta a `answer` para saber que pares `(assignment_id, exercise_id)` tienen respuesta (variable `answered`); pasa a traer tambien `verdict` en esa misma consulta (`select("assignment_id, exercise_id, verdict")`) y a poblar `ExerciseProgress.verdict` (nuevo campo opcional, `None` si no hay respuesta) en vez de reconstruir el booleano `answered` por separado. `answered` se deriva de `verdict is not None` en el schema, o se mantiene ambos campos por claridad para no romper a quien ya lea `answered` -- se mantiene `answered` tal cual (no es una capacidad que cambie) y se anade `verdict` como campo nuevo.

### Nuevos agentes: mismo scaffold que `agents/exercises`, puertos 8013/8014
`agents/evaluator` y `agents/reviewer` (nombres en ingles, igual que `web`/`code`/`exercises`), cada uno con la misma estructura de ficheros. URLs por defecto `http://agent-evaluator:8013/` y `http://agent-reviewer:8014/` (siguiente par de puertos libres tras 8010-8012), anunciadas en su propia Agent Card y repetidas en `backend/app/config.py` (`agent_evaluator_url`, `agent_reviewer_url`) exactamente igual que los tres agentes existentes. En `docker-compose.yml`, dos servicios nuevos `agent-evaluator`/`agent-reviewer` sin puerto publicado al host (`expose`, no `ports`), con `depends_on: litellm`, igual que `agent-exercises`.

### Contrato de entrada/salida de los agentes
- Evaluador: entrada `{statement, code, expected_answer, student_answer}`; salida `{verdict, justification}` (verdict uno de los tres valores de la constraint; justification el razonamiento).
- Revisor: entrada `{statement, student_answer, verdict, justification}` (la del evaluador); salida `{justification}` (la version revisada, que sustituye a la del evaluador).

Ambos siguen el mismo patron de `agents/exercises` (`app/input.py` parsea el mensaje A2A, `app/service.py` llama al modelo via `app/llm.py`, `app/executor.py` cablea entrada/salida, `app/tracing.py` registra el `trace_id` recibido).

### `GET /users`: anadido a `backend/app/routers/users.py`
Mismo router que ya tiene `POST /users`, `require_tech_lead`, devuelve `list[Profile]` filtrando `role = 'student'` directamente con el cliente admin (mismo patron que el resto del backend).

### Nombres de endpoints
- `GET /assignments`: alumno lista sus propias asignaciones.
- `GET /assignments/{assignment_id}`: alumno ve el detalle de una (ejercicios de su copia + si cada uno tiene respuesta).
- `POST /assignments/{assignment_id}/exercises/{exercise_id}/answer`: alumno responde.

Se eligen como recurso `assignments` propio en vez de anidar bajo `/blocks/{id}/...` (que ya es `tech_lead`-only en `blocks.py`): el alumno no necesariamente conoce ni deberia necesitar el `block_id` para operar sobre su propia asignacion.

## Risks / Trade-offs

- [Riesgo] Las dos llamadas A2A (evaluador + revisor) son sincronas dentro de la peticion HTTP: hasta 120s cada una (`DEFAULT_TASK_TIMEOUT_SECONDS` de `a2a_client.py`, sin cambios), es decir hasta ~240s de latencia percibida en el peor caso. -> Mitigacion: es una decision explicita (ver Non-Goals, "mover a asincrono"); se documenta aqui para que un futuro change que lo necesite lo sepa, en vez de descubrirlo por un timeout en produccion.
- [Riesgo] Condicion de carrera en doble envio simultaneo del mismo ejercicio. -> Mitigacion: ver Decisions, "Ya respondido" (comprobacion previa + captura del error de unicidad en el insert).
- [Riesgo] Dos agentes nuevos añaden superficie de fallo (dos servicios mas que pueden estar caidos o mal configurados). -> Mitigacion: mismo patron de timeouts y manejo de errores ya probado en `exercise-generation`; sin mitigacion nueva mas alla de reusar lo que ya funciona.

## Migration Plan

Sin migracion de base de datos (ver proposal.md - Impact). Despliegue: construir y levantar los dos servicios de agente nuevos (`docker-compose up -d --build agent-evaluator agent-reviewer`), relanzar el backend con la imagen nueva. Rollback: volver a la imagen anterior del backend y parar los dos servicios nuevos; no hay estado persistente que revertir porque no hay migracion.
