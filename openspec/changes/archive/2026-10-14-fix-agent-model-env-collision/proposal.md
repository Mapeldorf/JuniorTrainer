# Proposal

## Why

Detectado durante la verificacion end-to-end de `litellm-key-budgets`: al ejecutar un flujo real a traves de `agent-reviewer`, LiteLLM devolvio `403 key_model_access_denied` para el modelo `openrouter/z-ai/glm-5.3-flashx` -- un nombre de proveedor real, no el alias logico `reviewer` que la virtual key del agente tiene permitido. Causa raiz confirmada con `docker compose exec agent-reviewer env`: `infra/litellm/config.yaml` usa `GENERATOR_MODEL`/`EVALUATOR_MODEL`/`REVIEWER_MODEL` para que **LiteLLM** resuelva cada modelo logico a su proveedor real, pero `docker-compose.yml` pasa `env_file: .env` a los 5 agentes tambien, no solo a `litellm`. Cada agente tiene un campo `Settings` (`generator_model`/`evaluator_model`/`reviewer_model`) que `pydantic-settings` mapea automaticamente a esa misma variable de entorno, asi que el agente acaba leyendo el nombre de proveedor real en vez de su propio alias logico fijo.

Desde que `litellm-virtual-keys` restringe cada key a su modelo logico, este bug hace que las llamadas reales de los 5 agentes fallen con `403`. Es decir: **ahora mismo, con `docker-compose.yml` tal cual esta en `develop`, ningun agente puede completar una llamada real a LiteLLM.**

## What Changes

- `agents/{web,code,exercises}/app/config.py`: eliminar el campo `Settings.generator_model`; `agents/evaluator/app/config.py`: eliminar `evaluator_model`; `agents/reviewer/app/config.py`: eliminar `reviewer_model`. Ninguno de los 5 necesita variar por entorno -- son el alias logico fijo que cada agente siempre envia a LiteLLM, no un dato de configuracion real.
- `agents/*/app/llm.py`: cada uno pasa a usar una constante de modulo (`_MODEL_NAME = "generator"`, `"evaluator"` o `"reviewer"` segun corresponda) en vez de `settings.*_model`.
- Confirmado por inspeccion que el bug es identico en los 5 agentes (mismo patron `campo Settings con default = nombre logico, mapeado por pydantic-settings a una variable que infra/litellm/config.yaml tambien consume`).

## Capabilities

### Modified Capabilities
- `litellm-agent-keys`: añade un requirement explicito de que cada agente resuelve su modelo logico de forma fija, sin depender de ninguna variable de entorno que `infra/litellm/config.yaml` tambien use para resolver el proveedor real -- cierra el hueco que permitio este bug (la spec ya garantizaba la restriccion del lado de LiteLLM, pero nunca garantizaba que el agente enviara el valor correcto).

## Impact

- `agents/{web,code,exercises,evaluator,reviewer}/app/config.py` y `app/llm.py`: 5 archivos de cada tipo, mismo patron de cambio en los 5.
- `.env`/`.env.example`: sin cambios -- `GENERATOR_MODEL`/`EVALUATOR_MODEL`/`REVIEWER_MODEL` siguen existiendo, pero quedan exclusivamente para `infra/litellm/config.yaml`; deja de ser ambiguo que tambien las lea un agente.
- Corrige un bug de correctness activo en `develop`: sin este fix, ningun agente puede completar una llamada real a LiteLLM hoy.
