# Tasks

## 1. Credencial y configuracion de LiteLLM

- [x] 1.1 Añadir `HF_TOKEN` a `.env.example` (sin valor) y confirmar que ya esta en el `.env` local del usuario (ya creado). Confirmado.
- [x] 1.2 En `infra/litellm/config.yaml`, añadir las 3 entradas nuevas a `model_list` (`generator-fallback-hf`, `evaluator-fallback-hf` -> `huggingface/deepseek-ai/DeepSeek-V4.1-Flash`; `reviewer-fallback-hf` -> `huggingface/zai-org/GLM-5.3-Flash`), todas con `api_key: os.environ/HF_TOKEN`. Añadir `litellm_settings.fallbacks` con los 3 mapeos (`generator`->`[generator-fallback-hf]`, etc.). Verificar que el YAML sigue siendo valido. Verificado.
- [x] 1.3 Recrear `litellm` (`docker compose up -d --force-recreate litellm`) y confirmar en los logs que arranca sin error con los 6 modelos logicos (3 principales + 3 de fallback) cargados. Verificado.

## 2. Extender el aprovisionamiento de virtual keys

- [x] 2.1 En `infra/litellm/provision_keys.py`, extender `_AGENT_MODELS` para que cada agente incluya tambien su modelo de fallback (p. ej. `"agent-web": ["generator", "generator-fallback-hf"]`). Extender `_missing_fields`/el upsert para comparar la `models` de la key existente contra la lista deseada y actualizarla (junto con cualquier otro campo que falte) si no coincide. Verificar que `python -c "import ast; ast.parse(open('infra/litellm/provision_keys.py').read())"` no falla. Verificado.
- [x] 2.2 Ejecutar el script sobre las 5 keys ya existentes y verificar con `GET /key/list?key_alias=<alias>&return_full_object=true` que cada una queda con su modelo principal y su fallback en `models` (p. ej. `agent-web` -> `["generator", "generator-fallback-hf"]`). Verificado: las 5 se actualizaron solo con `models` (ya tenian budget y rpm_limit); `agent-web` confirma `['generator', 'generator-fallback-hf']`.
- [x] 2.3 Re-ejecutar el script inmediatamente despues y confirmar que no vuelve a tocar esas 5 keys (ya tienen todos los campos, incluida la `models` actualizada). Verificado: las 5 reportan "ya existe completa, omitida".

## 3. Verificacion del fallback real

- [x] 3.1 Provocar un fallo rapido del modelo principal de forma controlada (p. ej. apuntar temporalmente `GENERATOR_API_KEY` a un valor invalido en `.env` y recrear `litellm`) y, con una virtual key real, confirmar que la llamada se completa igualmente -- verificar en la respuesta que el proveedor/modelo que respondio es el de Hugging Face (campo `provider`/`model` de la respuesta), no OpenRouter. Revertir la credencial invalida al terminar. Verificado: con `GENERATOR_API_KEY` invalida, la llamada respondio `200` con `"model":"deepseek-ai/DeepSeek-V4.1-Flash"` -- el fallback a HF se disparo y completo la llamada. Credencial restaurada.
- [x] 3.2 Confirmar que una llamada normal (con el modelo principal funcionando) sigue respondiendo desde OpenRouter, sin invocar el fallback (mismo comportamiento que antes de esta propuesta). Verificado: `model: generator`, `provider: CoreWeave` (proveedor real de OpenRouter, no HF).
- [x] 3.3 Confirmar que una virtual key no puede llamar directamente al modelo de fallback de otro agente (p. ej. la key de `agent-evaluator` contra `generator-fallback-hf`) -- debe rechazarse igual que cualquier otro modelo no permitido, confirmando que la restriccion de modelo por key sigue intacta con el fallback añadido. Verificado: `403 key_model_access_denied`.

## 4. Latencia acumulada ante un timeout del principal

- [x] 4.1 Provocar un fallo del modelo principal por TIMEOUT, no por fallo rapido (p. ej. apuntar temporalmente el modelo principal a un servidor que responda tarde, similar a la verificacion hecha en `litellm-proxy-timeout`), y medir el tiempo total hasta que el fallback responde (o falla). Documentar el resultado observado en este fichero: si el tiempo total queda dentro de los 45s del cliente de cada agente, o si los supera. **Hallazgo critico**: con `request_timeout: 40` (valor de `litellm-proxy-timeout`), el tiempo total hasta la respuesta del fallback de HF fue de **45s exactos** -- justo en el limite del timeout de 45s del cliente de cada agente, sin margen real. El riesgo anticipado en `design.md` se confirma.
- [x] 4.2 Segun lo observado en 4.1, evaluar si hace falta un ajuste (p. ej. reducir `request_timeout` del proxy) y aplicarlo si corresponde, volviendo a verificar. Revertir cualquier configuracion temporal de la tarea 4.1 al terminar. Ajuste aplicado: `request_timeout` reducido de 40 a 20 en `infra/litellm/config.yaml`. Reverificado con un nuevo servidor lento: **22s totales** (vs los 45s anteriores), margen real frente al timeout de 45s del cliente. Entorno de prueba revertido (servidor lento eliminado, `config.yaml` restaurado al modelo real).
