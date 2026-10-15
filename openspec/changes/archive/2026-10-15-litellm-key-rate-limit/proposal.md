# Proposal

## Why

Los 5 agentes ya limitan peticiones entrantes por IP (`slowapi`, 60/min, `agents/*/app/rate_limit.py`), pero eso protege la entrada al agente, no su salida hacia LiteLLM. Las 5 virtual keys (`litellm-agent-keys`) tienen techo de gasto (`litellm-key-budgets`) pero ningun limite de ritmo: una rafaga de llamadas podria agotar el presupuesto mensual de una key en minutos, sin margen para reaccionar antes de que el budget la bloquee.

## What Changes

- `infra/litellm/provision_keys.py`: cada virtual key se crea (y se actualiza via upsert, igual que el budget) con `rpm_limit=60` -- mismo numero que ya usa `slowapi` en cada agente, para que el limite en LiteLLM no sea mas permisivo que el que ya existe en la entrada del agente.
- Sin `tpm_limit`: el rate limiting que se esta replicando (`slowapi` en los agentes) es por numero de peticiones, no por tokens; añadir un limite de tokens seria una proteccion distinta, no pedida por esta propuesta.
- Sin cambios en `agents/*`: un rechazo por rate limit de LiteLLM (`429`) sube como cualquier otro error del proveedor hasta el framework A2A, que ya lo convierte en tarea fallida (mismo patron que `budget_exceeded` y el guardrail de Lakera).

## Capabilities

### Modified Capabilities
- `litellm-agent-keys`: añade un requirement de limite de ritmo por key (peticiones por minuto), complementario al techo de gasto ya existente.

## Impact

- `infra/litellm/provision_keys.py`: logica de creacion y upsert extendida para incluir `rpm_limit`.
- Sin cambios en `agents/*/app/*.py` ni en `backend/*`.
- Sin nueva dependencia.
