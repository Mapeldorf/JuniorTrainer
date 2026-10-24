# Tasks

## 1. Captura de tokens y coste

- [ ] 1.1 Ampliar `RecordingModel` (`evals/model_wrapper.py`) para sumar por caso los tokens de entrada, salida y razonamiento y el coste facturado, dejando `null` lo no informado; verificar con tests de unidad (una llamada, varias, sin coste informado) con `python -m unittest evals.test_model_wrapper`
- [ ] 1.2 Propagar tokens y coste al registro de cada caso en `evals/agent_runner.py` (solo modo real; `null` en simulado); verificar ejecutando el modo simulado (`python -m evals.run`) sin cambios en las métricas existentes ni en el código de salida
- [ ] 1.3 Agregar tokens, coste y, para web y código, búsquedas y lecturas por agente en `evals/report.py` y en el resumen, con los casos que respaldan cada cifra; verificar con tests de `report` con valores calculados a mano

## 2. Precios

- [ ] 2.1 Crear `evals/prices.json` (modelos de producción y de referencia, con precio de entrada y salida por millón, fecha y fuente, y el precio por búsqueda de Tavily como hipótesis) y `evals/update_prices.py` que lo refresca desde la lista pública de modelos de OpenRouter sin credenciales; verificar con tests del parseo sobre una respuesta de ejemplo y ejecutando el script contra la API real
- [ ] 2.2 Rechazar un modelo ausente de la tabla en lugar de suponer un precio; verificar con un test

## 3. Calculador de costes

- [ ] 3.1 Crear `evals/cost_assumptions.json` con los niveles de uso (en equipos de un tech lead y 2 juniors), los parámetros de las tres fases de la campaña (500 ejercicios guardados a generar, ejercicios por generación, tasa de guardado del 90 %, ejercicios por junior, incorporaciones anuales, generación a demanda), tasa de memoria, proporción con repositorio, minutos por ejercicio y coste por hora, cada uno con su nota de hipótesis; verificar que se carga y que un valor ausente se detecta
- [ ] 3.2 Crear `evals/costs.py`: coste medio por agente, composición en las cuatro operaciones con desglose por etapa e incluyendo las búsquedas (o marcando el coste de generar como incompleto si falta su precio); verificar con tests de valores calculados a mano
- [ ] 3.3 Añadir los escenarios por fases (con el reparto entre generación y evaluación y la sensibilidad a ejercicios por alumno y tasa de guardado), la comparación del pico de 30 días con el presupuesto de cada clave, el efecto de la memoria, la comparativa con el modelo de referencia por rol y el coste del no-sistema; verificar con tests a mano, incluidos el caso de presupuesto superado y el cálculo de generaciones a partir de ejercicios guardados
- [ ] 3.4 Salida determinista (JSON y tablas en Markdown) con el número de casos que respalda cada cifra, rechazo de informes simulados y comprobación cruzada entre coste medido y coste calculado; verificar con un test que ejecuta el cálculo dos veces y compara

## 4. Medición y documentación

- [ ] 4.1 Ejecutar el modo real sobre los seis agentes con la captura activa (a cargo del usuario, con el stack levantado) y generar el informe de costes con `python -m evals.costs`; verificar que no hay agentes «sin datos» y que el coste medido coincide con el calculado
- [ ] 4.2 Redactar §3.8 del capstone con las tablas generadas, los supuestos y los límites, y actualizar las referencias de §3.4, §5.7 y el glosario; verificar que no queda «Sección pendiente» en §3.8 y que cada cifra del texto coincide con el informe
- [ ] 4.3 Documentar en `evals/README.md` cómo medir y calcular costes; verificar que los comandos documentados se ejecutan tal cual
