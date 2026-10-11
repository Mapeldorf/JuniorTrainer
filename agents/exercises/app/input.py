"""Extrae `exercise_type`, `count`, `web_result` y `code_result` de un
mensaje A2A entrante.

Contrato documentado en design.md "Contrato de entrada/salida del agente
de ejercicios": parte de datos
`{"exercise_type": "knowledge"|"debug", "count": 1-5, "web_result": {...}|null, "code_result": {...}|null}`.
`web_result`/`code_result` son el `dataclasses.asdict()` tal cual de
`WebResearchResult`/`CodeAnalysisResult` que produce cada agente, reenviados
sin transformar por el orquestador -- aqui no se valida su forma interna
(son opacos para este agente hasta que `service.py` los use), solo que
sean un dict o None. No hay forma de texto libre equivalente (no tiene
un formato natural en texto), asi que solo se acepta la parte de datos.

`count` llega SIEMPRE como `float` (nunca `int`), aunque el llamador
mande un entero de verdad: la parte de datos viaja como protobuf
`Struct`, cuyo unico tipo numerico es `double` (descubierto verificando
este scaffold -- ver tasks.md 5.1). Se tolera igual que ya se tolera
`bool` (subclase de `int` en Python), exigiendo que sea un valor entero
exacto (`3.0` vale, `3.5` no) y convirtiendolo a `int` antes de devolverlo.
"""

from a2a.helpers.proto_helpers import get_data_parts
from a2a.types import Message

_VALID_TYPES = {"knowledge", "debug"}


class InvalidExercisesAgentInput(ValueError):
    """El mensaje no trae una entrada valida para el agente de ejercicios."""


def parse_exercise_request(message: Message) -> tuple[str, int, dict | None, dict | None]:
    for data in get_data_parts(message.parts):
        if not isinstance(data, dict):
            continue

        exercise_type = data.get("exercise_type")
        if exercise_type not in _VALID_TYPES:
            raise InvalidExercisesAgentInput(
                f"exercise_type debe ser 'knowledge' o 'debug', se recibio: {exercise_type!r}"
            )

        count_raw = data.get("count")
        count = _as_exact_int(count_raw)
        if count is None or not (1 <= count <= 5):
            raise InvalidExercisesAgentInput(f"count debe ser un entero entre 1 y 5, se recibio: {count_raw!r}")

        web_result = data.get("web_result")
        code_result = data.get("code_result")
        if web_result is not None and not isinstance(web_result, dict):
            raise InvalidExercisesAgentInput(f"web_result debe ser un objeto o null, se recibio: {web_result!r}")
        if code_result is not None and not isinstance(code_result, dict):
            raise InvalidExercisesAgentInput(f"code_result debe ser un objeto o null, se recibio: {code_result!r}")
        if web_result is None and code_result is None:
            raise InvalidExercisesAgentInput(
                "se necesita al menos web_result o code_result para generar ejercicios"
            )

        return exercise_type, count, web_result, code_result

    raise InvalidExercisesAgentInput(
        "se necesita una parte de datos con exercise_type, count y web_result/code_result"
    )


def _as_exact_int(value: object) -> int | None:
    """int real, o float/bool con valor entero exacto; None si no aplica."""
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None
