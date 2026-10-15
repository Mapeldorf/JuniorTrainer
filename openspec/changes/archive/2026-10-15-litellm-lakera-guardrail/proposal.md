# Proposal

## Why

La mitigacion de prompt injection actual (`prompt-injection-mitigation`, ya archivada) es puramente defensiva por instruccion: delimitadores + una frase pidiendole al modelo que ignore instrucciones dentro del contenido no confiable (respuestas de alumnos, codigo de apoyo, resultados de busqueda web). No hay ninguna capa de deteccion real: si el modelo subyacente falla en seguir esa instruccion, no hay red de seguridad adicional. Lakera Guard añade esa deteccion -- un clasificador especializado que analiza el input antes de que llegue al LLM.

## What Changes

- `infra/litellm/config.yaml`: nueva seccion `guardrails` con un guardrail `lakera-guard` (`guardrail: lakera_v2`, `mode: pre_call`, `default_on: true`): se ejecuta automaticamente en toda llamada de los 5 agentes, sin que ningun agente tenga que pedirlo explicitamente. Si Lakera marca el input como intento de prompt injection, LiteLLM rechaza la llamada antes de invocar al proveedor -- no se gasta presupuesto (budget de la propuesta `litellm-virtual-keys` ya archivada) en una llamada maliciosa.
- `.env`/`.env.example`: nueva variable `LAKERA_API_KEY`.
- `docker-compose.yml`: `restart: unless-stopped` en el servicio `litellm` -- descubierto durante la verificacion que un fallo de red al llamar a Lakera (host inalcanzable) puede tumbar el proceso entero (SIGSEGV), no solo bloquear la llamada; antes no tenia ninguna politica de reinicio (ver design.md).
- Sin cambios en `agents/*`: al igual que con el `422 budget_exceeded` de la propuesta anterior, un rechazo de Lakera (`400`) sube como cualquier otro error del proveedor hasta el framework A2A, que ya lo convierte en tarea fallida.
- La mitigacion existente (delimitadores + instruccion defensiva) se mantiene sin cambios: Lakera es una capa adicional, no un reemplazo.

## Capabilities

### Modified Capabilities
- `prompt-injection-mitigation`: añade un requirement de deteccion automatizada (Lakera Guard) que complementa la mitigacion por instruccion ya existente, aplicada de forma uniforme a los 5 agentes via el proxy LiteLLM.

## Impact

- `infra/litellm/config.yaml`: seccion `guardrails` nueva.
- `.env.example`: variable `LAKERA_API_KEY` nueva.
- `docker-compose.yml`: `restart: unless-stopped` en `litellm`.
- Sin cambios en `agents/*/app/*.py` ni en `backend/*`.
- Nueva dependencia externa: Lakera Guard (cuenta y API key ya creadas por el usuario). Coste de Lakera gestionado en su propia plataforma, fuera de los budgets de LiteLLM que ya tiene este proyecto (son sistemas de facturacion distintos).
