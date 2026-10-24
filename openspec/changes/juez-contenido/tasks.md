# Tasks

## 1. Conjunto de calibración y su carga

- [ ] 1.1 Crear `evals/datasets/judge.jsonl` con un abanico de ejercicios (buenos, límite y claramente malos) que cubra los cinco criterios de la rúbrica; verificar que cada caso trae identificador único, tipo, enunciado, código de apoyo y respuesta esperada
- [ ] 1.2 Añadir la carga y validación del conjunto del juez a `evals/dataset.py` (o a un módulo `evals/judge_dataset.py`) y un test que falle nombrando caso y campo ante un ejercicio mal formado, sin llamar a ningún modelo
- [ ] 1.3 Crear el fichero de puntuaciones humanas `evals/datasets/judge.human.json` (vacío o de ejemplo, a rellenar a ciegas) y documentar su formato

## 2. Módulo del juez

- [ ] 2.1 Crear `evals/judge.py` (solo biblioteca estándar) que lea el conjunto, llame por HTTP al endpoint compatible con OpenAI de LiteLLM usando el alias `judge` y la master key, con el prompt de la rúbrica, y devuelva el resultado por ejercicio
- [ ] 2.2 Implementar el parseo y la validación del JSON de la rúbrica (puntuación 0–2 por criterio, `null` en el criterio que no aplica, justificación no vacía) y el **reintento único** si incumple; verificar con un doble que devuelve JSON inválido y comprobar que reintenta una vez y, si vuelve a fallar, cuenta como no juzgado
- [ ] 2.3 Implementar la calibración por κ de Cohen por criterio reutilizando `evals/metrics.cohen_kappa`, excluyendo los ejercicios sin puntuación humana y los no juzgados; verificar con puntuaciones calculadas a mano
- [ ] 2.4 Implementar el informe estructurado y el resumen legible en `evals/results/` (modelo juez, rúbrica, puntuaciones por ejercicio y calibración), con la calibración como no disponible si no hay puntuaciones humanas
- [ ] 2.5 Añadir tests unitarios (carga, parseo/reintento, κ, informe) que corran sin red ni modelos, e integrarlos en los tests del arnés que ejecuta el CI

## 3. Integración con LiteLLM

- [ ] 3.1 Añadir el alias `judge` a `infra/litellm/config.yaml` (modelo por `os.environ/JUDGE_MODEL`, clave por `os.environ/JUDGE_API_KEY`) y las entradas correspondientes en `.env.example`, documentando que debe ser un modelo **distinto** de los cuatro de producción
- [ ] 3.2 Verificar que `verify_guardrail_coverage.py` sigue en verde con el alias nuevo y que el alias no rompe el arranque de LiteLLM

## 4. Ejecución y calibración reales

- [ ] 4.1 Ejecutar el juez contra el stack levantado y verificar que produce el informe con las puntuaciones, sin escrituras en la base de datos
- [ ] 4.2 Puntuar la misma muestra a ciegas (tech lead) y calcular el κ por criterio; si algún criterio sale bajo, corregir la rúbrica y volver a ejecutar
- [ ] 4.3 Documentar en `evals/README.md` cómo se ejecuta el juez, el formato de la rúbrica y el de las puntuaciones humanas, y que no corre en CI (necesita modelo)
- [ ] 4.4 Actualizar §5.6 del capstone con el estado real (implementado, calibrado) y verificar que no quedan afirmaciones de «pendiente»

## 5. Integración

- [ ] 5.1 Ejecutar `python -m unittest discover -s evals -t . -p "test_*.py"` y verificar que todo pasa sin red