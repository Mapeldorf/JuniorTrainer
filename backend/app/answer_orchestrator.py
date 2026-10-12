"""Orquestacion sincrona de una evaluacion (grupo 5 del change
`valoracion-respuestas`): llama al agente evaluador y despues al revisor
por A2A, DENTRO de la misma peticion HTTP que envia la respuesta -- a
diferencia de `app/orchestrator.py` (que corre en `BackgroundTasks`),
`answer.verdict` es `NOT NULL` en el esquema, asi que la fila no puede
insertarse sin saberlo ya (ver design.md - Context/Decisions,
"Orquestacion de la evaluacion").

El `verdict` que persiste SIEMPRE es el del evaluador: el revisor solo
puede ajustar la `justification` (decision explicita de design.md: evita
que dos agentes compitan por la misma decision)."""

from app.a2a_client import A2ATaskError, send_a2a_task
from app.config import get_settings


class AnswerEvaluationFailed(RuntimeError):
    """Fallo irrecuperable evaluando una respuesta (evaluador o revisor
    inalcanzables, o respuesta sin los campos esperados): no se persiste
    nada en `answer` (requisito "La evaluacion no puede completarse",
    tarea 5.3 -- esta funcion no toca la base de datos, asi que el
    llamador no tiene nada que deshacer)."""


async def evaluate_answer(
    statement: str,
    code: list,
    expected_answer: str | None,
    student_answer: str,
    trace_id: str,
) -> tuple[str, str]:
    """Evalua y revisa una respuesta; devuelve `(verdict, justification)`
    ya listos para persistir. Lanza `AnswerEvaluationFailed` si cualquiera
    de los dos agentes falla o responde sin los campos esperados."""
    settings = get_settings()

    try:
        evaluation = await send_a2a_task(
            settings.agent_evaluator_url,
            {
                "statement": statement,
                "code": code,
                "expected_answer": expected_answer,
                "student_answer": student_answer,
            },
            trace_id=trace_id,
        )
    except A2ATaskError as exc:
        raise AnswerEvaluationFailed(f"el agente evaluador ha fallado: {exc}") from exc

    verdict = evaluation.get("verdict")
    justification = evaluation.get("justification")
    if verdict not in ("correct", "incomplete", "incorrect") or not justification:
        raise AnswerEvaluationFailed(
            f"el agente evaluador respondio sin un verdict/justification validos: {evaluation!r}"
        )

    try:
        review = await send_a2a_task(
            settings.agent_reviewer_url,
            {
                "statement": statement,
                "student_answer": student_answer,
                "verdict": verdict,
                "justification": justification,
            },
            trace_id=trace_id,
        )
    except A2ATaskError as exc:
        raise AnswerEvaluationFailed(f"el agente revisor ha fallado: {exc}") from exc

    reviewed_justification = review.get("justification")
    if not reviewed_justification:
        raise AnswerEvaluationFailed(f"el agente revisor respondio sin justification: {review!r}")

    return verdict, reviewed_justification
