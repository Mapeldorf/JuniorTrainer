# Proposal

## Why

`infra/litellm/config.yaml` no tiene ningun timeout propio: ni `request_timeout` en `litellm_settings`, ni `timeout` por modelo en `litellm_params`. Hoy la unica proteccion contra una llamada colgada es el timeout de 45s del lado del cliente, configurado en cada agente (`agents/*/app/llm.py`: `ChatOpenAI(..., timeout=45.0)`). Si el proveedor subyacente (via OpenRouter) se queda colgado de una forma que el cliente HTTP del agente no detecta limpiamente, no hay ninguna red de seguridad del lado del proxy -- solo los backstops de nivel muy superior (120s por tarea A2A, 300s por generacion completa), que tardarian mucho mas en cortar la llamada y darian un error mucho menos especifico.

## What Changes

- `infra/litellm/config.yaml`: añadir `litellm_settings.request_timeout: 40` -- un timeout global aplicado a toda llamada que LiteLLM hace al proveedor subyacente, para los 3 modelos logicos por igual. Tambien `litellm_settings.num_retries: 0`, para que el timeout corte en un unico intento en vez de que el reintento por defecto de LiteLLM alargue el tiempo hasta el error final muy por encima de los 45s del cliente (descubierto verificando esta misma propuesta, ver design.md).
- Sin cambios en los agentes ni en el backend: el timeout de 45s del cliente de cada agente se mantiene igual; el de LiteLLM (40s) queda por debajo para que sea el que falle primero con un error estructurado y limpio.

## Capabilities

### Modified Capabilities
- `agent-resilience`: añade un requirement de timeout explicito en el propio proxy de LiteLLM, junto a los ya existentes de timeout en el cliente del LLM y en el cliente de Tavily -- misma familia de proteccion (dependencias externas que se quedan colgadas), capa distinta (proxy en vez de cliente).

## Impact

- `infra/litellm/config.yaml`: una linea nueva en `litellm_settings`.
- Sin cambios en `agents/*` ni en `backend/*`.
- Sin nueva dependencia.
