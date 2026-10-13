"""Resolucion del commit HEAD de un repositorio (tarea 3.2).

Lo usa el orquestador para fijar el `commit_sha` una sola vez al iniciar
una generacion con repositorio (requisito "Commit fijado por generacion"
de `specs/github-repo-access/spec.md`), antes de llamar al agente de
codigo. Usa el mismo token de instalacion que el resto de la App (ver
`app/github_app.py`).
"""

import httpx

from app.github_app import GitHubAppError, get_github_app_client

GITHUB_API_BASE = "https://api.github.com"


class CommitResolutionError(RuntimeError):
    """No se pudo resolver el commit HEAD del repositorio."""


async def resolve_head_commit(owner: str, repo: str) -> str:
    try:
        token = await get_github_app_client().get_installation_token(owner, repo)
    except GitHubAppError as exc:
        raise CommitResolutionError(str(exc)) from exc

    async with httpx.AsyncClient(base_url=GITHUB_API_BASE, timeout=10.0) as http_client:
        response = await http_client.get(
            f"/repos/{owner}/{repo}/commits/HEAD",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
        )
    if response.status_code == 404:
        raise CommitResolutionError(f"el repositorio {owner}/{repo} no existe o no es accesible")
    if response.status_code >= 400:
        raise CommitResolutionError(
            f"no se pudo resolver el commit HEAD de {owner}/{repo}: {response.status_code} {response.text}"
        )
    return response.json()["sha"]
