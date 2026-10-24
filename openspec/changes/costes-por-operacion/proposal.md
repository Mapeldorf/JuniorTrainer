# Proposal

## Why

La sección 3.8 del capstone («Costes anticipados por nivel de uso») sigue pendiente y es una de las que pide la rúbrica. Hoy no hay ninguna cifra: no se sabe cuánto cuesta una generación, una evaluación o una validación, ni qué pasaría con el tope de 5 USD por clave de LiteLLM si el uso creciera. La suite de evaluación (`evals/`) ya ejecuta los seis agentes contra los modelos reales, así que medir es ahora barato.

Se ha comprobado que no hace falta construir una contabilidad nueva: cada respuesta de los agentes trae sus tokens (`usage_metadata`), con los de razonamiento aparte, y OpenRouter devuelve además el coste facturado de la llamada en `response_metadata.token_usage.cost`. Langfuse, en cambio, no devuelve ni tokens ni coste por su API (ya anotado en §3.8).

## What Changes

- El arnés de evaluación **captura tokens y coste por llamada** (entrada, salida, razonamiento, coste facturado si el proveedor lo informa) y los agrega en el informe por agente y por caso.
- Una **tabla de precios versionada** (`evals/prices.json`, con fecha y fuente) y un script que la refresca desde la API pública de modelos de OpenRouter.
- Un **calculador de costes** (`evals/costs.py`) que, a partir de un informe real, los precios y unos supuestos de uso editables, produce:
  - coste por operación (validar una tecnología, evaluar una respuesta, generar sin repositorio, generar con repositorio), desglosado por etapa;
  - coste de una **campaña de incorporación** en tres niveles de tamaño (piloto, equipo, organización): el uso real no es estacionario, así que se modela por fases —generación inicial de ejercicios por el tech lead, resolución por los juniors durante 1-2 semanas y régimen posterior a demanda— y se compara el mes más cargado con el presupuesto de 5 USD/30 días por clave;
  - efecto de la memoria de los agentes web y de código (con y sin acierto);
  - comparativa con un modelo de referencia: Opus 5.5 para web, código y ejercicios, y Haiku 5.5 para validador, evaluador y revisor;
  - coste del no-sistema (minutos de tech lead por ejercicio × coste por hora).
- La sección §3.8 del capstone, redactada con los resultados.

### Supuestos (el usuario no los tiene claros; quedan como parámetros a validar)

- **Forma del uso (indicada por el usuario).** Un tech lead genera del orden de 500 ejercicios durante el primer mes y después solo a demanda (un requisito nuevo de aprendizaje); los juniors dedican 1-2 semanas a resolverlos. Se espera por tanto que el coste se concentre en la **evaluación y la revisión** (muchas llamadas pequeñas) más que en la generación, aunque la medición lo dirá: no se da por supuesto. Un modelo mensual de régimen estacionario no representa ese patrón.
- **Supuestos de uso** (ejercicios guardados a generar, ejercicios por generación, tasa de candidatos que el tech lead guarda, juniors por nivel, ejercicios resueltos por junior en la campaña, porcentaje con repositorio, tasa de acierto de memoria, generaciones a demanda por trimestre): se proponen valores por defecto, marcados como hipótesis, en un fichero editable. Los números del capstone se derivan de ese fichero, no están escritos en el texto.
- **Coste del no-sistema**: sin minutos por ejercicio ni coste por hora, se presenta la fórmula y un ejemplo con valores marcados como hipótesis. El usuario debe sustituirlos por los suyos.
- **Los costes medidos son los de lo que respondió**: el modelo primario o, si falló, el de respaldo. El alias que ve el cliente no distingue cuál fue.
- **Los precios son los de OpenRouter en la fecha de consulta**; el respaldo en Hugging Face no se precia (no hay API pública equivalente).

### Fuera de alcance

Facturación real, alertas de gasto, el coste de Tavily y de la API de GitHub (el usuario indica que no le suponen coste), optimización de prompts para gastar menos, el caché de prompts del proveedor (`input_cache_read`) y cualquier cambio en el código de los agentes.

## Capabilities

### New Capabilities

Ninguna.

### Modified Capabilities

- `agent-evaluation`: añade la captura de tokens y coste, la tabla de precios y el cálculo de costes por operación, nivel de uso, caché y modelo de referencia.

## Impact

- `evals/` (captura en el envoltorio del modelo, informe, `prices.json`, `costs.py`, tests y README); sin cambios en `agents/`, backend, frontend ni CI salvo ejecutar los nuevos tests.
- `capstone/juniortrainer-capstone.md` §3.8 (y referencias cruzadas en §3.4, §5.7 y el glosario).
- Una consulta de lectura a la API pública de modelos de OpenRouter al refrescar precios.
- La ejecución real que alimenta las cifras consume presupuesto de las claves de LiteLLM.
