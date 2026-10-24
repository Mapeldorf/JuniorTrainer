# Tasks

## 1. Captura de tokens y coste

- [x] 1.1 Ampliar `RecordingModel` (`evals/model_wrapper.py`) para sumar por caso los tokens de entrada, salida y razonamiento y el coste facturado, dejando `null` lo no informado; verificar con tests de unidad (una llamada, varias, sin coste informado) con `python -m unittest evals.test_model_wrapper`
- [x] 1.2 Propagar tokens y coste al registro de cada caso en `evals/agent_runner.py` (solo modo real; `null` en simulado); verificar ejecutando el modo simulado (`python -m evals.run`) sin cambios en las métricas existentes ni en el código de salida
- [x] 1.3 Agregar tokens, coste y, para web y código, búsquedas y lecturas por agente en `evals/report.py` y en el resumen, con los casos que respaldan cada cifra; verificar con tests de `report` con valores calculados a mano

## 2. Precios

- [x] 2.1 Crear `evals/prices.json` (modelos de producción y de referencia, con precio de entrada y salida por millón, fecha y fuente, y los planes de Tavily —Researcher, Project y pago por uso— con cuota, créditos incluidos, precio del crédito adicional y créditos por búsqueda) y `evals/update_prices.py` que lo refresca desde la lista pública de modelos de OpenRouter sin credenciales; verificar con tests del parseo sobre una respuesta de ejemplo y ejecutando el script contra la API real
- [x] 2.2 Rechazar un modelo ausente de la tabla en lugar de suponer un precio; verificar con un test

## 3. Calculador de costes

- [x] 3.1 Crear `evals/cost_assumptions.json` con los niveles de uso (en equipos de un tech lead y 2 juniors), los parámetros de las tres fases de la campaña (500 ejercicios guardados a generar, 5 candidatos por generación, tasa de guardado del 90 %, 500 ejercicios resueltos por junior, incorporaciones anuales, generación a demanda), repositorios y tecnologías por proyecto (máx. 5 y 15), plan de Tavily, proporción con repositorio y plan de Tavily, cada uno con su nota de hipótesis; verificar que se carga y que un valor ausente se detecta
- [x] 3.2 Crear `evals/costs.py`: coste medio por agente, composición en las cuatro operaciones con desglose por etapa e incluyendo las búsquedas con el precio marginal del crédito (o marcando el coste de generar como incompleto si falta el plan); verificar con tests de valores calculados a mano
- [x] 3.3 Añadir los escenarios por fases (con el reparto entre generación y evaluación y la sensibilidad a ejercicios por alumno y tasa de guardado), la comparación del pico de 30 días con el presupuesto de cada clave, el efecto de la memoria con los fallos acotados por repositorios × tecnologías, el coste de Tavily del plan (cuota por los meses con uso más el exceso de créditos),, los costes unitarios (por ejercicio guardado, por evaluación y por junior formado) y la comparativa con el modelo de referencia por rol; verificar con tests a mano, incluidos el caso de presupuesto superado y el cálculo de generaciones a partir de ejercicios guardados
- [x] 3.4 Salida determinista (JSON y tablas en Markdown) con el número de casos que respalda cada cifra, rechazo de informes simulados y comprobación cruzada entre coste medido y coste calculado; verificar con un test que ejecuta el cálculo dos veces y compara

## 3b. Modelo de respaldo

- [x] 5.1 Añadir a `evals/prices.json` el respaldo de cada rol y sus precios por proveedor, y extender `evals/prices.py` para refrescarlos desde la lista pública de Hugging Face; verificar con tests del parseo y ejecutando el refresco contra la API real
- [x] 5.2 Calcular en `evals/costs.py` el coste de las operaciones y de la campaña con el respaldo (rango por proveedor) y la sensibilidad a la fracción de llamadas (0 %, 5 %, 20 %, 100 %), y mostrarlo en el informe; verificar con tests a mano, incluidos 0 % igual al medido y 100 % igual al respaldo
- [x] 5.3 Documentar el respaldo en `evals/README.md`; verificar que los comandos documentados se ejecutan

## 4. Medición y documentación

- [x] 4.1 Ejecutar el modo real sobre los seis agentes con la captura activa (a cargo del usuario, con el stack levantado) y generar el informe de costes con `python -m evals.costs`; verificar que no hay agentes «sin datos» y que el coste medido coincide con el calculado
- [x] 4.2 Redactar §3.8 del capstone con las tablas generadas, los supuestos y los límites, y actualizar las referencias de §3.4, §5.7 y el glosario; indicando en el punto del coste del no-sistema que no se calcula ningún ahorro y por qué, y añadiendo en §1.1 las premisas cualitativas de la formación —depurar cambios puntuales y atómicos sin recurrir a inferencia, plantear mejores especificaciones y liberar a tech leads y compañeros del acompañamiento de los juniors— sin cifras; verificar que no queda «Sección pendiente» en §3.8 y que cada cifra del texto coincide con el informe
- [x] 4.3 Documentar en `evals/README.md` cómo medir y calcular costes; verificar que los comandos documentados se ejecutan tal cual
