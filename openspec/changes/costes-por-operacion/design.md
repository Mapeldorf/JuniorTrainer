# Design

## Context

Ver `proposal.md`. Lo comprobado antes de decidir:

- **Los tokens ya llegan al arnés.** Una llamada real al evaluador a través de LiteLLM devuelve en la respuesta de `langchain-openai` `usage_metadata` (`input_tokens`, `output_tokens`, y `output_token_details.reasoning`) y `response_metadata.token_usage`, que incluye `cost` (coste facturado por OpenRouter, p. ej. 1,89·10⁻⁵ USD para una llamada de 38 tokens de entrada y 13 de salida) y `cost_details` con el desglose de entrada y salida. `RecordingModel` ya ve cada respuesta.
- **El alias no identifica al modelo.** `response_metadata.model_name` devuelve el alias lógico (`evaluator`), no el modelo que contestó: no se distingue primario de respaldo.
- **Hay tokens de razonamiento** aunque el diseño (§3.3) descartó los modelos de razonamiento: una petición trivial dio 10 de 13 tokens de salida como razonamiento. Cuenta como salida y se cobra.
- **Precios públicos disponibles** en `GET https://openrouter.ai/api/v1/models` (sin credenciales): DeepSeek V4.1 Flash 0,02 / 1,00 USD por millón (entrada / salida), GLM-5.3 FlashX 0,37 / 1,25, GLM-5.3 Flash 0,15 / 0,50, Claude Opus 5.5 4,00 / 20,00 y Claude Haiku 5.5 0,10 / 0,50. El respaldo en Hugging Face no tiene API pública equivalente.
- Los informes de la suite (`evals/results/`) hoy no guardan tokens ni coste, así que ninguno sirve como entrada: hay que repetir la ejecución real tras añadir la captura.

## Goals / Non-Goals

**Goals:**
- Cifras de coste por operación, nivel de uso, memoria y modelo de referencia que se recalculan al cambiar precios o supuestos.
- Separar con claridad lo **medido** (tokens y coste de llamadas reales) de lo **supuesto** (uso mensual, minutos por ejercicio).

**Non-Goals:**
- Contabilidad de facturación o alertas de gasto.
- Reducir el coste (optimizar prompts, ajustar modelos).
- Preciar el respaldo en Hugging Face.
- Modificar los agentes.

## Decisions

**1. Tokens de `usage_metadata`; coste facturado de `response_metadata.token_usage.cost` cuando exista.** El coste se **mide** cuando el proveedor lo informa y se **calcula** con la tabla de precios cuando no. Ambos deben coincidir en los modelos de OpenRouter: es una comprobación cruzada que se incluye como test del calculador y como métrica del informe. *Alternativas descartadas:* el endpoint de gasto de LiteLLM (`/spend/logs`), que depende de que su mapa de precios conozca los modelos de OpenRouter, y Langfuse, que no devuelve tokens (ya anotado en §3.8).

**2. La captura vive en `RecordingModel` y no toca los agentes.** Se suma, por caso, lo de todas sus llamadas. Los campos ausentes quedan como `null` (no informado), nunca como cero: es la misma regla que se aplica al resto de métricas sin datos.

**3. Precios en `evals/prices.json`, con fecha y fuente, refrescables con `evals/update_prices.py`.** El script solo lee la lista pública de modelos de OpenRouter y escribe solo los modelos que ya figuran en la tabla, más los de referencia. Un modelo ausente hace fallar el cálculo; nunca se asume un precio. *Alternativa descartada:* precios en el texto del capstone, que se quedan viejos sin que nadie lo note.

**4. El coste de una operación es la suma de los costes medios de sus agentes.** La suite ejecuta cada agente por separado, así que la composición es:
- validar una tecnología → validador;
- evaluar una respuesta → evaluador + revisor;
- generar sin repositorio → validador + web + ejercicios;
- generar con repositorio → validador + web + código + ejercicios.

Es una aproximación: en producción la entrada de un agente depende de la salida del anterior (el prompt del agente de ejercicios lleva el resumen del agente web), mientras que en la suite lleva un resumen fijo del dataset. Se declara en el informe. El coste de ejercicios depende además del número de candidatos pedidos (1 a 5); el informe lo presenta para el valor típico del dataset y señala la sensibilidad.

**5. La memoria es una resta.** Con acierto no se llama a web ni a código: el coste es el de la operación sin esos dos agentes. En los escenarios se pondera por una tasa de acierto configurable.

**6. El uso se modela como una campaña por fases, con el equipo como unidad.** Un equipo es un tech lead y 2 juniors. El patrón descrito es una ráfaga: el tech lead genera del orden de 500 ejercicios el primer mes, los juniors los resuelven en 2 semanas, cada año se incorporan 2 juniors más por equipo y después solo hay generación a demanda. Los niveles de uso se expresan en equipos (1, 5 y 30, que son los tech leads de los niveles piloto, equipo y organización del capstone). Tres fases:
- *Generación inicial:* generaciones por tech lead = ejercicios guardados a generar ÷ (ejercicios por generación × tasa de guardado). Con 500, 3 candidatos y un 90 % de guardado son unas 185 generaciones, no 167: la tasa de guardado importa porque la generación produce **candidatos** y el tech lead solo guarda parte. Cuantos más candidatos por generación (hasta 5), menos generaciones.
- *Resolución:* evaluaciones = equipos × juniors por equipo × ejercicios resueltos por junior. Con 2 juniors que resuelven los 500, son 1.000 por equipo en 2 semanas (si los 500 se reparten entre los dos, 500). Cada evaluación cuesta evaluador + revisor. Una respuesta no se modifica una vez dada (§2.5), así que no hay reintentos del alumno que multipliquen el coste.
- *Régimen:* por equipo y año, 2 juniors que se incorporan × el catálogo existente, más los ejercicios nuevos a demanda (generación y su resolución).

La memoria pesa mucho en este patrón: ~185 generaciones del mismo tech lead sobre un mismo repositorio y unas pocas tecnologías repiten la clave de memoria de web (tecnologías normalizadas) y de código (repositorio, commit y tecnologías), así que casi todas serían aciertos salvo la primera de cada combinación. La tasa de acierto es un supuesto con valor por defecto alto y se comprueba con una sensibilidad.

El informe da el coste de cada fase, el reparto entre generación y evaluación (se comprueba, no se asume) y el pico de gasto de cualquier ventana de 30 días, que es contra lo que se compara el presupuesto de 5 USD de cada clave: una campaña de 2 semanas concentra el gasto y puede agotar la clave del evaluador aunque el total sea pequeño.

Los supuestos viven en `evals/cost_assumptions.json`: equipos por nivel, juniors por equipo, parámetros de las tres fases, incorporaciones anuales, tasa de memoria, proporción con repositorio, precio por búsqueda, minutos por ejercicio y coste por hora, todos con un campo `nota` que los marca como hipótesis.

**6b. Tavily y GitHub entran en el cálculo.** Cada generación sin acierto de memoria hace hasta 5 búsquedas de Tavily (el presupuesto del agente web) y hasta 10 lecturas de GitHub (el del agente de código). El arnés ya cuenta ambas por caso (`probe.search_calls` y `probe.reads`). Las búsquedas se precian con un precio por búsqueda en `prices.json`, que se desconoce (depende del plan de Tavily) y queda como hipótesis; si falta, el coste de generar se marca como incompleto en lugar de omitirse en silencio. Las lecturas de GitHub se cuentan sin precio: la API de una GitHub App no se factura por llamada, solo tiene límite de tasa (a confirmar).

**7. Modelo de referencia por rol, definido en la tabla de precios.** Opus 5.5 para web, código y ejercicios (el trabajo pesado) y Haiku 5.5 para validador, evaluador y revisor. Se reutilizan los tokens medidos y solo cambian los precios. Es una cota inferior de lo que costaría de verdad: otro modelo gastaría otros tokens (más o menos razonamiento, otra verbosidad). El informe lo dice.

**8. Informe determinista a partir de ficheros.** `python -m evals.costs <informe-real.json>` lee el informe real, `prices.json` y `cost_assumptions.json` y escribe un JSON y las tablas en Markdown. No llama a ningún modelo ni a la red. Rechaza informes del modo simulado.

## Risks / Trade-offs

- [Pocas muestras: los tokens medios varían con el contenido] → Cada cifra indica cuántos casos la respalda; se recomienda repetir la ejecución real y se informa el rango (mínimo y máximo) además de la media.
- [El coste facturado incluye llamadas que cayeron al respaldo, de otro precio] → Se declara; el alias no permite distinguirlo.
- [Los tokens de razonamiento inflan la salida y no estaban en el diseño de §3.3] → Se informan por separado como hallazgo; no se corrigen aquí.
- [La composición por agente subestima o sobrestima la cadena real] → Se declara en el informe; se puede validar con una generación completa a través del backend (fuera de alcance).
- [Los supuestos de uso no son datos, y el patrón en ráfaga es difícil de predecir] → Siempre se imprimen como hipótesis; las cifras se leen como órdenes de magnitud y se acompañan de un análisis de sensibilidad sobre los dos parámetros que más pesan (ejercicios por alumno y tasa de guardado).
- [Los precios cambian] → Fecha y fuente en la tabla, y refresco con un comando.

## Open Questions

- ¿Qué minutos por ejercicio y coste por hora usa el usuario para el no-sistema? Se resuelve editando `cost_assumptions.json`; no cambia las specs ni las tareas.
