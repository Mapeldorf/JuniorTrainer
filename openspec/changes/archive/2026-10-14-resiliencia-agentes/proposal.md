# Proposal

## Why

Dos vacios de resiliencia/disponibilidad, encontrados auditando los 5 agentes LLM:

1. **Ningun cliente LLM ni el cliente Tavily tiene timeout explicito.** `ChatOpenAI` (construido en `app/llm.py` de los 5 agentes) y `AsyncTavilyClient` (`agents/web/app/service.py`) se crean sin `timeout=`. El propio proyecto ya documenta por que esto es un problema real: `backend/app/a2a_client.py` tiene una nota explicita de que el timeout por defecto de `httpx` (5s) causo un bug en produccion porque era mucho menor que una tarea real, y `agents/code/app/github_app.py`/`agents/code/app/tools/github_repo.py` ya fijan 10-20s de timeout en sus llamadas HTTP por ese mismo motivo. Sin un timeout equivalente en el cliente del LLM o de Tavily, una llamada que se quede colgada bloquea la tarea hasta que el limite superior de 2 minutos por tarea A2A del backend (`DEFAULT_TASK_TIMEOUT_SECONDS`, `backend/app/a2a_client.py`) la corte desde fuera -- sin que el agente sepa nunca que fue una llamada al LLM/Tavily la que colgo, y sin liberar antes el recurso bloqueado dentro del proceso del agente.
2. **Ningun agente limita cuantas tareas A2A procesa por unidad de tiempo.** El backend ya tiene rate limiting en sus rutas HTTP publicas (`backend/app/rate_limit.py`, propuesta `rate-limiting-backend`), pero los 5 agentes -- que ahora exigen la credencial de servicio del change `autenticacion-backend-agentes`, pero siguen siendo procesos HTTP con sus propios recursos limitados (LLM, Tavily, GitHub, Postgres) -- no tienen ningun limite propio. Si la autenticacion de servicio fallara, o si el backend tuviera un bug que generara un bucle de reintentos, nada en el agente mismo frena el gasto resultante.

## What Changes

- Los 5 agentes anaden `timeout=` explicito a su cliente `ChatOpenAI` (valor concreto en design.md).
- `agents/web` anade `timeout=` explicito a `AsyncTavilyClient`.
- Los 5 agentes anaden un limite de peticiones por IP a sus rutas HTTP (mismo patron que ya usa el backend: `slowapi`), como ultima linea de defensa independiente de la credencial de servicio.
- No se toca el backend ni su propio rate limiting (propuesta `rate-limiting-backend`, en curso, fuera de alcance de este cambio).

## Capabilities

### New Capabilities
- `agent-resilience`: define los limites de tiempo y de tasa que protegen a cada agente frente a dependencias externas colgadas y frente a un volumen de peticiones A2A por encima del uso legitimo esperado.

### Modified Capabilities
(ninguna: `agent-auth` cubre especificamente la verificacion de identidad de la peticion A2A, no los limites de tiempo/tasa -- son propiedades distintas, con su propia capacidad nueva en vez de ampliar el alcance de `agent-auth`)

## Impact

- **Codigo afectado**: `agents/{code,evaluator,exercises,reviewer,web}/app/llm.py` (timeout en `ChatOpenAI`), `agents/web/app/service.py` (timeout en `AsyncTavilyClient`), `agents/{code,evaluator,exercises,reviewer,web}/app/main.py` (middleware de rate limiting), `agents/{code,evaluator,exercises,reviewer,web}/requirements.txt` (nueva dependencia `slowapi`, ya usada por el backend).
- **Sin cambios**: `backend/app/rate_limit.py` y la propuesta `rate-limiting-backend` en curso; los "budgets" internos por tarea ya existentes (`FileBudget`, `SearchBudget`) tampoco cambian.
- **Compatibilidad**: ninguna ruptura para el uso legitimo -- los limites se fijan por encima del trafico real esperado (ver design.md).
