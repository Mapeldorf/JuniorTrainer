# Proposal

## Why

El backend (FastAPI, `backend/app`) filtra en algunos endpoints el texto crudo de excepciones internas (de Supabase o de los agentes de generacion/evaluacion) directamente en el `detail` de la respuesta HTTP. Un cliente -- incluyendo un alumno autenticado -- puede llegar a ver mensajes de error de librerias externas, lo que facilita reconocimiento de la infraestructura interna y es una mala practica de seguridad (OWASP: exposicion de informacion por manejo de errores).

## What Changes

- `POST /users` (`invite_student`, `backend/app/routers/users.py`): el `HTTPException(409)` deja de incluir `str(exc)` de la excepcion de Supabase; se registra la excepcion completa en el log del servidor y se devuelve un mensaje generico de conflicto.
- `POST /assignments/{assignment_id}/exercises/{exercise_id}/answer` (`backend/app/routers/assignments.py`): el `HTTPException(502)` cuando falla la evaluacion (`AnswerEvaluationFailed`) deja de incluir el texto de la excepcion del agente; se registra en el log y se devuelve un mensaje generico. La excepcion completa ya se guarda en `answer_evaluation.error_message` (tabla interna, no expuesta al alumno via API), asi que no se pierde trazabilidad.
- Se añade un logger de aplicacion (modulo estandar `logging`, sin dependencia nueva) usado en los puntos anteriores para no perder la causa raiz al dejar de exponerla en la respuesta HTTP.

## Capabilities

### New Capabilities
- `api-error-handling`: comportamiento transversal de que las respuestas de error HTTP del backend no exponen detalles internos (excepciones de librerias externas, stack traces), independientemente del endpoint.

### Modified Capabilities
(ninguna: no cambia el comportamiento funcional de `user-auth` ni `answer-evaluation`, solo el contenido de los mensajes de error en dos endpoints concretos)

## Impact

- `backend/app/routers/users.py`: mensaje de error de `invite_student`.
- `backend/app/routers/assignments.py`: mensaje de error de evaluacion de respuesta.
- Nuevo modulo de logging de aplicacion (o uso directo de `logging.getLogger(__name__)` en cada router, segun se decida en design.md).
- Fuera de alcance: `GET /generations/{id}` sigue exponiendo `generation.error_message` a quien tenga rol `tech_lead` -- es una decision de diseño ya existente (ver `specs/exercise-generation`) para que el tech lead pueda diagnosticar un fallo de generacion, restringida a un rol interno de confianza, no al publico general. No se toca en esta propuesta.
