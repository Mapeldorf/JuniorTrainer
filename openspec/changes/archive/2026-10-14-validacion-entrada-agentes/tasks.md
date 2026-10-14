# Tasks

## 1. Agente de codigo: validar owner/repo por su cuenta

- [x] 1.1 En `agents/code/app/input.py::parse_repo_input`, tras el `.strip()` ya existente de `owner`/`repo`, importar y llamar a `validate_owner_or_repo` de `agents/code/app/github_ref.py` (sin cambios en ese fichero, ya existe) para cada uno, capturando `InvalidGitHubRef` y relanzandola como `InvalidCodeAgentInput` con un mensaje claro. Verificar con un test manual: una entrada con `owner="../evil"` (u otro valor que rompa la regex) lanza `InvalidCodeAgentInput` sin llegar a `list_files`/`read_file`
- [x] 1.2 Confirmar que una entrada con `owner`/`repo` validos (caso normal) sigue funcionando sin cambios: ejecutar `agents/code/scripts/verify_memory_cache.py` o equivalente contra un repositorio real

  Verificado en vivo (`docker compose exec agent-code python -c ...`) contra `Mapeldorf/autobot-frontend` (repo real donde la GitHub App esta instalada, descubierto via `GET /installation/repositories`): `analyze_repo` completa con normalidad, `memory_hit=False`, resumen y 7 fragmentos reales.

## 2. Limite de tecnologias en el backend

- [x] 2.1 En `backend/app/schemas/generation.py`, anadir las constantes `_MAX_TECHNOLOGIES = 15` y `_MAX_TECHNOLOGY_LENGTH = 60`, y extender `_normalize_technologies` (o anadir un `field_validator` nuevo) para rechazar con `ValueError` una lista con mas de `_MAX_TECHNOLOGIES` elementos, o cualquier elemento con mas de `_MAX_TECHNOLOGY_LENGTH` caracteres tras recortar espacios. Verificar: `POST /generations` con 16 tecnologias, o con una tecnologia de 61 caracteres, responde `422` sin crear fila en `generation`

  Verificado por construccion directa del esquema (sin servidor HTTP): 16 tecnologias y una tecnologia de 61 caracteres lanzan `ValidationError`; 2 tecnologias normales se aceptan sin cambios. Verificacion contra `POST /generations` real (422 HTTP) en la tarea 4.1.
- [x] 2.2 Verificar que una generacion dentro de los limites (p. ej. 3 tecnologias cortas) sigue aceptandose con normalidad: repetir una verificacion existente (`backend/scripts/verify_generation_e2e.py` u otra invocacion equivalente) y confirmar que no se rompe por este cambio

  `verify_generation_e2e.py` sigue roto por el bug preexistente ya documentado en el change `autenticacion-backend-agentes` (firma antigua de `run_generation`), no relacionado con este cambio. Verificado en su lugar llamando a `orchestrator.run_generation` directamente (firma actual, datos de prueba limpiados al terminar) con 2 tecnologias: `status=ready`, 1 candidato generado, sin ningun efecto del nuevo limite.

## 3. Limite de tecnologias en el agente web

- [x] 3.1 En `agents/web/app/input.py`, anadir las mismas constantes (`_MAX_TECHNOLOGIES = 15`, `_MAX_TECHNOLOGY_LENGTH = 60`, con un comentario que remita a `backend/app/schemas/generation.py` como la otra copia del mismo limite) y una excepcion `InvalidTechnologiesInput(ValueError)`. Tras `_normalize`, rechazar con esa excepcion si hay mas de `_MAX_TECHNOLOGIES` elementos o alguno supera `_MAX_TECHNOLOGY_LENGTH` caracteres. Verificar con un test manual: una lista de 16 tecnologias (o una de 61 caracteres) lanza `InvalidTechnologiesInput` sin llamar a `research_with_checkpoint`

  Verificado en proceso: 16 tecnologias y una tecnologia de 61 caracteres lanzan `InvalidTechnologiesInput` (antes de llegar a `research_with_checkpoint`, que ni se llama); 2 tecnologias normales se aceptan sin cambios.
- [x] 3.2 Confirmar que una entrada dentro de los limites sigue funcionando: ejecutar `agents/web/scripts/verify_tavily_search.py` o equivalente con una lista corta de tecnologias

  Verificado en vivo via `send_a2a_task` contra `agent-web` real (rebuild con el codigo nuevo) con `["Markdown"]`: Tavily + LLM real, resumen y 5 fuentes devueltas con normalidad.

## 4. Verificacion de rechazo end-to-end

- [x] 4.1 Con el stack completo levantado, enviar una peticion `POST /generations` con 16 tecnologias y confirmar `422` sin que se cree fila en `generation` ni se invoque a ningun agente (revisar logs: ni `agent-web` ni `agent-code`/`agent-exercises` reciben la tarea)

  Verificado via `TestClient` real contra `app` (stack de middleware completo: CORS, rate limit, body size, security headers), con `require_tech_lead` sobreescrito para apuntar a un tech_lead real (sin usar contraseñas/JWT reales). 16 tecnologias -> `422` con el mensaje exacto del validador, sin ninguna fila nueva en `generation`. El caso normal (2 tecnologias) sigue devolviendo `201` y crea/completa la generacion con normalidad; datos de prueba limpiados.
- [x] 4.2 Enviar directamente al agente web (saltando el backend, con la credencial de servicio correcta) una tarea con `owner`/`repo` invalido al agente de codigo y con mas de 15 tecnologias al agente web, confirmando que cada uno rechaza la tarea por su cuenta sin necesitar que el backend la hubiera filtrado antes

  Verificado via `send_a2a_task` directo (credencial de servicio real, sin pasar por `backend/app/orchestrator.py`): `agent-code` rechaza `owner="../evil"` y `agent-web` rechaza una lista de 16 tecnologias, cada uno con su propio mensaje de error. El log de `agent-code` confirma que `parse_repo_input` lanza antes de que se llame a `list_files`/`read_file` (sin trafico a la API de GitHub).
