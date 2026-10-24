# Design

## Context

Ver `proposal.md` para la motivación. Estado técnico relevante:

- Los seis agentes llaman al modelo con `model.ainvoke(messages, extra_body={...})`,
  donde `extra_body` lleva los metadatos de traza de Langfuse (`litellm_trace_metadata`)
  y, en el validador, también `response_format` (verificado en
  `agents/*/app/service.py`).
- En modo real, el arnés construye el modelo con el propio `build_*_model()` del
  agente (un `ChatOpenAI(model="<alias>", base_url=..., api_key=...)`) y lo envuelve
  en `RecordingModel` (`evals/model_wrapper.py`), cuyo `ainvoke(self, messages, **kwargs)`
  reenvía la llamada al modelo real. En modo simulado el modelo es `ScriptedModel`,
  que ignora `kwargs` y no contacta con ningún proveedor.
- El informe ya captura, por caso, tokens de entrada/salida/razonamiento y coste
  facturado (`extract_usage`, `_usage_block`). La calidad se mide con métricas
  deterministas contra las etiquetas del dataset (exactitud y κ, validez, adherencia,
  cardinalidad, FP/FN del gate, duplicados). No hace falta capturar nada nuevo.
- Parámetro de razonamiento de OpenRouter: un objeto `reasoning` con `effort`
  (niveles), `max_tokens` (tope) o `enabled`. `exclude: true` solo oculta el
  razonamiento en la respuesta: **no reduce** los tokens generados ni el coste, así
  que no sirve para este experimento.

## Goals / Non-Goals

**Goals:**
- Fijar el esfuerzo de razonamiento en modo real sin tocar el código de los agentes.
- Reutilizar las métricas de coste y calidad que ya existen: el experimento es correr
  la suite en baseline y en cada ajuste y comparar los informes.
- Dejar registrado en el informe el ajuste usado, para atribuir cada medición.

**Non-Goals:**
- No se ejecuta la medición (necesita el stack real y gasta presupuesto).
- No se reconcilia §3.3/§3.8: se hace después, con los números.
- No se añade un comparador de informes; `evals.costs` y las métricas del informe ya
  permiten la comparación.
- No se cambia el comportamiento de producción: la palanca vive solo en el arnés.

## Decisions

- **El ajuste se inyecta en `RecordingModel`, no en los agentes.** Es el único punto
  por el que pasan todas las llamadas reales, y el arnés ya lo controla. `ainvoke`
  copia el `extra_body` entrante, fija en él la clave `reasoning` y reenvía; así no
  pisa los metadatos de traza ni el `response_format` del validador.
- **La clave `reasoning` del ajuste gana sobre la del agente.** Los agentes no ponen
  `reasoning` hoy, pero si alguno lo hiciera, el experimento debe fijar el valor que
  mide, no heredar el del agente.
- **Solo modo real.** En simulado el ajuste no significa nada (no hay proveedor), así
  que se rechaza en `run.py` con un mensaje claro en vez de aceptarlo como un no-op
  silencioso que ensuciaría el informe.
- **La palanca es el presupuesto de razonamiento, no `exclude`.** `off` se traduce a
  `{"enabled": false}`; `effort=<nivel>` a `{"effort": "<nivel>"}` con el nivel entre
  los que documenta OpenRouter (`none`, `minimal`, `low`, `medium`, `high`, `xhigh`,
  `max`); `max-tokens=<N>` a `{"max_tokens": N}` con N entero positivo. Un spec que no
  encaje aborta con error.
- **Qué modelos honran el ajuste es un hecho a medir, no a suponer.** Si un modelo
  tiene el razonamiento obligatorio, OpenRouter puede ignorar el ajuste; eso se ve en
  `GET /api/v1/models` y, sobre todo, en que los tokens de razonamiento del informe
  bajen (o no). El arnés inyecta el ajuste; comprobar su efecto es parte de la
  medición.

## Risks / Trade-offs

- [El ajuste llega al proveedor pero el modelo no lo respeta (razonamiento obligatorio)
  → la medición no mostraría ahorro] → No es un fallo del arnés: el informe seguirá
  mostrando los tokens de razonamiento reales, que es justo la señal de si el ajuste
  tuvo efecto. Se documenta como lo que el experimento debe comprobar.
- [Comparar calidad entre ajustes usa las etiquetas del dataset, que siguen siendo
  provisionales (gap de §5.6/§5.7)] → La comparación es **relativa** entre ajustes con
  las mismas etiquetas, así que es válida para decidir si un ajuste degrada; el valor
  absoluto de calidad es otro trabajo.
