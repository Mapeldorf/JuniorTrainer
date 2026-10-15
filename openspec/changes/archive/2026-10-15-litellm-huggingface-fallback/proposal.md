# Proposal

## Why

Hoy, si el proveedor subyacente de un modelo logico (OpenRouter) falla o esta caido, LiteLLM no tiene ninguna forma de recuperarse: la llamada falla sin mas, con el `request_timeout: 40` como unica red de seguridad (que acota el tiempo de espera, no mejora la disponibilidad). Un fallback automatico a un segundo proveedor mejora la disponibilidad real frente a una caida externa del proveedor principal.

## What Changes

- `infra/litellm/config.yaml`: 3 entradas nuevas en `model_list`, una por modelo logico, sirviendo via Hugging Face Inference Providers (serverless, sin endpoint dedicado):
  - `generator-fallback-hf` y `evaluator-fallback-hf` -> `huggingface/deepseek-ai/DeepSeek-V4.1-Flash` (mismo modelo que ya usan `GENERATOR_MODEL`/`EVALUATOR_MODEL` en OpenRouter).
  - `reviewer-fallback-hf` -> `huggingface/zai-org/GLM-5.3-Flash`. **Sustitucion documentada**: `GLM-5.3-FlashX` (el modelo que usa `REVIEWER_MODEL` hoy) es un producto de API de Z.ai, no un checkpoint publicado en Hugging Face; `zai-org/GLM-5.3-Flash` es el equivalente abierto mas cercano disponible via Inference Providers de HF.
- `litellm_settings.fallbacks`: `generator` -> `[generator-fallback-hf]`, `evaluator` -> `[evaluator-fallback-hf]`, `reviewer` -> `[reviewer-fallback-hf]`. Si la llamada al modelo principal falla, LiteLLM reintenta automaticamente contra el modelo de Hugging Face correspondiente antes de devolver el error al agente.
- `infra/litellm/config.yaml`: `litellm_settings.request_timeout` reducido de 40 a 20. Descubierto verificando esta misma propuesta: con 40s, un timeout del modelo principal seguido del fallback sumaba 45s exactos, sin margen real frente al timeout de 45s del cliente de cada agente. Con 20s, el peor caso queda en 40s, con margen.
- `.env`/`.env.example`: nueva variable `HF_TOKEN` (compartida, no por agente -- autentica contra Hugging Face, no es una credencial de negocio de ningun agente concreto).
- `infra/litellm/provision_keys.py`: cada virtual key pasa a incluir, ademas de su modelo logico principal, el modelo de fallback que le corresponde en su lista de `models` permitidos (p. ej. la key de `agent-web` pasa a permitir `["generator", "generator-fallback-hf"]`). El upsert se extiende para actualizar esta lista en las keys ya existentes que no la tengan.

## Capabilities

### Modified Capabilities
- `agent-resilience`: añade un requirement de fallback automatico a un proveedor alternativo cuando el modelo logico principal falla, complementando el timeout de proxy ya existente (proteccion de disponibilidad, no solo de tiempo de espera).

## Impact

- `infra/litellm/config.yaml`: 3 entradas nuevas en `model_list`, seccion `fallbacks` en `litellm_settings`, `request_timeout` reducido de 40 a 20.
- `infra/litellm/provision_keys.py`: upsert extendido para incluir el modelo de fallback en `models` de cada key.
- `.env.example`: variable `HF_TOKEN` nueva.
- Sin cambios en `agents/*/app/*.py` ni en `backend/*`.
- Nueva dependencia externa: Hugging Face Inference Providers (cuenta y token ya creados por el usuario). Facturacion propia de HF, fuera de los budgets de LiteLLM ya configurados (igual que ya ocurre con Lakera, sistemas de facturacion distintos).
