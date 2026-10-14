# Tasks

## 1. Timeout en el cliente LLM (5 agentes)

- [x] 1.1 En `agents/code/app/llm.py`, anadir `timeout=45.0` a la construccion de `ChatOpenAI`. Verificar: una llamada normal sigue funcionando; revisar que `ChatOpenAI`/`langchain-openai` acepta el parametro `timeout` (documentarlo si el nombre real difiere, p. ej. `request_timeout`)

  Confirmado: `timeout` es un alias de pydantic de `request_timeout` en `ChatOpenAI` (`langchain-openai`); `ChatOpenAI(..., timeout=45.0).request_timeout == 45.0`.

- [x] 1.2 Repetir 1.1 en `agents/evaluator/app/llm.py`
- [x] 1.3 Repetir 1.1 en `agents/exercises/app/llm.py`
- [x] 1.4 Repetir 1.1 en `agents/reviewer/app/llm.py`
- [x] 1.5 Repetir 1.1 en `agents/web/app/llm.py`

## 2. Timeout en el cliente Tavily

- [x] 2.1 En `agents/web/app/service.py`, anadir `timeout=15.0` (o el nombre de parametro correcto segun la version de `tavily-python` instalada) a la construccion de `AsyncTavilyClient`. Verificar con una busqueda real que sigue funcionando sin cambios

  Ajuste de implementacion: `AsyncTavilyClient.__init__` no acepta `timeout` (solo un `client: httpx.AsyncClient` opcional); el metodo `search()` si acepta `timeout` por llamada (default de la libreria: 60s). Se aplico `timeout=15.0` en la llamada `client.search(...)` dentro de `agents/web/app/tools/tavily_search.py::tavily_search`, el unico punto donde se invoca. Verificado en vivo (dentro del contenedor, por un problema de certificados SSL locales fuera de Docker no relacionado con el cambio): busqueda real devuelve 5 resultados con normalidad.

## 3. Rate limiting por IP (5 agentes)

- [x] 3.1 Anadir `slowapi` a `agents/code/requirements.txt` (misma version que ya fija `backend/requirements.txt`), y repetir en `agents/{evaluator,exercises,reviewer,web}/requirements.txt`
- [x] 3.2 Crear `agents/code/app/rate_limit.py` con un `Limiter(key_func=get_remote_address, default_limits=["60/minute"])`, igual de forma que `backend/app/rate_limit.py` pero sin la key function por `profile.id` (los agentes no tienen usuario final, ver design.md)
- [x] 3.3 En `agents/code/app/main.py`, montar `app.state.limiter`, `app.add_middleware(SlowAPIMiddleware)` DESPUES de `app.add_middleware(ServiceAuthMiddleware)` (para que el rate limiting sea la capa mas exterior y se ejecute antes, ver design.md "Orden del middleware"), y registrar el exception handler de `RateLimitExceeded` devolviendo `429` con un cuerpo minimo, igual que `backend/app/main.py`. Verificar con un test manual: mas de 60 peticiones en el mismo minuto a cualquier ruta reciben `429` sin ejecutar logica de negocio; una peticion dentro del limite sigue funcionando con normalidad

  Verificado empiricamente con `TestClient` (65 peticiones sin credencial en bucle): las primeras 60 devuelven `401` (ServiceAuthMiddleware), las 5 siguientes devuelven `429` -- confirma que `SlowAPIMiddleware` es la capa mas exterior y cuenta la peticion antes de que `ServiceAuthMiddleware` compare la credencial, tal como pide el diseño.
- [x] 3.4 Repetir 3.2 y 3.3 (modulo `rate_limit.py` + montaje en `main.py`) en `agents/evaluator`
- [x] 3.5 Repetir 3.2 y 3.3 en `agents/exercises`
- [x] 3.6 Repetir 3.2 y 3.3 en `agents/reviewer`
- [x] 3.7 Repetir 3.2 y 3.3 en `agents/web`

  Verificado por import en los 4 (`from app.main import app` sin errores, mismo orden de middleware `['SlowAPIMiddleware', 'ServiceAuthMiddleware']` que en `agents/code`). Verificacion funcional completa (401/429) en el grupo 4.

## 4. Verificacion end-to-end

- [x] 4.1 Con el stack completo levantado, confirmar que un flujo de generacion y uno de evaluacion completos (dentro de los limites) siguen funcionando con normalidad tras anadir los timeouts y el rate limiting en los 5 agentes

  Verificado en vivo con los 5 agentes reconstruidos: `evaluate_answer` (evaluador+revisor) completa con `verdict=correct`; `run_generation` (web+exercises, sin repositorio) completa con `status=ready` y 1 candidato. Datos de prueba limpiados.
- [x] 4.2 Enviar mas de 60 peticiones en menos de un minuto a uno de los agentes (p. ej. peticiones repetidas a su Agent Card) y confirmar `429` en las que excedan el limite, sin que se dispare ningun gasto de LLM/GitHub/Tavily para esas peticiones

  Verificado en vivo contra `agent-web` real (65 peticiones con credencial correcta, probando especificamente la capa de rate limit): 59 `200`, 6 `429` a partir de ahi. Los logs del agente confirman que las peticiones rechazadas no dejan ningun rastro de llamada a LLM/Tavily, solo el `429`.
