# Tasks

## 1. Alta de alumnos

- [x] 1.1 En `backend/app/routers/users.py`, añadir `logger = logging.getLogger(__name__)` y, en el `except Exception as exc` de `invite_student`, loguear la excepcion completa (`logger.exception(...)`) antes de levantar el `HTTPException`.
- [x] 1.2 Cambiar el `detail` del `HTTPException(409)` de `invite_student` a un mensaje generico que no incluya `{exc}` ni el email en texto libre de excepcion, y verificar manualmente (backend levantado localmente, curl/httpie) que una invitacion fallida (p. ej. Supabase dummy/no accesible) devuelve `409` con el mensaje generico y que el log del proceso muestra la excepcion completa. Verificado con un script manual (TestClient + dependency override de `require_tech_lead`, ya que este entorno no tiene un token Supabase real): `409 {'detail': 'No se ha podido invitar al alumno'}`, con `ERROR:app.routers.users:Fallo al invitar al alumno ...` y la traza completa en el log.

## 2. Evaluacion de respuestas

- [x] 2.1 En `backend/app/routers/assignments.py`, añadir `logger = logging.getLogger(__name__)` y, en el `except AnswerEvaluationFailed as exc` del endpoint de responder ejercicio, loguear la excepcion completa antes de levantar el `HTTPException`.
- [x] 2.2 Cambiar el `detail` del `HTTPException(502)` a un mensaje generico que no incluya `{exc}`, confirmando que `record_answer_evaluation(..., error_message=str(exc))` sigue guardando el detalle completo en `answer_evaluation` como hoy (no tocar esa llamada).
- [x] 2.3 Verificar manualmente (backend levantado localmente) que forzar un fallo de evaluacion (p. ej. agente evaluador no accesible) devuelve `502` con el mensaje generico al cliente, y que el log del proceso muestra la excepcion completa. Verificado con un script manual (TestClient + mocks de `get_admin_client`/`evaluate_answer`, dado que no hay agentes ni Supabase real en este entorno): `502 {'detail': 'No se ha podido evaluar la respuesta'}`, con `ERROR:app.routers.assignments:Fallo al evaluar la respuesta ...` y la traza completa en el log.

## 3. Verificacion final

- [x] 3.1 Revisar que el import check del CI (`python -c "from app.main import app"`) sigue pasando tras los cambios.
- [x] 3.2 Repasar el resto de routers (`blocks.py`, `exercises.py`, `generations.py`) para confirmar que ningun otro `HTTPException` interpola una excepcion cruda en `detail` (ya revisado en la propuesta: no hay mas casos salvo `GET /generations/{id}`, que queda fuera de alcance por diseño). Confirmado: los `detail=f"..."` restantes en `blocks.py` solo interpolan IDs que ya vienen en la peticion del cliente, no texto de excepciones.
