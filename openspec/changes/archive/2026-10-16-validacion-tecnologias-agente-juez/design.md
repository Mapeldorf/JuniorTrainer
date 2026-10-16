# Design

## Context

El flujo de generacion (change `generacion-ejercicios-agentes`) es: `POST /generations` crea la fila `generation` y lanza el orquestador en segundo plano; `_orchestrate` (`backend/app/orchestrator.py`) resuelve el commit (si hay repositorio) y llama al agente web y, si hay repo, al de codigo, y despues al de ejercicios. Sin repositorio solo se ejecuta el agente web (`_gather_inputs`, lineas 96-98).

La unica validacion de tecnologias hoy es de forma, en `backend/app/schemas/generation.py` (max 15, max 60 caracteres) y su copia en `agents/web/app/input.py`; el design archivado `2026-10-14-validacion-entrada-agentes` descarto explicitamente un catalogo cerrado de tecnologias. Ademas, el agente web cachea investigaciones por clave exacta de tecnologias (`agents/web/app/memory.py`), de modo que una entrada repetida (p. ej. el mismo DNI) devuelve el resumen guardado y la generacion continua como si la entrada fuera valida.

Ya existen dos defensas reutilizables: la credencial de servicio backend-agente (`specs/agent-auth`) y los guardarrailes del proxy LiteLLM (`presidio-pii`, Lakera `lakera-guard`). Ver `proposal.md` para el motivo.

## Goals / Non-Goals

**Goals:**
- Rechazar, antes de generar nada, cualquier conjunto de tecnologias que no sean tecnologias de programacion, mediante un agente juez con veredicto estructurado.
- Que el rechazo o el fallo del validador sean fail-closed: la generacion termina en `error` y no se ejecuta ningun agente de entrada.
- Ser muy restrictivo con la entrada del validador (PII y prompt injection en modo bloqueo), sin afectar a los demas agentes.
- Mantener latencia baja en un paso que se ejecuta siempre.

**Non-Goals:**
- No se anade un catalogo cerrado ni canonicalizacion semantica de tecnologias.
- No se cambia la validacion de forma del backend ni se adelanta el rechazo a la creacion de la fila de `generation`.
- No se toca la cache del agente web, ni los agentes web/codigo/ejercicios, ni la interfaz (el aviso agregado de `ocultar-generaciones-error` ya cubre el caso).
- No se cambia el modelo `generator` ni los modelos de evaluador/revisor.

## Decisions

### 1. Agente juez dedicado como puerta previa, no validacion en el schema del backend

Se anade un agente A2A `agents/validator/` que se invoca como primer paso del orquestador. Se descarta validar en `StartGenerationRequest` (backend) porque la decision es semantica (requiere un modelo) y porque se decidio, con el usuario, que el rechazo debe terminar en estado `error` de la generacion (no en un 422 que impida crear la fila). El agente revalida, ademas, los limites de forma, siguiendo el patron de defensa en profundidad del proyecto (`count` en el agente de ejercicios, `owner`/`repo` en el agente de codigo).

### 2. Modelo juez: general y rapido, GLM-5.3-Flash, mismo modelo en los dos proveedores

Se usa un modelo general rapido en vez de un modelo especificamente de decision. Se evaluo TypeSafe Jev (un modelo de decisiones tipadas, candidato natural para un juez) y se **descarto**: su via fuerte (System 1, `POST /v1/decide`) devuelve solo probabilidades, sin razon ni JSON libre, y esa interfaz no se puede enrutar por el proxy LiteLLM, que solo expone chat completions; los guardarrailes de bloqueo que exige este change viven en LiteLLM, asi que renunciar al proxy para usar `/v1/decide` era inviable. Ademas su id de OpenRouter (`typesafe/jev-router`) enruta a un modelo cerrado sin equivalente de pesos abiertos, lo que impide el patron "mismo modelo, dos proveedores".

Elegido: **GLM-5.3-Flash**, configurable por `VALIDATOR_MODEL`:

```yaml
- model_name: validator
  litellm_params:
    model: os.environ/VALIDATOR_MODEL          # openrouter/z-ai/glm-5.3-flash
    api_key: os.environ/VALIDATOR_API_KEY
    guardrails: ["presidio-pii-block", "lakera-guard-block"]

- model_name: validator-fallback-hf
  litellm_params:
    model: huggingface/zai-org/GLM-5.3-Flash
    api_key: os.environ/HF_TOKEN
    guardrails: ["presidio-pii-block", "lakera-guard-block"]
```

Mismo modelo open-weight en primario (OpenRouter) y fallback (Hugging Face), para que el juez se comporte igual si cae el proveedor principal y el fallback siga siendo independiente de verdad (no el mismo proveedor). `fallbacks: {validator: [validator-fallback-hf]}`. Los guardarrailes se vinculan a **los dos** deployments: hoy los fallbacks de evaluador/revisor no llevan Presidio y no se quiere heredar ese hueco.

### 3. Contrato del validador: default-deny y salida estructurada estricta

- Entrada (parte de datos A2A): `{"technologies": [str, ...]}`.
- Salida (parte de datos A2A): `{"valid": bool, "reason": str, "invalid_technologies": [str, ...]}`.
- El prompt pide **default-deny**: veredicto afirmativo solo si todas las entradas son tecnologias de programacion claramente reconocibles; cualquier duda, ambiguedad o desconocido => negativo. `reason` e `invalid_technologies` solo alimentan el mensaje de error (logs / `generation.error_message`), no se muestran como tal en la interfaz.
- Salida **estructurada estricta** via `response_format`/JSON schema (soportado por GLM-5.3-Flash): cualquier respuesta que no cumpla el esquema se trata como fallo de tarea (`error`), nunca como veredicto afirmativo. El parseo tolerante a vallas markdown (patron de `_parse_json` en los demas agentes) se mantiene como red de seguridad, pero el esquema es la garantia.

### 4. Pre-filtro determinista dentro del agente, no en el backend

Antes de llamar al modelo, `agents/validator/app/input.py` rechaza entradas que casan con un patron de dato personal o identificador (email, telefono, IBAN, DNI/NIE). El caso reportado (un DNI) queda asi cubierto de forma determinista, sin depender del recall del modelo ni de Presidio (que **no** detecta DNI: sus entidades son email, telefono, tarjeta, IP, IBAN). Se implementa en el agente (no en el schema del backend) para que el rechazo sea, de forma coherente, un estado `error` de la generacion.

### 5. Guardarrailes de LiteLLM: dos reglas nuevas, solo para el validador

No se puede reutilizar `presidio-pii` ni el global `lakera-guard` tal cual:

- `presidio-pii` usa `MASK`; cambiar su accion afectaria a evaluador/revisor. Se anade `presidio-pii-block` (`guardrail: presidio`, `mode: pre_call`, `presidio_filter_scope: "input"`, `default_on: false`, mismos tipos de entidad, todos `"BLOCK"`).
- `lakera-guard` esta en `default_on: true` con `on_flagged: "monitor"`; pasar el global a `block` afectaria a los 5 agentes (y ya se vio un falso positivo real sobre rutas de repositorio). Se anade `lakera-guard-block` (`guardrail: lakera_v2`, `mode: pre_call`, `default_on: false`, `on_flagged: "block"`), vinculado solo a los deployments del validador.

El global `lakera-guard` (monitor, `default_on: true`) **tambien** correria sobre el validador, y aqui esta el problema encontrado al implementar: la version de LiteLLM del repo usa el guardarrail `lakera_v2`, que **enmascara automaticamente la PII que detecta** (`_mask_pii_in_messages` → `[MASKED <TIPO>]`) en el `pre_call`. Como el global corre antes que los guardarrailes del deployment, sustituia el dato por su marcador y `presidio-pii-block` ya no veia nada que bloquear: el veredicto de "bloquear PII" no se cumplia (se enmascaraba y seguia).

Solucion (verificada en vivo): la virtual key `agent-validator` sale del guardarrail global con `opted_out_global_guardrails: ["lakera-guard"]` en su metadata (`infra/litellm/provision_keys.py`). El opt-out del global solo afecta a guardarrailes con `default_on: true` (`should_run_guardrail`); los del deployment (`presidio-pii-block`, `lakera-guard-block`, ambos `default_on: false`) siguen corriendo, en ese orden, de modo que `presidio-pii-block` bloquea la PII antes de que `lakera-guard-block` la pueda enmascarar. Resultado verificado: tarjeta y email → `400 Blocked entity detected ... by Guardrail: presidio-pii-block`; `React` → `200`. Ademas, esto elimina la doble llamada a Lakera que se habia aceptado como mal menor cuando se creia que el opt-out no estaba disponible.

### 6. El validador corre como primer paso del orquestador, fail-closed

En `_orchestrate`, la llamada al validador precede a `_resolve_commit` y a `_gather_inputs`. Un rechazo (`valid: false`) o un fallo del validador se traducen en `_GenerationFailed` con mensaje claro (p. ej. `"las tecnologias no parecen tecnologias de programacion: <invalid_technologies>"` o el motivo del fallo). Cualquier fallo de transporte/tiempo/guardarrail/parseo del validador se propaga como fallo de la generacion (no hay degradacion): al ser la unica entrada imprescindible antes de web/codigo, no tiene sentido continuar sin ella. Se propaga el mismo `trace_id`.

### 7. Trazabilidad y aprovisionamiento

- Traza: `mask_input=True` en la llamada del validador (el prompt lleva texto del usuario).
- Virtual key `agent-validator` restringida a `["validator", "validator-fallback-hf"]`, con el mismo techo de gasto y rpm que las demas (`infra/litellm/provision_keys.py`), env `AGENT_VALIDATOR_LITELLM_KEY`.

### 8. Estructura del agente

`agents/validator/` reusa el patron de `agents/evaluator/` pieza a pieza: `config.py` (host/puerto 8015/URL, `agent_service_token`, key virtual, Langfuse), `llm.py` (ChatOpenAI contra LiteLLM, modelo logico fijo `validator`, timeout explicito), `input.py`, `service.py`, `agent_card.py`, `executor.py`, `main.py` (ServiceAuth + SlowAPI), `rate_limit.py`, `service_auth.py`, `tracing.py`, `run.py`, `Dockerfile`, `requirements.txt`.

## Risks / Trade-offs

- **[Presidio `BLOCK` puede dar falsos positivos]** Un texto con pinta de dato personal (p. ej. un telefono) rechazaria una generacion legitima. -> Aceptado: el usuario pide maxima restriccion; los tipos de entidad son de riesgo real y poco frecuentes en un campo de tecnologias.
- **[Los guardarrailes en `block` anaden una llamada a Lakera (doble con el global) y pueden producir falsos positivos]** -> Aceptado explicitamente: bloquear es requisito en el validador; el campo es corto y el volumen es una llamada por generacion.
- **[Presidio no detecta DNI/NIE]** -> Mitigado por el pre-filtro determinista en el agente.
- **[Un fallback con distinto comportamiento al primario]** -> Mitigado usando el mismo modelo open-weight en ambos proveedores.
- **[Un veredicto estructurado del modelo puede no cumplir el esquema]** -> Fail-closed: se da la tarea por fallida; con `response_format` estricto el riesgo es bajo.
- **[El validador anade latencia a cada generacion]** -> Modelo de clase "flash" y una sola llamada corta; el pre-filtro y la revalidacion evitan llamar al modelo en los rechazos obvios.

## Verification notes (a confirmar en implementacion)

- Que la accion `BLOCK` del guardarrail Presidio y `on_flagged: "block"` de Lakera `lakera_v2` estan soportadas por la version de LiteLLM del repo.
- Que un bloqueo de guardarrail se traduce en un error que el agente y el orquestador convierten en estado `error` de la generacion (fail-closed).
- Que los guardarrailes vinculados al deployment se aplican tambien cuando LiteLLM salta al modelo de fallback.
- Que `response_format`/JSON schema se propaga correctamente a traves del proxy para `validator` y su fallback.
