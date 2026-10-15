# Proposal

## Why

LiteLLM expone su UI de administracion (`/ui`) por defecto, y el puerto 4000 ya esta publicado al host en `docker-compose.yml` (necesario para el desarrollo y la verificacion manual de este proyecto). Verificado contra el entorno real: la UI responde ahora mismo (`GET /ui` -> `307`, redirige al login). Sin `UI_PASSWORD` configurada, el login acepta la `LITELLM_MASTER_KEY` compartida como contraseña de administrador -- la misma credencial que ya usa `provision_keys.py` para gestionar keys/budgets. Cualquiera con acceso al puerto 4000 y esa key puede entrar a la UI con control total (crear/revocar keys, cambiar budgets) sin que exista ningun registro de quien lo hizo.

## What Changes

- `.env`/`.env.example`: nuevas variables `LITELLM_UI_USERNAME` y `LITELLM_UI_PASSWORD`, distintas de `LITELLM_MASTER_KEY`. En cuanto `UI_PASSWORD` esta puesta, el login deja de aceptar la master key como contraseña (comportamiento nativo de LiteLLM, confirmado en su documentacion).
- `docker-compose.yml`: las dos variables se pasan al servicio `litellm` como `UI_USERNAME`/`UI_PASSWORD` (los nombres que LiteLLM espera; con prefijo `LITELLM_` en `.env` para evitar otra colision de nombres como la de `fix-agent-model-env-collision` si algun otro servicio tuviera alguna vez una variable `UI_USERNAME`/`UI_PASSWORD` propia).
- Sin cambios en `infra/litellm/config.yaml`: estas credenciales son variables de entorno que LiteLLM lee directamente, no campos de `config.yaml` (mismo patron que `LAKERA_API_KEY`/`PRESIDIO_ANALYZER_API_BASE`).

## Capabilities

### New Capabilities
- `litellm-admin-access`: la UI de administracion de LiteLLM autentica con una credencial propia, distinta de la `master_key` que usan los scripts de aprovisionamiento y la administracion por API.

## Impact

- `.env.example`: 2 variables nuevas.
- `docker-compose.yml`: 2 entradas nuevas en `environment` del servicio `litellm`.
- Sin cambios en `agents/*`, `backend/*` ni `infra/litellm/config.yaml`.
- Sin nueva dependencia ni contenedor nuevo: la UI ya forma parte de la imagen de LiteLLM que ya se usa.
