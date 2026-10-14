# Tasks

## 1. Agentes "generator" (web, code, exercises)

- [x] 1.1 En `agents/web/app/config.py`, eliminar el campo `generator_model: str = "generator"` de `Settings`. En `agents/web/app/llm.py`, añadir `_MODEL_NAME = "generator"` como constante de modulo y usarla en `model=_MODEL_NAME` en vez de `settings.generator_model`. Verificar que `python -c "from app.config import get_settings; from app.llm import build_generator_model"` no falla. Verificado con `ast.parse` (sintaxis); el import real con dependencias (`langchain_openai`) se verifica en el grupo 3, dentro del contenedor.
- [x] 1.2 Repetir el mismo cambio en `agents/code/app/config.py`/`llm.py` y `agents/exercises/app/config.py`/`llm.py`. Verificar el mismo import check en cada uno. Verificado con `ast.parse` en los 4 ficheros.

## 2. Agentes "evaluator" y "reviewer"

- [x] 2.1 En `agents/evaluator/app/config.py`, eliminar `evaluator_model: str = "evaluator"`; en `agents/evaluator/app/llm.py`, `_MODEL_NAME = "evaluator"`. Verificar import check. Verificado con `ast.parse`.
- [x] 2.2 En `agents/reviewer/app/config.py`, eliminar `reviewer_model: str = "reviewer"`; en `agents/reviewer/app/llm.py`, `_MODEL_NAME = "reviewer"`. Verificar import check. Verificado con `ast.parse`.

## 3. Verificacion end-to-end contra el bug real

- [x] 3.1 Reconstruir y levantar los 5 agentes (`docker compose up -d --build agent-web agent-code agent-exercises agent-evaluator agent-reviewer`) y confirmar con `docker compose exec <agente> env` que `GENERATOR_MODEL`/`EVALUATOR_MODEL`/`REVIEWER_MODEL` siguen llegando al contenedor (no se tocan las variables de entorno, solo dejan de leerse) pero ya no afectan al valor que el agente envia. Verificado: los 5 arrancan sin error (import checks de 1.1/1.2/2.1/2.2 validados implicitamente), y `REVIEWER_MODEL` sigue presente en el entorno del contenedor sin tocar `.env`.
- [x] 3.2 Reproducir el escenario que detecto el bug: ejecutar un flujo real a traves de `agent-reviewer` (p. ej. copiando `scripts/` al contenedor y corriendo `python -m scripts.verify_justification_limit`, igual que en la verificacion de `litellm-key-budgets`) SIN forzar `-e REVIEWER_MODEL=reviewer`, y confirmar que ya no falla con `403 key_model_access_denied`. Verificado: las dos justificaciones de prueba se generan y recortan correctamente, sin ningun error de modelo.
- [x] 3.3 Repetir una verificacion equivalente para al menos uno de los agentes "generator" (web, code o exercises) y para evaluator, confirmando en los tres casos que la llamada real a LiteLLM se completa (o falla por un motivo de negocio normal -- p. ej. JSON invalido del modelo -- nunca por `403 key_model_access_denied`). Verificado: `agent-web` (`verify_generator_summary.py`, resumen real con Tavily + modelo `generator`) y `agent-evaluator` (`verify_justification_limit.py`, 3 veredictos correctos) completan su flujo real sin ningun error de modelo.
