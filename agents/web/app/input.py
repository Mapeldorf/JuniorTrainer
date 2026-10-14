"""Extrae la lista de tecnologias de un mensaje A2A entrante.

Acepta dos formas, para que tanto un orquestador programatico como una
llamada manual de depuracion funcionen igual:
  - Parte de datos: {"technologies": ["React", "FastAPI"]}
  - Parte de texto: "React, FastAPI" (separado por comas o saltos de linea)

Limite de numero/longitud (change `validacion-entrada-agentes`): misma
revalidacion independiente que ya hace `agents/exercises` con `count`,
aunque `backend/app/schemas/generation.py` ya aplica el mismo limite antes
de llamar a este agente -- no se depende de que el unico llamador posible
siga siendo siempre correcto. `_MAX_TECHNOLOGIES`/`_MAX_TECHNOLOGY_LENGTH`
son la copia de este agente del mismo valor que usa el backend.
"""

from a2a.helpers.proto_helpers import get_data_parts, get_text_parts
from a2a.types import Message

_MAX_TECHNOLOGIES = 15
_MAX_TECHNOLOGY_LENGTH = 60


class InvalidTechnologiesInput(ValueError):
    """La lista de tecnologias supera el numero o la longitud maxima permitida."""


def parse_technologies(message: Message) -> list[str]:
    for data in get_data_parts(message.parts):
        if isinstance(data, dict) and isinstance(data.get("technologies"), list):
            return _normalize([str(t) for t in data["technologies"]])

    text = "\n".join(get_text_parts(message.parts))
    if not text.strip():
        return []
    raw = text.replace("\n", ",").split(",")
    return _normalize(raw)


def _normalize(items: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for item in items:
        value = item.strip()
        if value and value not in seen:
            seen[value] = None
    result = list(seen)
    if len(result) > _MAX_TECHNOLOGIES:
        raise InvalidTechnologiesInput(f"no se permiten mas de {_MAX_TECHNOLOGIES} tecnologias por peticion")
    too_long = [t for t in result if len(t) > _MAX_TECHNOLOGY_LENGTH]
    if too_long:
        raise InvalidTechnologiesInput(
            f"cada tecnologia debe tener como maximo {_MAX_TECHNOLOGY_LENGTH} caracteres: {too_long!r}"
        )
    return result
