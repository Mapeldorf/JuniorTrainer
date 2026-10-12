"""Logica de negocio del agente de ejercicios, separada del transporte A2A.

Progresion por tarea (ver tasks.md del change `generacion-ejercicios-agentes`):
  - 5.1: scaffold.
  - 5.2: `search_saved_exercises` (ver app/tools/saved_exercises.py).
  - 5.3: una sola llamada al modelo `generator` via LiteLLM que recibe
    los resultados de web/codigo, el tipo, el numero pedido y los
    enunciados ya guardados (via `search_saved_exercises`), y devuelve
    exactamente `count` candidatos.
  - 5.4: memoria larga PROPIA (ver app/memory.py) -- se suma al
    historial de enunciados a evitar (que antes solo llevaba los
    guardados) y se escribe el historial tras generar.
  - 5.5 (este fichero, ahora): `trace_id` opcional que se reenvia a
    LiteLLM (ver app/tracing.py), igual que en los otros dos agentes.
"""

import json
import logging

from app.db import exercise_reader_conn_string
from app.llm import build_generator_model
from app.memory import get_recent_statements, save_statements
from app.models import CandidateExercise, ExerciseCodeBlock, ExerciseGenerationResult
from app.tools.saved_exercises import SearchBudget, SearchBudgetExceeded, search_saved_exercises
from app.tracing import litellm_trace_metadata

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Eres un asistente que redacta ejercicios de programacion para "
    "alumnos. Se te da: el tipo de ejercicio ('knowledge' = pregunta de "
    "conocimiento, sin necesidad de depurar nada; 'debug' = un fragmento "
    "de codigo con un fallo introducido a proposito que el alumno debe "
    "encontrar y corregir), el numero exacto de candidatos pedidos, un "
    "resumen de documentacion de las tecnologias relevantes, un resumen "
    "y fragmentos de un repositorio real (si los hay), y una lista de "
    "enunciados YA PROPUESTOS antes para este mismo tipo que NO debes "
    "repetir (ni el mismo tema con otras palabras).\n\n"
    "Responde EXCLUSIVAMENTE con un array JSON de EXACTAMENTE el numero "
    "de candidatos pedido. Cada candidato es un objeto con tres campos: "
    '"statement" (el enunciado, en español, claro y autocontenido), '
    '"code" (array de objetos {"file": ruta o null, "code": texto}, con '
    "el codigo de apoyo necesario para resolver el ejercicio -- para "
    "'debug' DEBE incluir el fallo ya introducido en el codigo; para "
    "'knowledge' puede quedar vacio si el enunciado no necesita codigo "
    'de apoyo), "expected_answer" (la respuesta esperada: para \'debug\', '
    "que corregir y por que; para 'knowledge', la respuesta a la "
    "pregunta). No inventes tecnologias que no esten en los resumenes "
    "proporcionados."
)


class ExerciseGenerationError(RuntimeError):
    """El modelo no devolvio candidatos validos (JSON invalido, numero incorrecto, etc.)."""


async def generate_exercises(
    exercise_type: str,
    count: int,
    web_result: dict | None,
    code_result: dict | None,
    trace_id: str | None = None,
) -> ExerciseGenerationResult:
    saved_statements: list[str] = []
    try:
        budget = SearchBudget(max_calls=3)
        saved = await search_saved_exercises(exercise_reader_conn_string(), exercise_type, budget, limit=10)
        saved_statements = [s.statement for s in saved]
    except SearchBudgetExceeded:
        # No deberia pasar en una unica llamada con un budget de 3, pero si
        # pasara no es razon para fallar la tarea: se sigue sin esa lista.
        logger.warning("budget de search_saved_exercises agotado inesperadamente", exc_info=True)
    except Exception:
        # "Una memoria caida no bloquea la generacion" aplica igual a esta
        # consulta de solo lectura: si Supabase no responde, se continua
        # sin la lista de guardados en vez de fallar la tarea entera.
        logger.warning("fallo consultando ejercicios guardados", exc_info=True)

    # Memoria larga PROPIA (tarea 5.4): enunciados ya propuestos antes para
    # este tipo, guardados o no -- se suma a los guardados para formar la
    # lista completa de temas a evitar. Un fallo de lectura ya se trata
    # como "sin historial" dentro de get_recent_statements().
    recent_statements = await get_recent_statements(exercise_type)

    avoid_statements = [*saved_statements, *recent_statements]

    candidates = await _draft_candidates(
        exercise_type, count, web_result, code_result, avoid_statements, trace_id
    )

    # Se escribe DESPUES de generar con exito: si _draft_candidates lanza
    # (JSON invalido, numero incorrecto...), no hay enunciados nuevos que
    # guardar. Un fallo de escritura se ignora dentro de save_statements().
    await save_statements(exercise_type, [c.statement for c in candidates])

    return ExerciseGenerationResult(
        candidates=candidates,
        memory_hit=bool(avoid_statements),
    )


async def _draft_candidates(
    exercise_type: str,
    count: int,
    web_result: dict | None,
    code_result: dict | None,
    avoid_statements: list[str],
    trace_id: str | None = None,
) -> list[CandidateExercise]:
    model = build_generator_model()

    blocks = [f"Tipo de ejercicio: {exercise_type}", f"Numero exacto de candidatos pedido: {count}"]

    if web_result and web_result.get("summary"):
        blocks.append(f"### Resumen de documentacion (agente web)\n{web_result['summary']}")
    if code_result and code_result.get("summary"):
        blocks.append(f"### Resumen del repositorio (agente de codigo)\n{code_result['summary']}")
        fragments = code_result.get("fragments") or []
        if fragments:
            fragment_lines = "\n".join(
                f"- {f.get('file')}:{f.get('start_line')} -- {f.get('note')}\n  {f.get('code')!r}"
                for f in fragments
            )
            blocks.append(f"### Fragmentos de codigo del repositorio\n{fragment_lines}")

    if avoid_statements:
        avoid_lines = "\n".join(f"- {s}" for s in avoid_statements)
        blocks.append(f"### Enunciados YA PROPUESTOS (no repetir el tema)\n{avoid_lines}")
    else:
        blocks.append("### Enunciados ya propuestos\n(ninguno todavia)")

    human_prompt = "\n\n".join(blocks)

    response = await model.ainvoke(
        [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": human_prompt},
        ],
        extra_body=litellm_trace_metadata(trace_id),
    )
    items = _parse_json(response.content, expect=list)
    if len(items) != count:
        raise ExerciseGenerationError(
            f"se pidieron {count} candidatos y el modelo devolvio {len(items)}: {response.content!r}"
        )

    candidates = []
    for item in items:
        if not isinstance(item, dict) or not all(k in item for k in ("statement", "code", "expected_answer")):
            raise ExerciseGenerationError(f"candidato con forma invalida: {item!r}")
        code_blocks = [
            ExerciseCodeBlock(file=c.get("file"), code=c.get("code", ""))
            for c in item["code"]
            if isinstance(c, dict) and isinstance(c.get("code"), str)
        ]
        candidates.append(
            CandidateExercise(
                type=exercise_type,
                statement=str(item["statement"]),
                code=code_blocks,
                expected_answer=str(item["expected_answer"]),
            )
        )
    return candidates


def _parse_json(raw: str, *, expect: type):
    """Identico a `_parse_json` del agente de codigo: tolera que el modelo
    envuelva la respuesta en una valla de markdown a pesar de que el
    prompt pide JSON puro."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ExerciseGenerationError(f"el modelo no devolvio JSON valido: {raw!r}") from exc
    if not isinstance(data, expect):
        raise ExerciseGenerationError(f"se esperaba un {expect.__name__}, se recibio: {raw!r}")
    return data
