# Design

## Context

Ver `proposal.md` para la motivacion. Estado tecnico relevante:

- `infra/litellm/provision_keys.py` (propuesta `litellm-agent-keys`) crea las 5 virtual keys via `POST /key/generate`, y comprueba si ya existen via `GET /key/list?key_alias=<alias>` antes de crear (idempotente por alias, sin tocar nada si ya existe).
- Verificado contra el proxy real de este entorno: al superar `max_budget`, LiteLLM responde `HTTP 422` con `{"error": {"type": "budget_exceeded", ...}}` -- distinto del `HTTP 403 key_model_access_denied` que ya usa la restriccion de modelo, y del `HTTP 401` de una key invalida/revocada.
- Verificado tambien: ningun agente (`agents/*/app/service.py`, `executor.py`) envuelve la llamada al modelo (`model.ainvoke(...)`) en un `try/except` propio; la excepcion que levanta `langchain-openai` ante una respuesta de error HTTP del proxy sube sin capturar hasta el framework A2A (`a2a.server.agent_execution`), que es quien convierte una excepcion no capturada en `execute()` en una respuesta de tarea fallida (no un colgado). Como red de seguridad adicional, `backend/app/a2a_client.py` ya tiene un timeout explicito de 120s por tarea A2A (propuesta `agent-resilience`), independiente de como el agente gestione el error.

## Goals / Non-Goals

**Goals:**
- Las 5 keys con techo de gasto real desde su creacion, sin paso manual adicional.
- Que las 5 keys que ya existen en el entorno de desarrollo del usuario (sin budget, creadas con la version anterior del script) queden protegidas sin tener que revocarlas y regenerarlas a mano.
- Que superar el presupuesto falle de forma visible (tarea A2A fallida), nunca como un colgado silencioso.

**Non-Goals:**
- No se añade manejo de errores especifico para `budget_exceeded` en los agentes: el mismo camino que ya gestiona cualquier otro fallo del proveedor (timeout, rate limit, modelo no disponible) es suficiente -- añadir una rama especial solo para este caso seria tratar distinto algo que, desde la perspectiva del agente, es "el proxy rechazo la llamada", igual que las otras causas.
- No se implementa dashboard de consumo ni alertas proactivas (email/Slack) cuando una key se acerca a su limite. Si hiciera falta, es una propuesta aparte con su propio alcance (que canal, que umbral, quien la recibe).
- No se decide aqui si $5/mes por key es el importe correcto a largo plazo: es la cifra acordada para esta propuesta; ajustarla mas adelante es cambiar un parametro (`max_budget` en el script), no requiere una propuesta nueva.

## Decisions

- **El script pasa a ser "upsert" (crear si falta, actualizar budget si existe sin el), no solo "crear o ignorar".** Alternativa descartada: dejar las 5 keys existentes del entorno de desarrollo sin budget y exigir revocarlas/regenerarlas a mano para que esta propuesta surta efecto. Se descarta porque obligaria a un paso manual fuera del propio script justo para el caso que motiva la propuesta (entornos ya provisionados), y porque dejaria el script con dos comportamientos distintos segun el entorno (nuevo vs ya provisionado) sin que el propio script lo resuelva.
- **El upsert solo toca `max_budget`/`budget_duration` cuando faltan, nunca si ya hay un budget puesto.** Si en algun momento alguien ajusta el budget de una key a mano (via `/key/update` o la logica de negocio que decida, p. ej. subirlo temporalmente), una re-ejecucion del script no debe pisarlo de vuelta a 5 sin querer. El script solo actua sobre el estado "sin budget", nunca sobre "con budget distinto al de esta propuesta".
- **No se añade logica nueva de manejo de errores en los agentes.** Justificado por la investigacion de Context: el framework A2A ya convierte cualquier excepcion no capturada de `execute()` en una tarea fallida, y el timeout de 120s de `a2a_client.py` es un backstop independiente. Añadir un `try/except EvaluationError`-like especifico para `budget_exceeded` seria logica nueva sin beneficio observable: el usuario final ya ve un error en ambos casos (timeout vs presupuesto superado), y distinguir el motivo exacto en la UI no esta pedido por esta propuesta.
- **Importe y periodo fijos en el script, no en variables de entorno.** `max_budget=5`/`budget_duration="30d"` como constantes en `provision_keys.py`, igual que las restricciones de modelo por agente ya son constantes (`_AGENT_MODELS`). Si se necesitara variar el importe por entorno (desarrollo vs produccion) en el futuro, se revisaria esta decision; hoy el proyecto no tiene ese tipo de diferenciacion por entorno en ningun otro sitio.

## Risks / Trade-offs

- [Un agente puede quedar bloqueado a mitad de uso normal (no por bug) si $5/mes resulta insuficiente para el volumen real de pruebas del TFM] → Mitigacion: el error es visible (tarea A2A fallida, no un colgado silencioso) y el ajuste es trivial -- subir `max_budget` a mano via `/key/update` o cambiar la constante en el script y reaprovisionar. No hay perdida de datos, solo una generacion/evaluacion que hay que reintentar.
- [El upsert añade una llamada API mas (`/key/update`) en el camino del script para keys existentes sin budget, aunque solo ocurre una vez por key hasta que tenga budget] → Mitigacion: coste despreciable, mismo patron que la idempotencia por alias que ya tiene el script.
- [`budget_duration=30d` se cuenta desde la creacion/ultima actualizacion de la key, no desde una fecha de calendario fija (p. ej. dia 1 de cada mes); las 5 keys no se resetean todas el mismo dia si se aprovisionaron en momentos distintos] → Mitigacion: irrelevante para este proyecto (no hay facturacion mensual real que reconciliar contra el reseteo); si llegara a importar, es un ajuste de `budget_duration`/`budget_reset_at` en una propuesta futura, no bloquea esta.
