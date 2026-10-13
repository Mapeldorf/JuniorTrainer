"""Extrae `owner`, `repo`, `commit_sha` y `technologies` de un mensaje A2A
entrante (change `acceso-repo-github-tool`, sustituye a `repo_path`).

Contrato de entrada: parte de datos
`{"owner": "...", "repo": "...", "commit_sha": "...", "technologies": [...]}`,
igual de forma que `parse_technologies` en `agents/web/app/input.py` pero
con tres campos mas. El orquestador (backend) ya valida y resuelve estos
tres valores antes de llamar a este agente (ver
`backend/app/schemas/generation.py`, `backend/app/github_client.py`); este
parseo solo exige que lleguen, no los vuelve a validar.
"""

from a2a.helpers.proto_helpers import get_data_parts
from a2a.types import Message


class InvalidCodeAgentInput(ValueError):
    """El mensaje no trae `owner`, `repo`, `commit_sha` o `technologies` validos."""


def parse_repo_input(message: Message) -> tuple[str, str, str, list[str]]:
    for data in get_data_parts(message.parts):
        if not isinstance(data, dict):
            continue
        owner = data.get("owner")
        repo = data.get("repo")
        commit_sha = data.get("commit_sha")
        technologies = data.get("technologies")
        if (
            isinstance(owner, str)
            and owner.strip()
            and isinstance(repo, str)
            and repo.strip()
            and isinstance(commit_sha, str)
            and commit_sha.strip()
            and isinstance(technologies, list)
        ):
            return owner.strip(), repo.strip(), commit_sha.strip(), _normalize([str(t) for t in technologies])
    raise InvalidCodeAgentInput(
        "se necesita una parte de datos con owner (str), repo (str), "
        "commit_sha (str) y technologies (list[str])"
    )


def _normalize(items: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for item in items:
        value = item.strip()
        if value and value not in seen:
            seen[value] = None
    return list(seen)
