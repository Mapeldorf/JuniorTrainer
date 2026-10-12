"""Extrae `statement`, `code`, `expected_answer` y `student_answer` de un
mensaje A2A entrante.

Contrato (ver design.md del change `valoracion-respuestas`, "Contrato de
entrada/salida de los agentes"): parte de datos
`{"statement": str, "code": [...], "expected_answer": str|null, "student_answer": str}`.
`code` se reenvia tal cual desde `assignment_exercise`/`exercise`
(lista de bloques `{"file": ..., "code": ...}`); es opaco para este
modulo, igual que `web_result`/`code_result` lo son para el agente de
ejercicios -- solo se exige que sea una lista.
"""

from a2a.helpers.proto_helpers import get_data_parts
from a2a.types import Message


class InvalidEvaluatorInput(ValueError):
    """El mensaje no trae una entrada valida para el agente evaluador."""


def parse_evaluation_request(message: Message) -> tuple[str, list, str | None, str]:
    for data in get_data_parts(message.parts):
        if not isinstance(data, dict):
            continue

        statement = data.get("statement")
        if not isinstance(statement, str) or not statement.strip():
            raise InvalidEvaluatorInput(f"statement debe ser un texto no vacio, se recibio: {statement!r}")

        code = data.get("code", [])
        if not isinstance(code, list):
            raise InvalidEvaluatorInput(f"code debe ser una lista, se recibio: {code!r}")

        expected_answer = data.get("expected_answer")
        if expected_answer is not None and not isinstance(expected_answer, str):
            raise InvalidEvaluatorInput(
                f"expected_answer debe ser un texto o null, se recibio: {expected_answer!r}"
            )

        student_answer = data.get("student_answer")
        if not isinstance(student_answer, str) or not student_answer.strip():
            raise InvalidEvaluatorInput(
                f"student_answer debe ser un texto no vacio, se recibio: {student_answer!r}"
            )

        return statement, code, expected_answer, student_answer

    raise InvalidEvaluatorInput(
        "se necesita una parte de datos con statement, code, expected_answer y student_answer"
    )
