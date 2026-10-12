"""Logica de negocio del agente evaluador, separada del transporte A2A.

Una sola llamada al modelo logico `evaluator` via LiteLLM: recibe el
enunciado, el codigo de apoyo y la respuesta esperada del ejercicio (de
la copia de la asignacion, nunca del `exercise` original -- eso lo
decide quien llama, no este agente) junto con la respuesta del alumno, y
devuelve un `verdict` (`correct`/`incomplete`/`incorrect`) con su
justificacion. Ver design.md del change `valoracion-respuestas`,
"Contrato de entrada/salida de los agentes"."""

import json
import logging

from app.llm import build_evaluator_model
from app.models import EvaluationResult
from app.tracing import litellm_trace_metadata

logger = logging.getLogger(__name__)

_VALID_VERDICTS = {"correct", "incomplete", "incorrect"}

_SYSTEM_PROMPT = (
    "Eres un asistente que evalua la respuesta de un alumno a un "
    "ejercicio de programacion. Se te da el enunciado, codigo de apoyo "
    "(si lo hay), la respuesta esperada (si se conoce) y la respuesta "
    "real del alumno.\n\n"
    "Responde EXCLUSIVAMENTE con un objeto JSON con dos campos: "
    '"verdict" (uno de exactamente estos tres valores: "correct" si la '
    'respuesta es correcta y completa, "incomplete" si va en la '
    'direccion correcta pero le falta algo relevante, "incorrect" si es '
    'equivocada) y "justification" (en español, explicando con '
    "precision por que mereces ese veredicto, citando que falta o que "
    "esta mal cuando no sea \"correct\")."
)


class EvaluationError(RuntimeError):
    """El modelo no devolvio una evaluacion valida (JSON invalido, verdict fuera de rango, etc.)."""


async def evaluate_answer(
    statement: str,
    code: list,
    expected_answer: str | None,
    student_answer: str,
    trace_id: str | None = None,
) -> EvaluationResult:
    model = build_evaluator_model()

    blocks = [f"### Enunciado\n{statement}"]
    if code:
        code_lines = "\n".join(f"- {c.get('file')}:\n  {c.get('code')!r}" for c in code if isinstance(c, dict))
        if code_lines:
            blocks.append(f"### Codigo de apoyo\n{code_lines}")
    if expected_answer:
        blocks.append(f"### Respuesta esperada\n{expected_answer}")
    else:
        blocks.append("### Respuesta esperada\n(no se registro una respuesta esperada para este ejercicio)")
    blocks.append(f"### Respuesta del alumno\n{student_answer}")

    human_prompt = "\n\n".join(blocks)

    response = await model.ainvoke(
        [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": human_prompt},
        ],
        extra_body=litellm_trace_metadata(trace_id),
    )
    item = _parse_json(response.content, expect=dict)

    verdict = item.get("verdict")
    if verdict not in _VALID_VERDICTS:
        raise EvaluationError(f"verdict debe ser uno de {_VALID_VERDICTS}, se recibio: {verdict!r}")

    justification = item.get("justification")
    if not isinstance(justification, str) or not justification.strip():
        raise EvaluationError(f"justification debe ser un texto no vacio, se recibio: {justification!r}")

    return EvaluationResult(verdict=verdict, justification=justification)


def _parse_json(raw: str, *, expect: type):
    """Identico a `_parse_json` del agente de ejercicios: tolera que el
    modelo envuelva la respuesta en una valla de markdown a pesar de que
    el prompt pide JSON puro."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EvaluationError(f"el modelo no devolvio JSON valido: {raw!r}") from exc
    if not isinstance(data, expect):
        raise EvaluationError(f"se esperaba un {expect.__name__}, se recibio: {raw!r}")
    return data
