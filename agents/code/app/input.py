"""Extrae `owner`, `repo`, `commit_sha` y `technologies` de un mensaje A2A
entrante (change `acceso-repo-github-tool`, sustituye a `repo_path`).

Contrato de entrada: parte de datos
`{"owner": "...", "repo": "...", "commit_sha": "...", "technologies": [...]}`,
igual de forma que `parse_technologies` en `agents/web/app/input.py` pero
con tres campos mas. El orquestador (backend) ya valida y resuelve estos
tres valores antes de llamar a este agente (ver
`backend/app/schemas/generation.py`, `backend/app/github_client.py`); este
agente los revalida igualmente antes de usarlos en cualquier llamada a la
API de GitHub (defensa en profundidad, change `validacion-entrada-agentes`
-- el mismo patron que ya aplica `agents/exercises` con `count`), sin
depender de que el unico llamador posible siga siendo siempre correcto.
"""

from a2a.helpers.proto_helpers import get_data_parts
from a2a.types import Message

from app.github_ref import InvalidGitHubRef, validate_owner_or_repo


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
            try:
                owner = validate_owner_or_repo(owner, field="owner")
                repo = validate_owner_or_repo(repo, field="repo")
            except InvalidGitHubRef as exc:
                raise InvalidCodeAgentInput(str(exc)) from exc
            return owner, repo, commit_sha.strip(), _normalize([str(t) for t in technologies])
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
