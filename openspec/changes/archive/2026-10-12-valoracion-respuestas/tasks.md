# Tasks

## 1. Autorizacion de alumno

- [x] 1.1 Anadir `require_student` a `backend/app/deps.py` (analoga a `require_tech_lead`: exige `profile.role == "student"`, 403 si no) y verificar con una llamada directa a la funcion con un `Profile` de cada rol (acepta student, rechaza tech_lead).

## 2. Consultar las propias asignaciones (capacidad `student-assignments`)

- [x] 2.1 Crear `backend/app/schemas/assignment.py` con los schemas de asignacion propia (resumen para listar, detalle con ejercicios y si cada uno tiene respuesta) y verificar que importan sin error.
- [x] 2.2 Crear `backend/app/routers/assignments.py` con `GET /assignments` (requisito "Listar las propias asignaciones"): devuelve solo las asignaciones del alumno autenticado. Verificar en vivo contra Supabase: un alumno con asignaciones ve solo las suyas; un alumno sin ninguna ve una lista vacia.
- [x] 2.3 Anadir `GET /assignments/{assignment_id}` (requisito "Ver el detalle de una asignacion propia"): devuelve los ejercicios de la copia en orden (`position`) con el contenido leido via `exercise_id` (enunciado/codigo), y si cada uno ya tiene respuesta. Verificar en vivo: el propio alumno ve el detalle completo; un alumno que prueba el `assignment_id` de otro recibe 404 y ningun dato.
- [x] 2.4 Registrar `assignments.router` en `backend/app/main.py` y verificar que la app importa sin error (`python -c "from app.main import app"`).

## 3. Agente evaluador

- [x] 3.1 Crear `agents/evaluator/` con el mismo scaffold que `agents/exercises` (Dockerfile, `app/{__init__,config,agent_card,llm,models,input,service,executor,tracing}.py`, `run.py`, `requirements.txt`), Agent Card describiendo la skill "evaluar una respuesta" y `agent_evaluator_host/port/url` (puerto 8013) en `app/config.py`. Verificar que el servicio arranca localmente (`uvicorn app.main:app` o equivalente) y responde a una Agent Card valida.
- [x] 3.2 Implementar `app/service.py` (contrato de `design.md`: entrada `statement, code, expected_answer, student_answer` -> salida `verdict, justification`, usando el modelo logico `evaluator` via `app/llm.py`) y `app/input.py`/`app/executor.py` para cablear la entrada/salida A2A. Verificar con una llamada directa al agente (sin backend) para una respuesta claramente correcta y otra claramente incorrecta, comprobando que el `verdict` devuelto coincide con lo esperado en cada caso.
- [x] 3.3 Anadir `trace_id` (resuelto/generado igual que en `agents/exercises/app/tracing.py`) y un script `scripts/verify_trace_id.py` analogo a los de los otros agentes. Verificar que el `trace_id` recibido en los metadatos del mensaje aparece en la traza registrada.

## 4. Agente revisor

- [x] 4.1 Crear `agents/reviewer/` con el mismo scaffold, Agent Card de la skill "revisar una justificacion", `agent_reviewer_host/port/url` (puerto 8014). Verificar que el servicio arranca y responde a una Agent Card valida.
- [x] 4.2 Implementar `app/service.py` (entrada `statement, student_answer, verdict, justification` -> salida `justification` revisada, modelo logico `reviewer`) y el cableado A2A correspondiente. Verificar con una llamada directa al agente que la justificacion de salida es nunca vacia y que el `verdict` de entrada no aparece en absoluto en el contrato de salida (el revisor no puede cambiarlo porque ni se le devuelve).
- [x] 4.3 Anadir `trace_id` y su script de verificacion, igual que en el evaluador.

## 5. Orquestacion y envio de respuesta (capacidad `answer-evaluation`)

- [x] 5.1 Anadir `agent_evaluator_url`/`agent_reviewer_url` a `backend/app/config.py` (mismos defaults `http://agent-evaluator:8013/` / `http://agent-reviewer:8014/`) y verificar que `Settings()` carga sin error con el `.env` del proyecto.
- [x] 5.2 Crear `backend/app/answer_orchestrator.py` con la orquestacion sincrona evaluador -> revisor (requisito "El resultado de la evaluacion incluye un verdict y una justificacion revisada"), reusando `send_a2a_task`. Verificar llamando a la funcion directamente contra los dos agentes reales (arrancados en local) con una respuesta correcta y otra incorrecta/incompleta, comprobando el `verdict` y que la `justification` final es la revisada, no la del evaluador.
- [x] 5.3 Anadir el manejo de fallo de cualquiera de los dos agentes (requisito "La evaluacion no puede completarse"): propagar un error claro sin persistir nada. Verificar apagando uno de los dos agentes y comprobando que la llamada falla sin crear ninguna fila en `answer`.
- [x] 5.4 Anadir `POST /assignments/{assignment_id}/exercises/{exercise_id}/answer` en `assignments.py` (requisitos "Enviar una respuesta a un ejercicio de la propia asignacion" y "La evaluacion usa la copia de la asignacion, nunca el ejercicio original"): valida pertenencia de la asignacion y que el ejercicio esta en su copia, llama a la orquestacion, inserta `answer` con el cliente admin. Verificar en vivo: una respuesta valida a un ejercicio de la propia asignacion queda persistida con verdict+justification; un intento sobre un `exercise_id` fuera de la copia o sobre la asignacion de otro alumno se rechaza sin crear nada; si el `exercise` original ya tiene `deleted_at`, la evaluacion igualmente usa el enunciado/respuesta esperada de la copia.
- [x] 5.5 Anadir el rechazo de doble respuesta (requisito "Un ejercicio de una asignacion solo se responde una vez"): comprobacion previa + captura del error de unicidad del insert, traducidos a 409. Verificar en vivo: responder dos veces el mismo ejercicio devuelve 409 la segunda vez y la respuesta original no cambia.
- [x] 5.6 Registrar el `trace_id` de la evaluacion en Langfuse (nueva funcion en `backend/app/tracing.py`, analoga a `record_generation`). Verificar que aparece una traza por respuesta evaluada.

## 6. Progreso con verdict (capacidad `block-assignment`, modificada)

- [x] 6.1 Anadir el campo `verdict` a `ExerciseProgress` (`backend/app/schemas/block.py`) y ampliar la consulta de `get_block_progress` en `backend/app/routers/blocks.py` para traer `verdict` de `answer` (requisito "Consultar el progreso de un bloque asignado", version modificada). Verificar en vivo: el progreso de un bloque con respuestas ya evaluadas muestra el `verdict` de cada una; los ejercicios sin respuesta siguen sin `verdict`.

## 7. Listar alumnos (capacidad `user-auth`, modificada)

- [x] 7.1 Anadir `GET /users` a `backend/app/routers/users.py` (requisito "Listar alumnos"): `require_tech_lead`, devuelve `id, name, email` de los perfiles con `role = 'student'`. Verificar en vivo: un tech lead recibe la lista completa de alumnos; un alumno que lo intenta recibe 403 y ningun dato.

## 8. Cableado de infraestructura

- [x] 8.1 Anadir los servicios `agent-evaluator`/`agent-reviewer` a `docker-compose.yml` (mismo patron que `agent-exercises`: `expose`, sin `ports`, `depends_on: litellm`) y verificar que `docker compose config` valida el fichero sin errores.
- [x] 8.2 Revisar que `.env.example` ya cubre `EVALUATOR_MODEL`/`EVALUATOR_API_KEY`/`REVIEWER_MODEL`/`REVIEWER_API_KEY` (ya existen como placeholder) y anadir cualquier variable nueva que falte (p. ej. credenciales de Postgres de los agentes nuevos, si acaban necesitandolas). Verificar listando las variables que cada agente nuevo requiere en su `Settings` y confirmando que todas tienen entrada en `.env.example`.

## 9. Verificacion end-to-end

- [x] 9.1 Escribir `backend/scripts/verify_valoracion_respuestas.py` (mismo patron que `verify_bloques_asignaciones.py`: llamadas directas a los endpoints, datos de prueba con un tag disponible, limpieza en `finally`) cubriendo el flujo completo: listar asignaciones, ver detalle, responder correctamente, responder incorrectamente, intentar responder dos veces, intentar responder fuera de la propia asignacion, progreso con verdict visible para el tech lead, y `GET /users`. Verificar que el script completo pasa contra el entorno real (Supabase + agentes levantados).

## Workflow follow-up

- Archivar el change una vez el usuario lo revise y confirme.
- Verificar el resultado archivado (`openspec validate --specs`).
