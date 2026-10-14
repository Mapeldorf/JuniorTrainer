# Proposal

## Why

Hoy los 5 agentes (web, code, exercises, evaluator, reviewer) autentican contra el proxy de LiteLLM con la misma `LITELLM_MASTER_KEY`, copiada tal cual en cada uno. LiteLLM no puede distinguir qué agente hizo cada llamada: no hay atribución de coste/uso por agente, ninguna key puede revocarse sin romper los otros cuatro agentes, y cualquier agente puede en teoría llamar a cualquier modelo logico (incluidos los de otro agente), no solo al suyo.

## What Changes

- Nuevo contenedor Postgres dedicado (`litellm-db`) en `docker-compose.yml`, solo para las tablas internas de LiteLLM (gestión de keys/budgets vía Prisma). Aislado del Postgres de Supabase que ya usan los agentes para memoria.
- `infra/litellm/config.yaml`: añadir `general_settings` con `master_key` (pasa a ser solo de administración, ya no la usan los agentes para llamadas de negocio) y `database_url` apuntando al nuevo Postgres.
- 5 virtual keys, una por agente físico, cada una restringida por `models` al modelo lógico que ese agente necesita (web/code/exercises → `generator`; evaluator → `evaluator`; reviewer → `reviewer`), generadas una vez con un script de aprovisionamiento (`infra/litellm/provision_keys.py`) contra la API `/key/generate` de LiteLLM.
- **BREAKING**: cada agente deja de leer `LITELLM_MASTER_KEY` y pasa a leer su propia variable (`AGENT_WEB_LITELLM_KEY`, `AGENT_CODE_LITELLM_KEY`, `AGENT_EXERCISES_LITELLM_KEY`, `AGENT_EVALUATOR_LITELLM_KEY`, `AGENT_REVIEWER_LITELLM_KEY`); el `.env` de cualquier entorno existente deja de funcionar para los agentes hasta rellenar las 5 variables nuevas con las keys generadas por el script.
- `.env.example` actualizado con las 5 variables nuevas, la nota de `LITELLM_MASTER_KEY` reducida a su nuevo alcance (solo administración/aprovisionamiento), y las variables del nuevo Postgres (`LITELLM_DB_*`).

## Capabilities

### New Capabilities
- `litellm-agent-keys`: cada agente autentica contra el proxy de LiteLLM con una credencial propia, restringida al modelo lógico que le corresponde, atribuible y revocable de forma independiente del resto de agentes.

### Modified Capabilities
(ninguna: no existe aun ningun capability archivado sobre autenticacion/autorizacion de los agentes frente a LiteLLM al que aplicar un delta; `agent-auth` en `openspec/specs/` cubre la autenticacion backend->agentes, un perimetro distinto, no agente->LiteLLM)

## Impact

- `docker-compose.yml`: nuevo servicio `litellm-db` (Postgres + volumen) y `DATABASE_URL` en el servicio `litellm`.
- `infra/litellm/config.yaml`: `general_settings.master_key` y `general_settings.database_url`.
- `infra/litellm/provision_keys.py` (nuevo): script de aprovisionamiento de las 5 virtual keys, ejecutado una vez por entorno.
- `agents/{web,code,exercises,evaluator,reviewer}/app/config.py` y `app/llm.py`: cada uno sustituye `litellm_master_key` por su propia variable de virtual key.
- `.env.example`: 5 variables nuevas de virtual keys + variables del Postgres dedicado; `LITELLM_MASTER_KEY` se mantiene pero con alcance reducido.
- Sin cambios en el contrato de ningun endpoint del backend ni en los schemas de negocio.
