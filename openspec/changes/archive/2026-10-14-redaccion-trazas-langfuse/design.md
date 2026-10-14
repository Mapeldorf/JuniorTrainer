# Design

## Context

`infra/litellm/config.yaml` configura `litellm_settings.success_callback`/`failure_callback: ["langfuse"]`: LiteLLM registra en Langfuse Cloud el prompt y la respuesta completos de toda llamada que pase por el, salvo que se le indique lo contrario por llamada. Los 5 agentes ya pasan `extra_body=litellm_trace_metadata(trace_id)` a cada `model.ainvoke(...)`; esa funcion (duplicada identica en cada `app/tracing.py`, mismo patron sin codigo compartido entre agentes ya usado para `service_auth.py` y las frases anti-injection) hoy es:

```python
def litellm_trace_metadata(trace_id: str | None) -> dict:
    if not trace_id:
        return {}
    return {"metadata": {"existing_trace_id": trace_id}}
```

Investigacion (docs.litellm.ai/docs/observability/langfuse_integration, confirmado via fetch directo de la pagina): las claves `mask_input`/`mask_output` dentro de ese mismo `metadata`, puestas a `true`, hacen que Langfuse reciba `"redacted-by-litellm"` en vez del contenido real para esa llamada -- sin afectar la llamada real al proveedor del LLM, y sin afectar el resto de metadata de la traza (coste, tokens, latencia, modelo, exito/fallo).

Ver proposal.md - Why para el resto de la motivacion y las alternativas descartadas (SDK de Langfuse, `turn_off_message_logging` global).

## Goals / Non-Goals

**Goals:**
- Que el contenido sensible (codigo de repositorio, respuesta de alumno, contenido web) nunca llegue en claro a Langfuse Cloud.
- Conservar el resto de la observabilidad de cada traza (coste, latencia, tokens, modelo, exito/fallo) en las llamadas redactadas.
- Reutilizar el mecanismo nativo de LiteLLM ya probado por el proyecto (el mismo `metadata` que ya usa `existing_trace_id`), sin anadir dependencias nuevas.

**Non-Goals:**
- No se cambia la configuracion de `infra/litellm/config.yaml` (los callbacks de Langfuse siguen activos globalmente; la redaccion es por llamada, no una desactivacion general).
- No se anade un mecanismo de deteccion automatica de que es "sensible" dentro de un texto libre (PII masking, Presidio, etc.); la decision de que llamadas redactar es estatica, por punto de llamada, igual que el resto de decisiones de este proyecto en torno a datos no confiables.
- No se toca el SDK de Langfuse usado para los spans propios de cada agente (`record_task()`): ya no contienen contenido sensible (confirmado revisando los 5 `tracing.py`).

## Decisions

### Mecanismo: `mask_input`/`mask_output` de LiteLLM, no `turn_off_message_logging` ni el `mask=` de Langfuse

Ya razonado en proposal.md. En una frase: es el unico de los tres mecanismos que es (a) por llamada, no global, y (b) actua en el punto real de la fuga (el callback de LiteLLM hacia el LLM), no en los spans propios de los agentes (que ya no necesitan redaccion).

### `litellm_trace_metadata` gana dos parametros opcionales, y cambia su condicion de retorno vacio

```python
def litellm_trace_metadata(
    trace_id: str | None, *, mask_input: bool = False, mask_output: bool = False
) -> dict:
    metadata: dict = {}
    if trace_id:
        metadata["existing_trace_id"] = trace_id
    if mask_input:
        metadata["mask_input"] = True
    if mask_output:
        metadata["mask_output"] = True
    return {"metadata": metadata} if metadata else {}
```

**Hallazgo durante el diseño**: la version actual devuelve `{}` (sin ninguna clave) si no hay `trace_id` -- en una ejecucion sin orquestador (agente en solitario, scripts de verificacion), eso haria que el enmascarado tampoco se aplicara, justo cuando mas conviene no depender de que el llamador se acuerde de pasar un trace_id. La version nueva construye el diccionario incondicionalmente a partir de los flags, y solo lo deja vacio si de verdad no hay nada que decir (ni trace_id, ni flags).

### Que llamada de cada agente lleva que flag

| Agente | Llamada | `mask_input` | `mask_output` | Motivo |
|---|---|---|---|---|
| `code` | `_pick_files` (elige ficheros) | no | no | Solo interpola nombres de fichero y tamanos, nunca contenido |
| `code` | `_analyze` (analiza contenido) | si | si | El prompt lleva el contenido completo de los ficheros; la respuesta (`fragments`) copia codigo literal |
| `evaluator` | `_invoke_and_parse` | si | no | El prompt lleva `student_answer`/`code`; la salida (`verdict`/`justification`) es juicio derivado, util para depurar calidad |
| `reviewer` | `_invoke_and_parse` | si | no | Mismo criterio que evaluator: el prompt lleva `student_answer`/la justificacion del evaluador; la salida es juicio derivado |
| `web` | `_summarize` | si | no | El prompt lleva fragmentos de busqueda de terceros; el resumen generado no es sensible en si |
| `exercises` | `_invoke_and_parse` (usada por `_draft_candidates`, incluido el reintento) | si | si | El prompt puede llevar fragmentos de codigo de repositorio recibidos de `agents/code`; la salida (`code` del candidato) puede adaptar/citar ese mismo codigo |

`code::_pick_files` queda deliberadamente sin redactar: los nombres de fichero de un repositorio privado son informacion de mucho menor sensibilidad que su contenido, y mantenerlos visibles en la traza ayuda a depurar por que el modelo elige unos ficheros u otros sin exponer nada del codigo en si. Si en el futuro se considera que los propios nombres de fichero son sensibles (p. ej. revelan la estructura interna de un producto no publico), esto se revisaria aparte.

## Risks / Trade-offs

- **[Trade-off] Perdida de observabilidad detallada en las llamadas redactadas.** No se podra ver en Langfuse el prompt/respuesta exacto para depurar por que un analisis de codigo o una evaluacion salio mal. *Aceptado*: es el objetivo explicito del cambio -- la alternativa (no redactar) expone datos de terceros/personales en un SaaS externo de forma permanente. El resto de la traza (coste, latencia, tokens, si fallo) sigue disponible para detectar que algo fue mal, aunque no el detalle.
- **[Riesgo] Confiar en que LiteLLM aplique correctamente el enmascarado antes de enviar nada a Langfuse.** Es un mecanismo de un proveedor externo (LiteLLM), no verificable por inspeccion de codigo propio. *Mitigacion*: verificar en vivo (tareas de este change) que una llamada marcada con `mask_input`/`mask_output` aparece de verdad como `"redacted-by-litellm"` en Langfuse Cloud, no solo confiar en la documentacion.
- **[Riesgo] La tabla de que redactar es una decision estatica por punto de llamada.** Si se anade una llamada nueva a un agente en el futuro que interpole contenido sensible, hay que acordarse de anadirle los flags -- no hay ninguna comprobacion automatica que lo fuerce. *Mitigacion*: documentado explicitamente en este design.md y en el comentario de cada `tracing.py`, mismo nivel de confianza que el resto de mitigaciones manuales ya existentes en el proyecto (p. ej. los delimitadores anti-injection).
