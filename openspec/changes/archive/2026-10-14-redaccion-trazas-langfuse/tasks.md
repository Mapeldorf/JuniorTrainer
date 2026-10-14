# Tasks

## 1. Extender `litellm_trace_metadata` en los 5 agentes

- [x] 1.1 En `agents/code/app/tracing.py`, cambiar `litellm_trace_metadata` para aceptar `mask_input: bool = False, mask_output: bool = False` y construir el `metadata` incondicionalmente a partir de `trace_id`/los flags (ver design.md), devolviendo `{}` solo si no hay nada que decir. Verificar con un test manual: `litellm_trace_metadata(None, mask_input=True) == {"metadata": {"mask_input": True}}`

  Verificado en proceso: los 4 casos (sin trace_id con flag, con trace_id sin flags, con trace_id y ambos flags, sin nada) devuelven exactamente lo esperado.
- [x] 1.2 Repetir 1.1 en `agents/evaluator/app/tracing.py`
- [x] 1.3 Repetir 1.1 en `agents/exercises/app/tracing.py`
- [x] 1.4 Repetir 1.1 en `agents/reviewer/app/tracing.py`
- [x] 1.5 Repetir 1.1 en `agents/web/app/tracing.py`

  Verificado por import en los 4: `litellm_trace_metadata(None, mask_input=True)` y `litellm_trace_metadata('abc')` devuelven el resultado esperado en cada uno.

## 2. Aplicar los flags en cada call-site

- [x] 2.1 En `agents/code/app/service.py:166` (`_pick_files`), dejar `litellm_trace_metadata(trace_id)` sin flags (no interpola contenido de ficheros, ver design.md tabla)
- [x] 2.2 En `agents/code/app/service.py:201` (`_analyze`), cambiar a `litellm_trace_metadata(trace_id, mask_input=True, mask_output=True)`
- [x] 2.3 En `agents/evaluator/app/service.py:143`, cambiar a `litellm_trace_metadata(trace_id, mask_input=True)`
- [x] 2.4 En `agents/reviewer/app/service.py:131`, cambiar a `litellm_trace_metadata(trace_id, mask_input=True)`
- [x] 2.5 En `agents/web/app/service.py:108` (`_summarize`), cambiar a `litellm_trace_metadata(trace_id, mask_input=True)`

  Tambien se actualizo un comentario adyacente que decia "extra_body={} (sin trace_id) no cambia el comportamiento" -- ya no es exacto con mask_input activo (el objetivo de la tarea 1 es precisamente que si cambie, aunque no haya trace_id).
- [x] 2.6 En `agents/exercises/app/service.py:279` (`_invoke_and_parse`, usada por `_draft_candidates` tanto en el intento inicial como en el reintento), cambiar a `litellm_trace_metadata(trace_id, mask_input=True, mask_output=True)`

## 3. Verificacion en vivo contra Langfuse Cloud real

- [x] 3.1 Con el stack levantado, ejecutar una llamada real a `agents/code::analyze_repo` contra un repositorio real (cache-miss, para forzar las dos llamadas al modelo) con un `trace_id` nuevo, y comprobar en Langfuse Cloud que la traza de `_analyze` muestra `input`/`output` como `"redacted-by-litellm"` (o equivalente), mientras que la de `_pick_files` sigue mostrando el listado de ficheros en claro, y que ambas conservan coste/latencia/modelo visibles

  Verificado consultando la API real de Langfuse Cloud (`client.api.observations.get_many(trace_id=..., fields='io,core')`) tras una llamada real contra `Mapeldorf/autobot-frontend`: la observacion `litellm-acompletion` de `_analyze` tiene `input`/`output` literalmente `"redacted-by-litellm"`; la de `_pick_files` muestra el prompt y la respuesta en claro (listado de ficheros elegidos); el span propio `agente-code` tambien en claro (metadata inocua, nunca debia enmascararse).
- [x] 3.2 Ejecutar una evaluacion real (`evaluate_answer`, evaluador + revisor) y comprobar en Langfuse Cloud que el `input` de ambas llamadas aparece redactado, mientras que el `output` (verdict/justification) sigue visible en claro

  Verificado consultando la API real de Langfuse Cloud: las dos observaciones `litellm-acompletion` (evaluador y revisor) tienen `input="redacted-by-litellm"`; el `output` de ambas sigue en claro (verdict/justification legibles).
- [x] 3.3 Ejecutar una investigacion web real (`research`, agente web) y comprobar en Langfuse Cloud que el `input` de la llamada de resumen aparece redactado, mientras que el `output` (el resumen generado) sigue visible en claro

  Verificado consultando la API real de Langfuse Cloud: `input="redacted-by-litellm"` en la llamada de resumen; `output` (el resumen Markdown generado) en claro.
- [x] 3.4 Ejecutar una generacion de ejercicios real con repositorio (`agents/exercises`, con `code_result` no vacio) y comprobar en Langfuse Cloud que tanto `input` como `output` de esa llamada aparecen redactados

  Verificado consultando la API real de Langfuse Cloud: con `code_result` incluyendo fragmentos de codigo, `input` y `output` de la llamada LLM aparecen ambos como `"redacted-by-litellm"`; el span propio del agente (metadata inocua) sigue en claro.
- [x] 3.5 Ejecutar cualquiera de las llamadas redactadas SIN `trace_id` (agente en solitario) y comprobar que la traza suelta que crea LiteLLM tambien aparece redactada -- confirma el hallazgo de la tarea 1 (el enmascarado ya no depende de que exista `trace_id`)

  Verificado llamando a `agents/evaluator::evaluate_answer` directamente con `trace_id=None`: LiteLLM crea su propia traza suelta, y su `input` sigue apareciendo como `"redacted-by-litellm"` en Langfuse Cloud -- confirma que el fix del hallazgo de la tarea 1 funciona de verdad, no solo en el analisis del dict en Python.
