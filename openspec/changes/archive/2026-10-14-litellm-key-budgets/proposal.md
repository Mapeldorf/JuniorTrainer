# Proposal

## Why

Las 5 virtual keys de LiteLLM (propuesta `litellm-agent-keys`, ya archivada) no tienen ningun techo de gasto: un bucle, un bug, o un volumen de pruebas inesperado durante el desarrollo del TFM puede disparar cientos de llamadas sin que nadie se entere hasta ver la factura del proveedor. El rate limiting por IP que ya tienen los agentes (`slowapi`, 60/min) protege de un bucle descontrolado en el tiempo, pero no pone techo de coste acumulado.

## What Changes

- `infra/litellm/provision_keys.py`: las keys se crean ya con `max_budget=5` (USD) y `budget_duration=30d` en la propia llamada a `/key/generate`, no como paso separado.
- El script pasa de "omitir si el alias ya existe" a comportamiento *upsert*: si la key ya existe pero no tiene budget (las 5 que ya hay en desarrollo, creadas antes de esta propuesta), la actualiza via `/key/update` en vez de dejarla tal cual.
- **BREAKING** (solo para entornos ya provisionados con la version anterior del script): al re-ejecutar el script, las 5 keys existentes pasan a tener `max_budget=5`/`budget_duration=30d` donde antes no tenian limite.
- Sin cambios en `agents/*`: al superar su budget, una key queda bloqueada por LiteLLM (comportamiento nativo, HTTP 422 `budget_exceeded`) y la llamada falla como cualquier otro error del proveedor (timeout, rate limit) que los agentes ya propagan como fallo de la tarea A2A -- no hace falta manejo nuevo.

## Capabilities

### Modified Capabilities
- `litellm-agent-keys`: añade un requirement de techo de gasto por key (bloqueo al superarlo) al capability ya archivado en `openspec/specs/litellm-agent-keys/spec.md`.

## Impact

- `infra/litellm/provision_keys.py`: logica de creacion pasa a incluir budget; logica de deteccion de "ya existe" pasa a comprobar tambien si tiene budget, y actualizarlo si no.
- Sin cambios en `agents/*/app/config.py`, `llm.py`, ni en ningun schema o endpoint del backend.
- Sin dashboard ni alertas proactivas de consumo (email/Slack): fuera de alcance, queda como posible propuesta futura.
