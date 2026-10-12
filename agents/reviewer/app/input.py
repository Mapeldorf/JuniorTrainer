"""Extrae `statement`, `student_answer`, `verdict` y `justification` de un
mensaje A2A entrante.

Contrato (ver design.md del change `valoracion-respuestas`, "Contrato de
entrada/salida de los agentes"): parte de datos
`{"statement": str, "student_answer": str, "verdict": "correct"|"incomplete"|"incorrect", "justification": str}`.
`verdict` y `justification` son los que propuso el agente evaluador; este
agente los recibe para dar contexto a la revision, pero solo devuelve una
`justification` (revisada) -- nunca un `verdict` nuevo.
"""

from a2a.helpers.proto_helpers import get_data_parts
from a2a.types import Message

_VALID_VERDICTS = {"correct", "incomplete", "incorrect"}


class InvalidReviewerInput(ValueError):
    """El mensaje no trae una entrada valida para el agente revisor."""


def parse_review_request(message: Message) -> tuple[str, str, str, str]:
    for data in get_data_parts(message.parts):
        if not isinstance(data, dict):
            continue

        statement = data.get("statement")
        if not isinstance(statement, str) or not statement.strip():
            raise InvalidReviewerInput(f"statement debe ser un texto no vacio, se recibio: {statement!r}")

        student_answer = data.get("student_answer")
        if not isinstance(student_answer, str) or not student_answer.strip():
            raise InvalidReviewerInput(
                f"student_answer debe ser un texto no vacio, se recibio: {student_answer!r}"
            )

        verdict = data.get("verdict")
        if verdict not in _VALID_VERDICTS:
            raise InvalidReviewerInput(f"verdict debe ser uno de {_VALID_VERDICTS}, se recibio: {verdict!r}")

        justification = data.get("justification")
        if not isinstance(justification, str) or not justification.strip():
            raise InvalidReviewerInput(
                f"justification debe ser un texto no vacio, se recibio: {justification!r}"
            )

        return statement, student_answer, verdict, justification

    raise InvalidReviewerInput(
        "se necesita una parte de datos con statement, student_answer, verdict y justification"
    )
