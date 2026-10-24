# Tasks

## 1. Conjunto de calibración y su carga

- [x] 1.1 Crear `evals/datasets/judge.jsonl` con un abanico de ejercicios (buenos, límite y claramente malos) que cubra los cinco criterios de la rúbrica; verificar que cada caso trae identificador único, tipo, enunciado, código de apoyo y respuesta esperada
- [x] 1.2 Añadir la carga y validación del conjunto del juez a `evals/judge_dataset.py` y un test que falle nombrando caso y campo ante un ejercicio mal formado, sin llamar a ningún modelo
- [x] 1.3 Crear el fichero de puntuaciones humanas `evals/datasets/judge.human.json` (vacío o de ejemplo, a rellenar a ciegas) y documentar su formato

## 2. Módulo del juez

- [x] 2.1 Crear `evals/judge.py` (solo biblioteca estándar) que lea el conjunto, llame por HTTP al endpoint compatible con OpenAI de LiteLLM usando el alias `judge` y su propia virtual key, con el prompt de la rúbrica, y devuelva el resultado por ejercicio
- [x] 2.2 Implementar el parseo y la validación del JSON de la rúbrica (puntuación 0–2 por criterio, `null` en el criterio que no aplica, justificación no vacía) y el **reintento único** si incumple; cubierto por tests (incluida la salida envuelta en vallas de código)
- [x] 2.3 Implementar la calibración por κ de Cohen por criterio reutilizando `evals/metrics.cohen_kappa`, excluyendo los ejercicios sin puntuación humana y los no juzgados; verificar con puntuaciones calculadas a mano
- [x] 2.4 Implementar el informe estructurado y el resumen legible en `evals/results/` (modelo juez, rúbrica, puntuaciones por ejercicio y calibración), con la calibración como no disponible si no hay puntuaciones humanas
- [x] 2.5 Añadir tests unitarios (carga, parseo/reintento, κ, informe, alias lógico de la llamada) que corran sin red ni modelos

## 3. Integración con LiteLLM

- [x] 3.1 Añadir el alias `judge` a `infra/litellm/config.yaml` (modelo por `os.environ/JUDGE_MODEL`, clave por `os.environ/JUDGE_API_KEY`) y las entradas correspondientes en `.env.example`, documentando que debe ser un modelo **distinto** de los cuatro de producción
- [x] 3.2 Aprovisionar la virtual key propia del juez (`agent-judge`, restringida al alias `judge`) en `infra/litellm/provision_keys.py` y verificar que `verify_guardrail_coverage.py` sigue en verde y que el alias carga en LiteLLM

## 4. Ejecución y calibración reales

- [x] 4.1 Ejecutar el juez contra el stack levantado (modelo `openrouter/anthropic/claude-sonnet-4.6`) y verificar que juzga los 10 ejercicios de Angular sin escrituras en la base de datos
- [x] 4.2 Puntuar la misma muestra a ciegas (tech lead) y calcular el κ por criterio. Con la rúbrica **anclada** (definición por nivel, la misma para juez y humano), κ **global 0,475** (acuerdo moderado): unicidad 0,796, nivel 0,677, utilidad 0,375, autosuficiencia 0,286, calidad del fallo −0,091 (solo 4 pares). Subió desde 0,312 en la ronda con la rúbrica laxa, lo que **confirma que el problema era la definición de la rúbrica**. Siguen flojos `autosuficiencia` y `calidad_del_fallo` (esta última con muestra mínima): revisarlos es el siguiente paso, no ejecutado
- [x] 4.3 Documentar en `evals/README.md` cómo se ejecuta el juez, el formato de la rúbrica y el de las puntuaciones humanas, y que no corre en CI (necesita modelo)
- [ ] 4.4 Actualizar §5.6 del capstone con el estado real (implementado y en ejecución, sin calibrar) — va en rama aparte, tras el merge

## 5. Integración

- [x] 5.1 Ejecutar `python -m unittest discover -s evals -t . -p "test_*.py"` y verificar que todo pasa sin red (incluidos los tests de `provision_keys.py`)