# Proposal

## Why

La medición de costes (§3.8) reveló que, aunque §3.3 descartó los modelos de
razonamiento, los modelos elegidos **razonan igualmente**: entre el 72 % y el 81 %
de la salida del revisor, el validador y el agente de ejercicios son tokens de
razonamiento, que el proveedor factura como salida. No es un fallo, es una
contradicción medida entre el diseño y la realidad, y hoy no hay forma de
cuantificar qué pasaría si se recortara ese razonamiento: ni cuánto coste se
ahorraría, ni cuánta calidad se perdería (si es que se pierde).

La suite de evaluación ya mide ambas cosas por separado —coste por llamada y
tokens de razonamiento (`evals.costs`, §3.8) y calidad con métricas deterministas
(§5.5)— pero siempre con el razonamiento que el modelo decide por su cuenta. Falta
una palanca para fijar el esfuerzo de razonamiento y volver a medir, de modo que el
experimento sea coste **frente a** calidad al variar ese único factor.

## What Changes

- Un ajuste nuevo del arnés, **solo en modo real**, que fija el esfuerzo de
  razonamiento del modelo: `--reasoning effort=<nivel>`, `--reasoning max-tokens=<N>`
  o `--reasoning off`. Se traduce al objeto `reasoning` del parámetro unificado de
  OpenRouter y se **inyecta en `extra_body`** de cada llamada al modelo, fusionándolo
  con lo que el agente ya pone ahí (metadatos de traza, `response_format`), **sin
  tocar el código de los agentes**: el punto de inyección es el envoltorio
  `RecordingModel` que la suite ya interpone.
- El informe registra el ajuste usado (o "no fijado" en el baseline), para poder
  atribuir y comparar dos ejecuciones.
- Un ajuste inválido aborta la ejecución antes de llamar al modelo. En modo simulado
  el ajuste se rechaza, porque el doble guionizado no llama a ningún proveedor y el
  resultado no significaría nada.
- **Alcance de la palanca:** se usa el *presupuesto* de razonamiento (`effort` /
  `max_tokens`) o su desactivación (`enabled: false`), que son los que reducen los
  tokens de razonamiento facturados. **No** se usa `exclude`, que solo oculta el
  razonamiento en la respuesta sin reducir lo que el modelo genera ni lo que cuesta.

## Capabilities

### Modified Capabilities
- `agent-evaluation`: añade un requisito de control del esfuerzo de razonamiento en
  modo real (inyección en la llamada, registro en el informe, rechazo en simulado).

## Impact

- `evals/model_wrapper.py`: `parse_reasoning()` nuevo (spec → objeto `reasoning` o
  error) y `RecordingModel` acepta un `reasoning` opcional que fusiona en `extra_body`.
- `evals/agent_runner.py`: flag `--reasoning`; se aplica solo en modo real y se
  registra en el payload.
- `evals/run.py`: flag `--reasoning` que se propaga al subproceso; rechaza el ajuste
  en modo simulado.
- `evals/report.py`: `build_report` registra el ajuste de razonamiento y el resumen
  lo muestra en la cabecera.
- Documentación: `evals/README.md` explica el experimento (correr baseline y cada
  nivel, comparar coste y calidad).
- **Fuera de alcance:** ejecutar la medición (necesita el stack real y gasta
  presupuesto) y reconciliar §3.3/§3.8 con los resultados; eso se hace después, con
  los informes en la mano. La comparación entre informes se hace a ojo o con
  `evals.costs`; no se añade un comparador dedicado en este change.
