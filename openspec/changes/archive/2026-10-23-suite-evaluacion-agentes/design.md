# Design

## Context

Ver `proposal.md`. Lo que se ha comprobado en el código:

- Cada agente es un paquete independiente cuyo paquete Python se llama `app` (`agents/<x>/app/`), con su propio `requirements.txt` y, en local, su `.venv`. Dos agentes no pueden importarse en el mismo proceso.
- La lógica está separada del transporte: `evaluate_answer`, `review_justification`, `validate_technologies` y `generate_exercises` son funciones `async` en `app/service.py` que importan `build_*_model` desde `app.llm` y llaman a `model.ainvoke(messages, extra_body=...)`. Basta con sustituir el nombre `build_*_model` en `app.service` para inyectar un modelo falso, sin tocar producción.
- Los reintentos correctivos (evaluador, revisor, validador, ejercicios) se reconocen por una **segunda llamada a `ainvoke`**; no hay contador ni evento expuesto, solo un `logger.warning`.
- Dependencias externas que el arnés debe fijar: Presidio (`app.redaction.redact`, en evaluador y revisor), el catálogo de tecnologías (`list_catalog_technologies`, validador) y los ejercicios guardados (`search_saved_exercises`, ejercicios, que ya tolera su fallo).
- Los 19 `verify_*.py` hacen comprobaciones de este mismo tipo pero con un único ejemplo cada uno, sin dataset ni métricas.
- La CI actual solo cubre backend, frontend y la comprobación estática de LiteLLM.

## Goals / Non-Goals

**Goals:**
- Un único punto de entrada que, con un comando, evalúa los cuatro agentes sobre el dataset y emite un informe comparable entre ejecuciones.
- Que el modo simulado sea determinista y barato para correr en cada PR, y que ejercite la lógica real de parseo, límites y reintento.
- Que el modo real reutilice exactamente el mismo dataset y el mismo informe, para poder comparar primario y fallback cambiando solo la variable de entorno del modelo.

**Non-Goals:**
- Juzgar calidad pedagógica (juez LLM), medir costes, hacer red teaming o fijar umbrales de bloqueo.
- Sustituir los `verify_*.py` existentes: se conservan; convertirlos en tests es otro trabajo.

## Decisions

**1. Un orquestador y un ejecutor por agente, en procesos separados.** `evals/run.py` (solo biblioteca estándar) lee el dataset, lanza para cada agente un subproceso con `cwd=agents/<x>` y el intérprete de su entorno, y agrega los resultados. El ejecutor (`evals/agent_runner.py`) se importa con `PYTHONPATH` apuntando a la raíz del repo, hace el parcheo y devuelve un JSON por stdout. *Alternativa descartada:* un solo proceso con manipulación de `sys.modules` para cargar varios `app`: frágil y difícil de razonar.

**2. Inyección por sustitución del símbolo `build_*_model` en `app.service`.** Es el único punto de acoplamiento, y se comprueba en la primera tarea. *Alternativa:* un LiteLLM falso por HTTP; descartada porque exige red local y no prueba más código del agente. *Alternativa:* modificar los agentes para aceptar un modelo inyectado; descartada para no tocar producción.

**3. Un envoltorio común del modelo.** Tanto el doble (simulado) como el modelo real (real) se envuelven en una clase que cuenta llamadas, mide tiempo y captura el último prompt enviado. De ahí salen, sin tocar el agente, la tasa de reintento, la latencia y la comprobación de delimitadores. La captura de rechazos del proxy distingue un error de guardarrail de un fallo de contrato.

**4. El caso guioniza al doble.** Cada caso de modo simulado puede llevar `sim.responses`, una lista de respuestas crudas en orden de llamada (por ejemplo, una justificación de 70 palabras seguida de una de 40). El doble las devuelve tal cual; así se ejercitan el parseo, el límite y el reintento reales. Un caso sin guion usa una respuesta por defecto derivada de su etiqueta, que sirve para el flujo feliz.

**5. Formato JSONL en `evals/datasets/{generation,evaluation,validation,adversarial}.jsonl`.** Legible por diff, una línea por caso, validado al cargar con comprobaciones propias (sin dependencia nueva). Los casos con catálogo o ejercicios previos los aportan en el propio caso, y el arnés parchea `list_catalog_technologies` y `search_saved_exercises` con ellos, de modo que ningún modo toca la base de datos. Presidio se sustituye por una redacción identidad en ambos modos: su efecto se verifica ya en `verify_redaction.py`, y su falso positivo se mide en el modo real a través del proxy.

**6. Métricas puras en `evals/metrics.py`.** Funciones sin E/S (exactitud, matriz de confusión, κ de Cohen, percentiles por rango más cercano, Jaccard de términos) para poder probarlas con valores calculados a mano. *No repetición de temas:* el capstone habla de solapamiento semántico, pero hacerlo sin modelos de *embeddings* solo es posible de forma aproximada; se usa el índice de Jaccard sobre términos normalizados y se declara como aproximación.

**7. Dos modos, por defecto el simulado.** El modo real se activa con `--mode real`, comprueba antes que LiteLLM responde y que existe la credencial del agente, y registra el alias de modelo. El código de salida distingue: simulado, no cero ante cualquier invariante rota; real, cero salvo error de ejecución. Los umbrales llegarán con la línea base.

**8. CI con un trabajo propio y filtro de rutas.** Un job `agent-evals` en `ci.yml` con `dorny/paths-filter` (`agents/**`, `evals/**`), que instala los `requirements.txt` de los cuatro agentes en entornos separados y ejecuta el modo simulado. Es coherente con el job `litellm-guardrails`, y no necesita secretos.

**9. Resultados en `evals/results/`, ignorados por git.** Salvo un informe de referencia que se guarda a propósito (`evals/baseline/`) cuando se tome la línea base real de §5.7. Evita ruido en los diffs.

**10. Agentes web y de código (añadidos tras aclarar que sus dependencias no suponen coste).**
- *Simulado:* se sustituyen en `app.service` `AsyncTavilyClient`, `get_settings` y `tavily_search` (web), `list_files` y `read_file` (código) y las funciones de memoria de ambos. Los sustitutos reproducen el contrato de los reales (descuentan el presupuesto con `consume()` antes de actuar), de modo que `SearchBudget` y `FileBudget` se ejercitan de verdad.
- *Real:* la memoria se anula siempre (ni se lee ni se escribe). Web usa Tavily real. Código necesita un repositorio real, que no puede ir en el dataset porque puede ser privado: se indica por entorno (`EVALS_REAL_REPO`); sin él, sus casos se omiten con el motivo (resultado `skipped`, fuera de todas las métricas).
- *Observabilidad sin tocar los agentes:* el envoltorio del modelo guarda ahora el contenido de cada respuesta y el prompt de usuario de cada llamada. De ahí salen las rutas elegidas por el modelo (frente al listado real: la validación del agente las filtra y no deja rastro) y la comprobación de delimitadores del segundo prompt del agente de código, que es el que lleva el contenido de los ficheros.
- *Reintento:* web y código no tienen reintento correctivo, y el de código hace siempre dos llamadas; por eso la tasa de reintento se informa como no disponible para ellos y sus expectativas de llamadas por defecto son 1 y 2.
- *Fundamentación de fragmentos:* un fragmento está fundamentado si su código aparece literalmente en el fichero que declara y empieza en `start_line`. Es una comprobación de cadena, no semántica.
- *Declaración de ausencia de fuentes (web):* heurística por palabras clave en la sección de la tecnología dentro del resumen; se declara como tal en el informe.

## Risks / Trade-offs

- [El modo simulado solo prueba el código, no el modelo] → Se dice en el informe y en la documentación; los números de calidad salen del modo real.
- [Etiquetas escritas por quien implementa, no por un humano independiente] → Se declara como supuesto; el tech lead debe revisarlas antes de tomar el κ como referencia.
- [Un dataset pequeño da métricas ruidosas en modo real] → Se informa el número de casos junto a cada métrica; el tamaño crece sin cambiar el arnés.
- [El parcheo depende de nombres internos (`build_*_model`)] → Una comprobación inicial falla con un mensaje claro si el símbolo cambia.
- [Cuatro entornos de dependencias alargan el CI] → Filtro de rutas y caché de `pip`; solo corre cuando se tocan agentes o `evals/`.
- [El modo real consume presupuesto de las virtual keys (5 USD/30 días)] → Se documenta el coste esperado por ejecución y se permite filtrar por agente y por conjunto.

## Open Questions

- ¿Se versiona un informe de referencia real? Se decide al tomar la primera línea base, sin afectar a las specs ni a las tareas.
