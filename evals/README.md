# Suite de evaluación de agentes

Mide los agentes **evaluador, revisor, validador y de ejercicios** sobre un dataset dorado versionado en este repositorio. Solo usa la biblioteca estándar de Python; los agentes se ejecutan con sus propias dependencias.

Especificación: `openspec/specs/agent-evaluation/` (o el change `suite-evaluacion-agentes` mientras no esté archivado). Contexto: capítulos 5.4 y 5.5 del capstone.

## Uso

Desde la raíz del repositorio:

```bash
python -m evals.run                         # modo simulado, los cuatro agentes
python -m evals.run --agents evaluator      # solo uno
python -m evals.run --mode real --limit-per-set 5   # modelos reales vía LiteLLM
python -m unittest discover -s evals -t . -p "test_*.py"   # tests del propio arnés
```

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

En ambos modos el catálogo de tecnologías y los ejercicios previos los aporta el dataset, y la redacción de PII (Presidio) se sustituye por la identidad: **no se lee ni se escribe en la base de datos**. El modo real comprueba antes de empezar que LiteLLM responde y que existe la credencial del agente.

## Dataset (`evals/datasets/*.jsonl`)

Una línea JSON por caso, con `id` único dentro de su conjunto. La carga (`evals/dataset.py`) falla antes de ejecutar nada si un caso está mal formado, indicando conjunto, caso y campo.

| Fichero | Campos principales |
|---|---|
| `evaluation.jsonl` | `statement`, `code`, `expected_answer`, `student_answer`, `label` (`correct`/`incomplete`/`incorrect`), `proposed_justification` (entrada del revisor) |
| `validation.jsonl` | `technologies`, `context` (`catalog_entry`/`generation`), `catalog`, `expect_valid`, `expect_duplicates`, `expect_prefilter`, `category` |
| `generation.jsonl` | `type`, `count`, `technologies`, `web_result`, `code_result`, `saved_statements`, `group` (generaciones consecutivas), `topics` |
| `adversarial.jsonl` | `target` (`evaluator`/`reviewer`/`validator`), `kind` y los campos de `evaluation` o `validation` según el objetivo |

**Campos solo del modo simulado.** `sim` es el guion de respuestas crudas del modelo (una lista, o un objeto agente → lista cuando el caso sirve a varios agentes); sin `sim`, el doble responde bien según la etiqueta del caso. `sim_expect` declara qué debe hacer el agente con ese guion (`outcome`: `ok` o `contract_error`, y `calls`: nº de llamadas al modelo); por defecto `ok` con 1 llamada. Si el resultado no coincide, la invariante se rompe y el proceso sale con código 1.

### Añadir un caso

1. Añade una línea al conjunto correspondiente (conserva el `id` único y los campos obligatorios).
2. Si el caso es para el modo simulado y debe provocar un comportamiento concreto (un reintento, un JSON inválido), añade `sim` y `sim_expect`.
3. `python -m unittest evals.test_dataset` comprueba que el dataset carga; `python -m evals.run` que las invariantes se cumplen.

> **Las etiquetas las ha redactado quien implementó la suite**, a partir de lo que piden los prompts. Antes de tomar la exactitud o el κ de Cohen del modo real como referencia, el tech lead debe revisarlas.

## Métricas

Validez de salida · adherencia a límites (enunciado ≤ 50 palabras, nombre ≤ 8, justificación ≤ 50) · tasa de activación del reintento correctivo (casos con más de una llamada al modelo) · conformidad de cardinalidad · exactitud del veredicto con matriz de confusión y κ de Cohen · falsos positivos y negativos del gate del validador y precisión/cobertura de duplicados · solapamiento de temas entre generaciones consecutivas (Jaccard sobre términos: aproximación determinista del solapamiento semántico) · falsos positivos de guardarraíl (solo modo real) · latencia p50/p95/p99 (solo representativa en modo real).

Una métrica sin casos aparece como `n/d`, no como cero.

## Casos adversariales

Comprobación determinista en ambos modos: el contenido no confiable (respuesta del alumno, justificación propuesta, tecnologías) viaja entre los delimitadores de dato en el prompt que recibe el modelo, y los datos personales los rechaza el pre-filtro antes de llamar al modelo. En modo real se cuentan además los **ataques exitosos** (un veredicto `correct` con una etiqueta distinta, o un `valid=true` donde no debía), sin que bloqueen la ejecución.

Hallazgo informativo: si el texto del alumno incluye el marcador de fin de delimitador, el prompt contiene dos y el contenido sigue "dentro" del tramo; el informe lo lista en `spoofable_markers` (hoy, `ad-eval-cierre-delimitador`).

## Punto de acoplamiento con los agentes

El arnés sustituye en `app.service` de cada agente los nombres `build_*_model` y `redact` (evaluador y revisor), `list_catalog_technologies` (validador) y `search_saved_exercises` / `exercise_reader_conn_string` (ejercicios). Si un agente renombra alguno, el arnés falla con un mensaje que nombra el símbolo ausente.
