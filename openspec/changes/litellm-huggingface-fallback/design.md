# Design

## Context

Ver `proposal.md` para la motivacion. Investigacion hecha contra documentacion oficial (no supuesta):

- LiteLLM soporta modelos de Hugging Face con el formato `huggingface/<org>/<modelo>` via su API serverless de Inference Providers (sin necesitar un endpoint dedicado), autenticando con `HF_TOKEN`.
- Confirmado contra las paginas reales de Hugging Face: `deepseek-ai/DeepSeek-V4.1-Flash` y `zai-org/GLM-5.3-Flash` tienen la seccion "Inference Providers" activa (varios proveedores detras, entre ellos Novita), por lo que son llamables sin configuracion adicional.
- `litellm_settings.fallbacks` es una lista de mapeos `{model_name: [modelos_de_fallback]}`. Cada llamada fallida al modelo principal se reintenta primero `num_retries` veces contra el mismo modelo, y despues contra los modelos de fallback en orden. Este proyecto ya tiene `num_retries: 0` (propuesta `litellm-proxy-timeout`), asi que un fallo del modelo principal pasa directamente al fallback, sin reintentos previos contra el mismo modelo.
- Las 5 virtual keys ya restringen, via `models`, a que modelos logicos puede llamar cada agente (propuesta `litellm-agent-keys`). Un modelo de fallback es un `model_name` nuevo y distinto del principal -- si la `models` de la key no lo incluye explicitamente, no hay garantia de que LiteLLM permita la llamada de fallback con esa misma key (no documentado de forma concluyente; se verifica empiricamente en las tareas de implementacion). Se opta por el diseño mas seguro: incluir el fallback explicitamente en la `models` de cada key, igual que ya se hace con el modelo principal.

## Goals / Non-Goals

**Goals:**
- Mejorar la disponibilidad real: una caida del proveedor principal (OpenRouter) ya no tira abajo la generacion/evaluacion/revision sin mas.
- Mantener la restriccion de modelo por key intacta: ningun agente gana permiso para llamar a un modelo que no sea su principal o su propio fallback.

**Non-Goals:**
- No se decide aqui el coste de Hugging Face como un budget aparte: la facturacion de HF es independiente de los budgets de LiteLLM ya configurados (mismo caso que Lakera). Si hiciera falta, seria una propuesta aparte sobre gestion de costes de proveedores externos de guardrails/fallback.
- No se usa `context_window_fallbacks` ni `content_policy_fallbacks`: el `fallback` generico (`fallbacks`) cubre el caso que motiva esta propuesta (el proveedor principal no responde o falla), que es mas general que esos dos casos especificos.
- No se sustituye `GLM-5.3-FlashX` por un clon exacto: no existe un checkpoint de FlashX en Hugging Face (es un producto de API optimizado, no un modelo publicado). `zai-org/GLM-5.3-Flash` es la aproximacion mas cercana disponible; se documenta como decision explicita, no como equivalencia exacta.

## Decisions

- **Tres `model_name` de fallback distintos (`generator-fallback-hf`, `evaluator-fallback-hf`, `reviewer-fallback-hf`), no uno compartido**, aunque `generator-fallback-hf` y `evaluator-fallback-hf` apunten al mismo modelo de Hugging Face. Mantiene la misma granularidad de permisos que ya tienen los modelos principales (un `model_name` por modelo logico, cada uno en la `models` de su propia key), en vez de introducir una excepcion a ese patron solo para el fallback.
- **El upsert de `provision_keys.py` se extiende para comparar tambien la lista `models` de la key, no solo `max_budget`/`rpm_limit`.** Si la key existente no incluye su modelo de fallback, se actualiza junto con cualquier otro campo que le falte, en la misma llamada a `/key/update` (mismo patron ya establecido: una sola llamada con lo que falte, nunca pisa lo que ya esta puesto).
- **Riesgo de latencia acumulada, verificado explicitamente en las tareas, no asumido.** Si el modelo principal falla por un *timeout* (40s, `request_timeout`) en vez de un fallo rapido (p. ej. un error de autenticacion), el fallback se dispara DESPUES de agotar esos 40s. El propio intento de fallback tiene su propio `request_timeout` de 40s. En el peor caso (el principal cuelga hasta su timeout Y el fallback tambien), el tiempo total podria superar los 45s del cliente de cada agente -- el mismo tipo de problema que ya aparecio con los reintentos en `litellm-proxy-timeout`, pero esta vez entre modelo principal y modelo de fallback, no entre reintentos del mismo modelo. Las tareas de implementacion miden la latencia real de un fallback disparado por un timeout del principal, no solo por un fallo rapido, y documentan el resultado.

## Risks / Trade-offs

- [Latencia acumulada: un fallo lento del modelo principal (por timeout) deja poco o ningun margen para que el fallback complete dentro de los 45s del cliente] → **Confirmado, no solo hipotetico**: con `request_timeout: 40` (valor heredado de `litellm-proxy-timeout`), el tiempo total medido fue de 45s exactos, sin margen real. Mitigacion aplicada: `request_timeout` reducido a 20 en esta misma propuesta (ver `infra/litellm/config.yaml`); reverificado con un nuevo servidor lento, el tiempo total bajo a 22s, con margen real. Este cambio sustituye el valor de 40s que `litellm-proxy-timeout` habia elegido sin conocer todavia esta interaccion.
- [`GLM-5.3-FlashX` no tiene equivalente exacto en Hugging Face; `GLM-5.3-Flash` puede comportarse de forma distinta (otro tamaño/variante del modelo)] → Mitigacion: aceptado y documentado explicitamente; es un fallback de disponibilidad, no una garantia de resultados identicos al modelo principal -- el objetivo es que la tarea se complete de algun modo razonable, no que sea indistinguible del camino normal.
- [Un fallo masivo y simultaneo del proveedor principal dispararia fallback en las 5 keys a la vez, concentrando trafico nuevo en Hugging Face sin ningun control de ritmo propio hacia ese proveedor] → Mitigacion: el `rpm_limit=60` y el `max_budget=5` ya configurados por key siguen aplicando igual a las llamadas de fallback (son limites de la key, no del modelo); no se añade un limite adicional especifico para Hugging Face en esta propuesta.
