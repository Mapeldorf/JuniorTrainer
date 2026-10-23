# Tasks

## 1. Métricas puras y carga del dataset

- [x] 1.1 Crear `evals/metrics.py` (exactitud, matriz de confusión de tres clases, κ de Cohen, percentiles p50/p95/p99, Jaccard de términos, tasas) y `evals/test_metrics.py` con valores calculados a mano; verificar con `python -m unittest evals.test_metrics`
- [x] 1.2 Crear `evals/dataset.py` con la carga y validación de los cuatro conjuntos JSONL; verificar con tests que cubren conjunto vacío, identificador duplicado, campo ausente y valor fuera de rango (falla nombrando conjunto, caso y campo)

## 2. Dataset dorado

- [x] 2.1 Crear `evals/datasets/evaluation.jsonl` con respuestas de alumno etiquetadas (`correct`, `incomplete`, `incorrect`, con casos límite) y guiones para el modo simulado, y verificar que carga y cubre los tres veredictos
- [x] 2.2 Crear `evals/datasets/validation.jsonl` (tecnologías válidas, cadenas no técnicas, datos personales, identificadores y variantes duplicadas con su catálogo) y verificar que carga y que incluye casos de ambos contextos
- [x] 2.3 Crear `evals/datasets/generation.jsonl` (combinaciones de tecnologías, tipo, cantidad, entradas web/código fijas y ejercicios previos) y verificar que carga
- [x] 2.4 Crear `evals/datasets/adversarial.jsonl` (respuestas que intentan fijar el veredicto, tecnologías-instrucción, datos personales) y verificar que carga y que cada caso indica el resultado esperado
- [x] 2.5 Documentar en `evals/README.md` el formato de cada conjunto, cómo añadir un caso y que las etiquetas deben revisarse por el tech lead; verificar que los ejemplos del README cargan con `evals/dataset.py`

## 3. Ejecutor por agente (simulado)

- [x] 3.1 Comprobar y registrar en `evals/README.md` el punto de inyección: que `app.service` de evaluador, revisor, validador y ejercicios expone `build_*_model` sustituible, y que `redact`, `list_catalog_technologies` y `search_saved_exercises` son parcheables; verificar importando cada `app.service` en su entorno
- [x] 3.2 Crear `evals/model_wrapper.py` (doble guionizado, envoltorio que cuenta llamadas, mide tiempo, captura el último prompt y distingue rechazo del proxy) con tests unitarios para contar reintentos y capturar prompts
- [x] 3.3 Crear `evals/agent_runner.py` para evaluador y revisor con parcheo de modelo y redacción; verificar ejecutándolo en `agents/evaluator` y `agents/reviewer` sobre `evaluation.jsonl` en modo simulado y comprobando que una justificación de 70 palabras guionizada activa el reintento y que una que sigue pasándose falla la tarea
- [x] 3.4 Extender `evals/agent_runner.py` al validador (parcheo del catálogo, pre-filtro, ambos contextos) y a ejercicios (parcheo de guardados, cardinalidad, límites); verificar con casos guionizados de esquema inválido, de PII rechazada sin llamada al modelo y de candidatos con enunciado de más de 50 palabras

## 4. Orquestador, métricas e informe

- [x] 4.1 Crear `evals/run.py`: selección de agente, conjunto y modo (`--mode simulated` por defecto), lanzamiento de un subproceso por agente con su intérprete, marcado de agente no ejecutado y agregación; verificar con una ejecución completa en modo simulado que produce un informe para los cuatro agentes
- [x] 4.2 Implementar el cálculo de todas las métricas del capstone §5.5 en el informe (validez, límites, reintento, cardinalidad, veredicto con matriz y κ, gate y duplicados, no repetición, latencia con marca de no representativa en simulado, guardarrail como no disponible en simulado); verificar con un test que fija un informe esperado sobre un dataset reducido
- [x] 4.3 Implementar la salida: informe JSON en `evals/results/`, resumen legible por pantalla y código de salida (distinto de cero ante invariante rota en simulado); verificar rompiendo a propósito un guion y comprobando el código de salida y el caso señalado
- [x] 4.4 Añadir `evals/results/` a `.gitignore`; verificar con `git status` tras una ejecución

## 5. Comprobación de delimitadores y adversarial

- [x] 5.1 Implementar la comprobación determinista de que el contenido no confiable viaja entre delimitadores de dato en el prompt capturado (respuesta de alumno, tecnologías) y la del pre-filtro del validador; verificar que falla si se altera un prompt en un test con el prompt manipulado
- [x] 5.2 Implementar la métrica de ataque exitoso del modo real (adversarial con veredicto `correct` distinto de su etiqueta) sin que bloquee la ejecución; verificar con un doble que simula un ataque exitoso

## 6. Modo real

- [x] 6.1 Implementar el modo real (`--mode real`): comprobación previa de LiteLLM y de la credencial del agente, registro de alias de modelo, medición del rechazo por guardarrail frente al fallo de contrato; verificar que sin stack falla antes de evaluar ningún caso con un mensaje claro
- [ ] 6.2 Ejecutar el modo real contra el stack levantado sobre un subconjunto pequeño por agente y verificar que el informe contiene latencia real, rechazos de guardarrail y ataques exitosos, sin escrituras en la base de datos

## 7. Integración continua

- [x] 7.1 Añadir el job `agent-evals` a `.github/workflows/ci.yml` con filtro de rutas (`agents/**`, `evals/**`), entornos separados por agente y solo modo simulado; verificar en un PR de prueba que corre al tocar un agente, que no corre al tocar solo el frontend y que no hace llamadas a proveedores
- [x] 7.2 Actualizar `capstone/juniortrainer-capstone.md` (§5.3 y §5.4 con el estado real de los niveles 2 y 3; §5.5 con lo implementado y lo que queda); verificar que no quedan afirmaciones de «Pendiente» sobre lo implementado

## 8. Integración

- [x] 8.1 Ejecutar la suite completa en modo simulado desde un entorno limpio (sin `.env`, sin red) y verificar código de salida 0 e informe completo

## 9. Agentes web y de código

- [x] 9.1 Ampliar `evals/dataset.py` con los conjuntos `web` y `code` (y objetivos `web`/`code` en el adversarial) y sus tests; verificar que los casos mal formados fallan nombrando conjunto, caso y campo
- [x] 9.2 Ampliar `evals/model_wrapper.py` para guardar el contenido de cada respuesta y el prompt de usuario de cada llamada, con tests; verificar que se conservan en orden
- [x] 9.3 Crear `evals/datasets/web.jsonl` y `evals/datasets/code.jsonl` (repos de ejemplo, rutas inventadas, memoria, presupuestos) y los casos adversariales web/code; verificar que cargan
- [x] 9.4 Ampliar `evals/agent_runner.py` a web y código (sustitutos de Tavily, GitHub y memoria que descuentan presupuesto; modo real con Tavily real y `EVALS_REAL_REPO`; resultado `skipped`); verificar en modo simulado que ambos agentes cumplen sus invariantes
- [x] 9.5 Ampliar `evals/report.py` con las métricas de web y código (tasa de reintento no disponible para ellos) y sus tests con valores calculados a mano
- [x] 9.6 Ampliar `evals/run.py`, el job `agent-evals` de CI (seis entornos), el README de `evals/` y §5.3/§5.4/§5.5 del capstone; verificar con una ejecución completa de los seis agentes en modo simulado, con código de salida 0
