"""Logica de negocio del agente revisor, separada del transporte A2A.

Una sola llamada al modelo logico `reviewer` via LiteLLM: recibe el
enunciado, la respuesta del alumno, y el verdict+justification que
propuso el agente evaluador, y devuelve una justificacion revisada (que
puede confirmar la original o corregirla). El `verdict` no se le pide de
vuelta -- decision explicita de design.md: el que persiste es siempre el
del evaluador."""

import json
import logging

from app.llm import build_reviewer_model
from app.models import ReviewResult
from app.tracing import litellm_trace_metadata

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Eres un asistente que revisa la justificacion que otro modelo (el "
    "evaluador) ha propuesto para el veredicto de la respuesta de un "
    "alumno a un ejercicio. Se te da el enunciado, la respuesta del "
    "alumno, el veredicto ya decidido (correct/incomplete/incorrect, no "
    "puedes cambiarlo) y la justificacion propuesta.\n\n"
    "Tu trabajo es devolver la MEJOR version de esa justificacion: "
    "confirmala si ya es precisa y coherente con el veredicto, o "
    "corrigela si es vaga, incorrecta, o no coherente con el veredicto "
    "dado.\n\n"
    "Responde EXCLUSIVAMENTE con un objeto JSON con un unico campo: "
    '"justification" (en español, la version final).'
)


class ReviewError(RuntimeError):
    """El modelo no devolvio una revision valida (JSON invalido, campo vacio, etc.)."""


async def review_justification(
    statement: str,
    student_answer: str,
    verdict: str,
    justification: str,
    trace_id: str | None = None,
) -> ReviewResult:
    model = build_reviewer_model()

    human_prompt = (
        f"### Enunciado\n{statement}\n\n"
        f"### Respuesta del alumno\n{student_answer}\n\n"
        f"### Veredicto ya decidido\n{verdict}\n\n"
        f"### Justificacion propuesta por el evaluador\n{justification}"
    )

    response = await model.ainvoke(
        [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": human_prompt},
        ],
        extra_body=litellm_trace_metadata(trace_id),
    )
    item = _parse_json(response.content, expect=dict)

    reviewed = item.get("justification")
    if not isinstance(reviewed, str) or not reviewed.strip():
        raise ReviewError(f"justification debe ser un texto no vacio, se recibio: {reviewed!r}")

    return ReviewResult(justification=reviewed)


def _parse_json(raw: str, *, expect: type):
    """Identico a `_parse_json` del agente evaluador: tolera que el
    modelo envuelva la respuesta en una valla de markdown."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ReviewError(f"el modelo no devolvio JSON valido: {raw!r}") from exc
    if not isinstance(data, expect):
        raise ReviewError(f"se esperaba un {expect.__name__}, se recibio: {raw!r}")
    return data
