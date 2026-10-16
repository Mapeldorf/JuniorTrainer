# Proposal

## Why

Hoy el único filtro sobre el campo Tecnologías es de forma (nº y longitud): cualquier cadena pasa, y sin repositorio el orquestador invoca directamente al agente web, que puede devolver una investigación cacheada para esa misma clave y producir ejercicios igualmente. Se ha comprobado en uso real escribiendo un DNI en Tecnologías: el sistema genera candidatos en vez de rechazar una entrada que no es una tecnología de programación.

## What Changes

- Se añade un **agente validador** (A2A, `agents/validator/`) que actúa como **puerta previa** del flujo de generación: decide si las tecnologías introducidas son tecnologías de programación y solo entonces el orquestador continúa con web/código/ejercicios.
- El validador es **default-deny**: solo aprueba cuando **todas** las entradas son tecnologías claramente reconocibles; ante duda, ambigüedad o texto que no lo sea, devuelve rechazo.
- Si el validador rechaza, o si falla (transporte, timeout, bloqueo de guardarraíl o respuesta inválida), la generación termina en estado `error` y **no se ejecuta ningún otro agente** (fail-closed). Como consecuencia, una entrada inválida nunca llega a la caché del agente web.
- El validador usa el modelo lógico `validator` (GLM-5.3-Flash, primario por OpenRouter y fallback por Hugging Face con el mismo modelo) con **salida estructurada estricta** (`response_format` / JSON schema).
- **Guardarraíles reforzados solo para el validador**: Presidio PII en modo `BLOCK` (rechaza email/teléfono/tarjeta/IP/IBAN) y Lakera Guard en modo `block` (rechaza intentos de prompt injection), ambos vinculados a sus deployments. La virtual key del validador queda fuera del guardarraíl global `lakera-guard` (`opted_out_global_guardrails`) porque, al implementar, se comprobó que ese global **enmascara** la PII que detecta antes de que Presidio pueda bloquearla.
- **Pre-filtro determinista** dentro del agente (regex de email, teléfono, IBAN y DNI/NIE) que rechaza antes de llamar al LLM, cubriendo el caso del DNI de forma no probabilística.
- El validador revalida los mismos límites de entrada (≤ 15 tecnologías, ≤ 60 caracteres) de forma independiente, siguiendo el patrón de defensa en profundidad del proyecto.
- La respuesta rechazada no cambia la interfaz: la generación queda en `error`, por lo que ya no aparece en el listado y se avisa con el mensaje agregado existente (`ocultar-generaciones-error`).

Fuera de alcance: cambiar el estado `error` ni su mensaje, rediseñar la pantalla de revisión, tocar la caché del agente web o el catálogo de tecnologías del backend, y añadir validación de contenido en el propio schema del backend (el rechazo ocurre en el agente, no antes de crear la generación).

## Capabilities

### New Capabilities
- `technology-validation`: define la validación de que las tecnologías de una generación son tecnologías de programación antes de arrancar el flujo, mediante un agente juez default-deny con salida estructurada estricta, pre-filtro determinista de PII/identificadores y guardarraíles de bloqueo, y la regla de error (fail-closed) cuando la entrada no es válida.

### Modified Capabilities
- `exercise-generation`: la orquestación pasa a tener un paso previo obligatorio de validación de tecnologías, y una entrada no tecnológica (o un fallo del validador) marca la generación en `error` sin lanzar los agentes de entrada.
- `agent-auth`: la credencial de servicio pasa a exigirse también al agente `validator` (la capacidad enumeraba los 5 agentes existentes).
- `prompt-injection-mitigation`: la detección automática del proxy, hoy de solo observación para todos los agentes, pasa a **bloquear** en las llamadas del validador.
- `pii-redaction`: se añade la detección de PII en modo de bloqueo (`BLOCK`) para el validador, que rechaza la llamada, distinta del modo de sustitución por marcador (`MASK`) de evaluador y revisor.
- `agent-trace-privacy`: el input del validador (texto introducido por el usuario) deja de registrarse en claro en Langfuse.

## Impact

- **Nuevo agente** `agents/validator/` (A2A en el puerto 8015; estructura espejo de `agents/evaluator/`): `input.py`, `service.py`, `llm.py`, `config.py`, `agent_card.py`, `executor.py`, `main.py`, `rate_limit.py`, `service_auth.py`, `tracing.py`, `run.py`, `Dockerfile`, `requirements.txt`, `scripts/verify_*`.
- **Backend**: `backend/app/config.py` (URL del validador) y `backend/app/orchestrator.py` (llamada de validación como primer paso de `_orchestrate`).
- **LiteLLM**: `infra/litellm/config.yaml` (modelos `validator` y `validator-fallback-hf`, guardarraíles `presidio-pii-block` y `lakera-guard-block`, `fallbacks`) e `infra/litellm/provision_keys.py` (virtual key `agent-validator`).
- **Infra**: `docker-compose.yml` (servicio `agent-validator` y `depends_on` del backend) y `.env.example` (`VALIDATOR_MODEL`, `VALIDATOR_API_KEY`, `AGENT_VALIDATOR_LITELLM_KEY`).
- **Specs**: delta de las capacidades anteriores en `openspec/specs/`.
- **Sin cambios de frontend.**
