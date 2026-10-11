"""Extrae la lista de tecnologias de un mensaje A2A entrante.

Acepta dos formas, para que tanto un orquestador programatico como una
llamada manual de depuracion funcionen igual:
  - Parte de datos: {"technologies": ["React", "FastAPI"]}
  - Parte de texto: "React, FastAPI" (separado por comas o saltos de linea)
"""

from a2a.helpers.proto_helpers import get_data_parts, get_text_parts
from a2a.types import Message


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
    return list(seen)
