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
  - 5.5: `trace_id` opcional que se reenvia a LiteLLM (ver
    app/tracing.py), igual que en los otros dos agentes.

Change `ejercicios-nivel-junior` (ver design.md, decisiones 1-3): el
prompt pide nivel junior recien incorporado, un unico concepto por
candidato y codigo de apoyo acotado; el enunciado se limita a
`_MAX_STATEMENT_WORDS` palabras, garantizado en codigo (no solo en el
prompt) con un unico reintento correctivo antes de fallar la tarea.
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
    "desarrolladores junior recien incorporados a un proyecto. Se te da: "
    "el tipo de ejercicio ('knowledge' = pregunta de conocimiento, sin "
    "necesidad de depurar nada; 'debug' = un fragmento de codigo con un "
    "fallo introducido a proposito que el alumno debe encontrar y "
    "corregir), el numero exacto de candidatos pedidos, un resumen de "
    "documentacion de las tecnologias relevantes, un resumen y "
    "fragmentos de un repositorio real (si los hay), y una lista de "
    "enunciados YA PROPUESTOS antes para este mismo tipo que NO debes "
    "repetir (ni el mismo tema con otras palabras).\n\n"
    "Cada candidato SHALL tratar UN UNICO concepto y SHALL ser "
    "resoluble solo con el enunciado y el codigo de apoyo que entregas "
    "-- nunca pidas redisenar, refactorizar, ni cambiar o recorrer mas "
    "de un fichero. No es un ejercicio de arquitectura ni de diseno: es "
    "una pregunta puntual o un fallo puntual que un junior recien "
    "incorporado resuelve leyendo solo lo que se le da. En 'knowledge', "
    "NO encadenes varias preguntas en un mismo enunciado (nada de '...y "
    "que diferencia hay entre... y que funcion se ejecuta...'): elige "
    "UN SOLO aspecto concreto y preguntalo directamente, sin comparar "
    "dos elementos ni pedir varias explicaciones a la vez.\n\n"
    "Responde EXCLUSIVAMENTE con un array JSON de EXACTAMENTE el numero "
    "de candidatos pedido. Cada candidato es un objeto con tres campos:\n"
    '- "statement": el enunciado, en español, de COMO MAXIMO 50 '
    "PALABRAS (el codigo de apoyo y la respuesta esperada no cuentan "
    "para ese limite). Claro, autocontenido, sobre el unico concepto "
    "del candidato.\n"
    '- "code": array de objetos {"file": ruta o null, "code": texto}, '
    "con COMO MUCHO UN fragmento breve de UN solo fichero -- para "
    "'debug' DEBE incluir EXACTAMENTE UN fallo ya introducido en el "
    "codigo; para 'knowledge' puede quedar vacio si el enunciado no "
    "necesita codigo de apoyo.\n"
    '- "expected_answer": la respuesta esperada: para \'debug\', que '
    "corregir y por que; para 'knowledge', la respuesta a la "
    "pregunta.\n\n"
    "No inventes tecnologias que no esten en los resumenes "
    "proporcionados."
)

# Garantia en codigo del limite de palabras del enunciado (design.md
# decision 1-2): el prompt ya lo pide, pero esta constante es lo que
# realmente lo hace cumplir -- ver `_statements_over_limit` y el
# reintento en `_draft_candidates`.
_MAX_STATEMENT_WORDS = 50


class ExerciseGenerationError(RuntimeError):
    """El modelo no devolvio candidatos validos (JSON invalido, numero incorrecto, limite de palabras incumplido tras el reintento, etc.)."""


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
    # (JSON invalido, numero incorrecto, limite de palabras tras el
    # reintento...), no hay enunciados nuevos que guardar -- y por tanto
    # ningun enunciado demasiado largo entra nunca en el historial
    # (design.md decision 3). Un fallo de escritura se ignora dentro de
    # save_statements().
    await save_statements(exercise_type, [c.statement for c in candidates])

    return ExerciseGenerationResult(
        candidates=candidates,
        memory_hit=bool(avoid_statements),
    )


def _statements_over_limit(statements: list[str]) -> list[tuple[str, int]]:
    """Enunciados que superan `_MAX_STATEMENT_WORDS`, con su recuento.

    Cuenta como palabra cada secuencia de caracteres separada por
    espacios en blanco (`str.split()` sin argumentos ya colapsa saltos
    de linea y espacios dobles/multiples), igual que especifica el
    requisito "Longitud maxima del enunciado".
    """
    over = []
    for statement in statements:
        word_count = len(statement.split())
        if word_count > _MAX_STATEMENT_WORDS:
            over.append((statement, word_count))
    return over


def _overlong_retry_notice(overlong: list[tuple[str, int]]) -> str:
    lines = "\n".join(
        f'- "{statement}" -- {word_count} palabras ({word_count - _MAX_STATEMENT_WORDS} de mas)'
        for statement, word_count in overlong
    )
    return (
        f"De los candidatos que acabas de devolver, estos enunciados superan "
        f"el limite de {_MAX_STATEMENT_WORDS} palabras:\n{lines}\n\n"
        "Vuelve a responder con el array JSON completo (los mismos candidatos, "
        f"el mismo numero), acortando esos enunciados a {_MAX_STATEMENT_WORDS} "
        "palabras o menos sin perder el sentido. No cambies los candidatos que "
        "ya cumplian el limite."
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

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": human_prompt},
    ]

    candidates, raw_content = await _invoke_and_parse(model, messages, exercise_type, count, trace_id)

    # Garantia en codigo del limite de palabras (design.md decision 2):
    # un unico reintento correctivo sobre la peticion COMPLETA (no solo
    # el candidato que se pasaba), para no mezclar candidatos de dos
    # respuestas distintas y reabrir la posibilidad de temas repetidos.
    overlong = _statements_over_limit([c.statement for c in candidates])
    if overlong:
        logger.warning(
            "enunciados por encima del limite de %d palabras, reintentando una vez: %r",
            _MAX_STATEMENT_WORDS,
            overlong,
        )
        messages = [
            *messages,
            {"role": "assistant", "content": raw_content},
            {"role": "user", "content": _overlong_retry_notice(overlong)},
        ]
        candidates, raw_content = await _invoke_and_parse(model, messages, exercise_type, count, trace_id)

        overlong = _statements_over_limit([c.statement for c in candidates])
        if overlong:
            raise ExerciseGenerationError(
                f"tras el reintento, siguen pasandose del limite de {_MAX_STATEMENT_WORDS} "
                f"palabras: {overlong!r}"
            )

    return candidates


async def _invoke_and_parse(
    model,
    messages: list[dict],
    exercise_type: str,
    count: int,
    trace_id: str | None,
) -> tuple[list[CandidateExercise], str]:
    """Una llamada al modelo + parseo de su respuesta en `count` candidatos.

    Factorizado para poder llamarse dos veces (intento inicial y, si
    algun enunciado se pasa del limite, el reintento correctivo de
    `_draft_candidates`). Devuelve tambien el contenido crudo de la
    respuesta, para poder anadirlo como turno `assistant` en el
    reintento.
    """
    response = await model.ainvoke(messages, extra_body=litellm_trace_metadata(trace_id))
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
    return candidates, response.content


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
