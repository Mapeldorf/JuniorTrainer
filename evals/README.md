# Suite de evaluación de agentes

Mide los seis agentes (**evaluador, revisor, validador, ejercicios, web y código**) sobre un dataset dorado versionado en este repositorio. Solo usa la biblioteca estándar de Python; los agentes se ejecutan con sus propias dependencias.

Especificación: `openspec/specs/agent-evaluation/` (o el change `suite-evaluacion-agentes` mientras no esté archivado). Contexto: capítulos 5.4 y 5.5 del capstone.

## Uso

Desde la raíz del repositorio:

```bash
python -m evals.run                         # modo simulado, los cuatro agentes
python -m evals.run --agents evaluator      # solo uno (o varios: --agents web,code)
python -m evals.run --mode real --limit-per-set 5   # modelos reales vía LiteLLM
EVALS_REAL_REPO=propietario/repo@commit python -m evals.run --mode real --agents code   # el agente de código necesita un repo real
python -m evals.run --mode real --case-timeout 60     # límite por caso (180 s por defecto)
python -m unittest discover -s evals -t . -p "test_*.py"   # tests del propio arnés
```

En modo real los adversariales de web y código **no se ejecutan**: su contenido no confiable (un fragmento de búsqueda, un fichero) lo aporta el caso, pero en ese modo el agente lee Tavily y GitHub de verdad, así que no se inyectaría nada y el resultado daría una falsa sensación de resistencia. Sí se ejecutan los del evaluador, el revisor y el validador, cuya entrada la controla el caso.

En modo real se imprime una línea por caso con su estado y su duración. `--limit-per-set N` toma N casos **repartidos** por todo el conjunto (no los N primeros) y en modo real omite los casos guionizados (`sim`/`sim_expect`), que solo tienen sentido con un modelo falso.

El informe JSON queda en `evals/results/` (ignorado por git) y se imprime un resumen. Código de salida: `0` bien; `1` modo simulado con una invariante rota; `2` la ejecución falló (dataset inválido, agente que no arranca, LiteLLM caído en modo real).

### Entornos de los agentes

Todos los agentes se llaman `app` como paquete, así que cada uno corre en su propio proceso. El arnés usa `agents/<agente>/.venv` si existe; si no, el intérprete actual (que fallará si faltan dependencias y lo marcará como *no ejecutado*). Para forzar uno: `--python validator=/ruta/a/python`.

```bash
python -m venv agents/validator/.venv
agents/validator/.venv/Scripts/pip install -r agents/validator/requirements.txt   # bin/pip en Linux/macOS
```

## Dos modos

| | Simulado (por defecto) | Real (`--mode real`) |
|---|---|---|
| Modelo | Doble guionizado por el caso | El real, vía LiteLLM y la virtual key del agente |
| Coste / red | Ninguno | Gasta presupuesto de las virtual keys; necesita el stack levantado |
| Qué demuestra | Que **el código** del agente parsea, aplica límites y reintenta bien | Calidad del modelo, latencia real, falsos positivos de guardarraíl, ataques exitosos |
| Falla el proceso si… | Una invariante del caso no se cumple | Solo si la ejecución en sí falla (no hay umbrales todavía) |
| Se ejecuta en CI | Sí, en PR que toquen `agents/**` o `evals/**` | No |

En ambos modos el catálogo de tecnologías, los ejercicios previos y la memoria de los agentes web y de código los aporta el dataset (o se anulan), y la redacción de PII (Presidio) se sustituye por la identidad: **no se lee ni se escribe en la base de datos**. El modo real comprueba antes de empezar que LiteLLM responde y que existe la credencial del agente (y, para el agente web, `TAVILY_API_KEY`).

**Web y código.** En modo simulado se sustituyen Tavily, las lecturas de GitHub y la memoria por datos del caso (los sustitutos descuentan el presupuesto como las herramientas reales). En modo real el agente web usa Tavily de verdad. El agente de código lee GitHub de verdad, y para ello necesita un repositorio que no puede ir en el dataset (puede ser privado): se indica con `EVALS_REAL_REPO=propietario/repo@commit`. Los casos traen las tecnologías de sus repositorios de ejemplo (React, FastAPI…); si el repositorio real usa otras, fija `EVALS_REAL_TECHNOLOGIES=Angular,TypeScript` (si no, el modelo elegirá cero ficheros y la tarea fallará con «no se pudo leer ningún fichero»). Sin `EVALS_REAL_REPO`, los casos del agente de código salen como **omitidos** con el motivo, no entran en ninguna métrica y la ejecución no falla.

## Dataset (`evals/datasets/*.jsonl`)

Una línea JSON por caso, con `id` único dentro de su conjunto. La carga (`evals/dataset.py`) falla antes de ejecutar nada si un caso está mal formado, indicando conjunto, caso y campo.

| Fichero | Campos principales |
|---|---|
| `evaluation.jsonl` | `statement`, `code`, `expected_answer`, `student_answer`, `label` (`correct`/`incomplete`/`incorrect`), `proposed_justification` (entrada del revisor) |
| `validation.jsonl` | `technologies`, `context` (`catalog_entry`/`generation`), `catalog`, `expect_valid`, `expect_duplicates`, `expect_prefilter`, `category` |
| `generation.jsonl` | `type`, `count`, `technologies`, `web_result`, `code_result`, `saved_statements`, `group` (generaciones consecutivas), `topics` |
| `web.jsonl` | `technologies`, `search_results` (tecnología → lista de `{title, url, snippet}`), `cached` (simula memoria) |
| `code.jsonl` | `owner`, `repo`, `commit_sha`, `technologies`, `files` (`{path, size_bytes}`), `contents` (ruta → texto), `cached` |
| `adversarial.jsonl` | `target` (`evaluator`/`reviewer`/`validator`/`web`/`code`), `kind` y los campos del conjunto correspondiente al objetivo |

**Campos solo del modo simulado.** `sim` es el guion de respuestas crudas del modelo (una lista, o un objeto agente → lista cuando el caso sirve a varios agentes); sin `sim`, el doble responde bien según la etiqueta del caso. `sim_expect` declara qué debe hacer el agente con ese guion (`outcome`: `ok` o `contract_error`, y `calls`: nº de llamadas al modelo); por defecto `ok` con 1 llamada. Si el resultado no coincide, la invariante se rompe y el proceso sale con código 1.

### Añadir un caso

1. Añade una línea al conjunto correspondiente (conserva el `id` único y los campos obligatorios).
2. Si el caso es para el modo simulado y debe provocar un comportamiento concreto (un reintento, un JSON inválido), añade `sim` y `sim_expect`.
3. `python -m unittest evals.test_dataset` comprueba que el dataset carga; `python -m evals.run` que las invariantes se cumplen.

> **Las etiquetas las ha redactado quien implementó la suite**, a partir de lo que piden los prompts. Antes de tomar la exactitud o el κ de Cohen del modo real como referencia, el tech lead debe revisarlas.

## Métricas

Validez de salida · adherencia a límites (enunciado ≤ 50 palabras, nombre ≤ 8, justificación ≤ 50) · tasa de activación del reintento correctivo (casos con más de una llamada al modelo) · conformidad de cardinalidad · exactitud del veredicto con matriz de confusión y κ de Cohen · falsos positivos y negativos del gate del validador y precisión/cobertura de duplicados · solapamiento de temas entre generaciones consecutivas (Jaccard sobre términos: aproximación determinista del solapamiento semántico) · falsos positivos de guardarraíl (solo modo real) · latencia p50/p95/p99 (solo representativa en modo real).

**Solo agente web:** presupuesto de 5 búsquedas, cobertura de tecnologías en el resumen y declaración explícita de las que no tienen fuentes (heurística por palabras clave). **Solo agente de código:** rutas elegidas por el modelo que existen en el listado real (la validación del agente las filtra y no deja rastro, por eso se leen de la respuesta del modelo), presupuesto de 10 lecturas y fragmentos fundamentados (el código aparece literalmente en el fichero y empieza en `start_line`). Web y código no tienen reintento correctivo (y el de código hace siempre dos llamadas), así que su tasa de reintento es `n/d`.

Una métrica sin casos aparece como `n/d`, no como cero.

## Costes (capstone §3.8)

Con el modo real, cada caso guarda los tokens (entrada, salida y razonamiento) y el coste facturado que informa el proveedor. `evals.costs` los convierte en las tablas de §3.8:

```bash
python -m evals.run --mode real --agents evaluator,reviewer,validator,exercises,web,code --limit-per-set 10
EVALS_REAL_REPO=propietario/repo@commit EVALS_REAL_TECHNOLOGIES=Angular,TypeScript python -m evals.run --mode real --agents code --limit-per-set 3
python -m evals.costs evals/results/<informe-1>.json evals/results/<informe-2>.json   # el ultimo informe manda por agente
python -m evals.update_prices                                                       # refresca evals/prices.json desde OpenRouter
```

- **Entradas:** los informes reales, `prices.json` (precios con fecha y fuente, modelos de produccion y de referencia, planes de Tavily) y `cost_assumptions.json` (supuestos de uso; cada uno lleva su origen: `usuario`, `capstone` o `hipotesis`). Un informe simulado se rechaza.
- **Salida determinista** (`evals/results/<informe>-costes.{json,md}`): medicion por agente, coste por operacion con desglose, campana por fases y nivel de uso (con el pico de 30 dias frente al presupuesto de cada clave de LiteLLM, Tavily segun el plan y sensibilidad a las claves de memoria), costes unitarios, comparativa con el modelo de referencia y comprobacion cruzada de lo facturado frente al precio de lista.
- **Modelo de respaldo:** `prices.json` guarda el respaldo de cada rol (el de `infra/litellm/config.yaml`) con el precio por proveedor de inferencia que publica Hugging Face; `python -m evals.update_prices` lo refresca sin credenciales. El informe da el coste con el proveedor mas barato y el mas caro, con los mismos tokens medidos, y ponderado por la fraccion de llamadas que cae al respaldo (0 %, 5 %, 20 %, 100 %). **Esa fraccion real no se mide** (el alias no distingue el modelo que contesto): son escenarios.
- **Solo costes:** no calcula ahorros, retornos ni puntos de equilibrio.
- **Limites:** la composicion por agente aproxima la cadena real (en produccion la entrada de un agente depende de la salida del anterior); el coste facturado es el del modelo que respondio, primario o respaldo, y el alias no los distingue; el modelo de referencia es una cota inferior.

## Casos adversariales

Comprobación determinista en ambos modos: el contenido no confiable (respuesta del alumno, justificación propuesta, tecnologías, fragmentos de búsqueda web, ficheros del repositorio) viaja entre los delimitadores de dato en el prompt que recibe el modelo, y los datos personales los rechaza el pre-filtro antes de llamar al modelo. En modo real se cuentan además los **ataques exitosos** (un veredicto `correct` con una etiqueta distinta, o un `valid=true` donde no debía), sin que bloqueen la ejecución.

Hallazgo informativo: si el contenido no confiable incluye el marcador de fin de delimitador, el prompt contiene uno de más y el contenido sigue "dentro" de su tramo según el arnés; el informe lo lista en `spoofable_markers` (hoy, `ad-eval-cierre-delimitador`, `ad-web-cierre-delimitador` y `ad-code-cierre-delimitador`). En el agente de código la comprobación reproduce el formato numerado de líneas del prompt (`1: ...`), así que si el agente lo cambia la comprobación fallará y habrá que actualizarla.

## Punto de acoplamiento con los agentes

El arnés sustituye en `app.service` de cada agente los nombres `build_*_model` y `redact` (evaluador y revisor), `list_catalog_technologies` (validador), `search_saved_exercises` / `exercise_reader_conn_string` (ejercicios), `get_cached_research`, `save_research`, `AsyncTavilyClient`, `get_settings` y `tavily_search` (web) y `get_cached_analysis`, `save_analysis`, `list_files` y `read_file` (código). Si un agente renombra alguno, el arnés falla con un mensaje que nombra el símbolo ausente.
