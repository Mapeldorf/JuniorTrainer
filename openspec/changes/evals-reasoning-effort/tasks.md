# Tasks

## 1. Traduccion del ajuste y punto de inyeccion

- [x] 1.1 En `evals/model_wrapper.py`, añadir `parse_reasoning(spec)` que convierta `None`/vacio en `None` (baseline), `"off"` en `{"enabled": False}`, `"effort=<nivel>"` en `{"effort": nivel}` (niveles: none, minimal, low, medium, high, xhigh, max), `"max-tokens=<N>"`/`"max_tokens=<N>"` en `{"max_tokens": N}` con N entero > 0, y levante `ValueError` con un mensaje claro para cualquier otro caso.
- [x] 1.2 En `RecordingModel`, aceptar un parametro opcional `reasoning` (dict o None, por defecto None). Si no es None, en `ainvoke` copiar el `extra_body` entrante, fijar en el la clave `reasoning` y reenviar, sin perder las demas claves (metadatos de traza, `response_format`). Con `reasoning=None` el comportamiento no cambia.

## 2. Flag en el arnes

- [x] 2.1 En `evals/agent_runner.py`, añadir `--reasoning` (cadena, por defecto vacia). Parsear con `parse_reasoning`; si falla, `_fatal`. Aplicar el ajuste solo en modo real (pasarlo a `_Session`/`RecordingModel`); en simulado no se aplica. Incluir el spec en el payload `EVALS_JSON` (`"reasoning": <spec o null>`).
- [x] 2.2 En `evals/run.py`, añadir `--reasoning` y propagarlo al subproceso de cada agente. Rechazar (`return 2`) si se indica un ajuste fuera del modo real, con un mensaje claro. Pasar el ajuste a `build_report`.
- [x] 2.3 En `evals/report.py`, `build_report` acepta `reasoning=None` y lo incluye en el informe; `render_summary` lo muestra en la cabecera cuando esta fijado. Con `reasoning=None` el informe y el resumen no cambian de forma observable (clave presente a `null`).

## 3. Test sin red

- [x] 3.1 En `evals/test_model_wrapper.py`, añadir tests de `parse_reasoning` (baseline, off, effort valido/invalido, max-tokens valido/invalido/no numerico) y de que `RecordingModel` con `reasoning` fusiona la clave en `extra_body` sin pisar las demas y que con `reasoning=None` no la añade. Usar un modelo interno de doble que registre los `kwargs` recibidos.
- [x] 3.2 Ejecutar `python -m unittest evals.test_model_wrapper evals.test_report` y verificar que pasa. Ejecutar `python -m evals.run` (modo simulado) y verificar que la suite sigue verde y que `--reasoning low` en simulado se rechaza.

## 4. Documentacion

- [x] 4.1 En `evals/README.md`, documentar el experimento: correr el baseline y cada ajuste en modo real sobre revisor, validador y ejercicios (evaluador como control), y comparar el coste (`evals.costs`) y las metricas de calidad entre informes. Dejar dicho que el efecto real del ajuste (que los tokens de razonamiento bajen) depende de que el modelo lo honre, y que eso es parte de la medicion.
