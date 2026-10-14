# Proposal

## Why

Los 5 agentes pasan `extra_body=litellm_trace_metadata(trace_id)` a cada llamada `model.ainvoke(...)`. LiteLLM tiene configurado `success_callback`/`failure_callback: ["langfuse"]` (`infra/litellm/config.yaml`), lo que registra el prompt y la respuesta COMPLETOS de cada llamada en Langfuse Cloud -- un SaaS externo, fuera de la infraestructura del proyecto. Sin ningun control hoy, eso incluye:

- Codigo de repositorios de terceros/privados, tanto en `agents/code` (que lo lee directamente) como en `agents/exercises` (que recibe los mismos fragmentos literales de codigo via `code_result['fragments']`, un paso mas adelante en la orquestacion).
- La respuesta literal de un alumno a un ejercicio, en `agents/evaluator` y `agents/reviewer` -- potencialmente informacion personal si el alumno escribe algo identificable.
- Contenido de busqueda web de terceros, en `agents/web`.

Investigacion (ver conversacion previa): LiteLLM soporta exactamente esto sin tocar nada mas, documentado en docs.litellm.ai/docs/observability/langfuse_integration -- las claves `mask_input`/`mask_output` en el `metadata` que ya se pasa por llamada. Puestas a `true`, Langfuse recibe `"redacted-by-litellm"` en vez del contenido real, SOLO para esa llamada y SOLO lo que se registra (nunca lo que se envia al proveedor del LLM real); el resto de metadata de la traza (coste, latencia, tokens, modelo, exito/fallo) sigue intacta. Se descarta la alternativa global `litellm.turn_off_message_logging=True` porque apagaria la observabilidad de TODAS las llamadas, incluidas las que no manejan ningun dato sensible (p. ej. la eleccion de ficheros en `agents/code`, que solo interpola nombres y tamanos). Tambien se descarta el `mask=` del propio SDK de Langfuse (a nivel de cliente): los spans que cada agente crea con sus propias manos (`record_task()` en cada `tracing.py`) ya solo contienen metadata inocua (tecnologias, verdict, contadores), nunca el contenido sensible -- la fuga real es unicamente via el callback de LiteLLM hacia la llamada al LLM, asi que el mecanismo de LiteLLM es el correcto y suficiente.

## What Changes

- `litellm_trace_metadata(trace_id)` (duplicada en cada `app/tracing.py`, mismo patron que el resto de helpers sin codigo compartido entre agentes) pasa a aceptar `mask_input`/`mask_output` opcionales, anadiendo esas claves al `metadata` que ya construye.
- Se activa `mask_input=True` en toda llamada que interpole codigo de repositorio, respuesta de un alumno, o contenido de busqueda web en el prompt.
- Se activa tambien `mask_output=True` donde la respuesta del modelo puede reproducir ese contenido literal (en vez de solo un resumen/juicio derivado): `agents/code::_analyze` y `agents/exercises::_draft_candidates`/`_invoke_and_parse`.
- Se deja sin enmascarar la salida de `evaluator`/`reviewer` (verdict+justificacion) y de `web` (resumen): es contenido derivado por el modelo, de bajo riesgo, y utile para depurar calidad de evaluaciones/resumenes.
- Hallazgo adicional durante el diseño: `litellm_trace_metadata` devuelve `{}` (sin ninguna clave) cuando no hay `trace_id`, lo que haria que el enmascarado tambien se saltara en una llamada sin `trace_id` (p. ej. un agente ejecutado en solitario sin orquestador). Se corrige para que el enmascarado se aplique con independencia de si hay `trace_id` o no.

## Capabilities

### New Capabilities
- `agent-trace-privacy`: define que datos de un agente nunca se registran en claro en el backend de tracing externo (Langfuse), con independencia de que la traza en si siga existiendo.

### Modified Capabilities
(ninguna: ninguna capacidad existente gobierna hoy el contenido de las trazas de Langfuse)

## Impact

- **Codigo afectado**: `agents/{code,evaluator,exercises,reviewer,web}/app/tracing.py` (`litellm_trace_metadata`), y los call-sites de `model.ainvoke(...)` en cada `app/service.py` que deben pasar los nuevos flags.
- **Sin cambios**: `infra/litellm/config.yaml`, el SDK de Langfuse usado para los spans propios de cada agente (`record_task`), el contrato de entrada/salida de ningun agente.
- **Compatibilidad**: ninguna ruptura -- cambia solo que se registra en un SaaS externo, no el comportamiento observable del sistema para quien lo usa.
