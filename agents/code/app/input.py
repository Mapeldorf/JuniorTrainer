"""Extrae `repo_path` y `technologies` de un mensaje A2A entrante.

Contrato de entrada documentado en design.md "Contrato de entrada del
agente de codigo": parte de datos
`{"repo_path": "...", "technologies": [...]}`, igual de forma que
`parse_technologies` en `agents/web/app/input.py` pero con un campo mas.
No hay forma de texto libre equivalente (una ruta de repo no tiene un
formato natural en texto como las tecnologias), asi que solo se acepta
la parte de datos.
"""

from a2a.helpers.proto_helpers import get_data_parts
from a2a.types import Message


class InvalidCodeAgentInput(ValueError):
    """El mensaje no trae `repo_path` o `technologies` validos."""


def parse_repo_input(message: Message) -> tuple[str, list[str]]:
    for data in get_data_parts(message.parts):
        if not isinstance(data, dict):
            continue
        repo_path = data.get("repo_path")
        technologies = data.get("technologies")
        if isinstance(repo_path, str) and repo_path.strip() and isinstance(technologies, list):
            return repo_path.strip(), _normalize([str(t) for t in technologies])
    raise InvalidCodeAgentInput(
        "se necesita una parte de datos con repo_path (str) y technologies (list[str])"
    )


def _normalize(items: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for item in items:
        value = item.strip()
        if value and value not in seen:
            seen[value] = None
    return list(seen)
