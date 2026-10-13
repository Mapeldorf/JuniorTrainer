"""Herramientas de solo lectura del agente de codigo contra la API de
GitHub (tarea 4.1), sustituyendo a `app/tools/filesystem.py` (que leia un
`repo_path` local -- ya eliminado, ver tarea 4.6).

Requisitos de `specs/github-repo-access/spec.md`:
  - "El repositorio nunca se descarga ni se almacena": todo el contenido
    llega por llamadas HTTP bajo demanda, nunca se escribe a disco.
  - "Listado del arbol en una sola llamada": `list_files` usa la Git Trees
    API recursiva en vez de recorrer directorios uno a uno.
  - "Host de la API fijo, sin URLs de usuario": toda llamada va contra
    `GITHUB_API_BASE`, construida solo con `owner`/`repo`/`commit_sha`
    (ya validados antes de llegar aqui, ver `app/input.py`), nunca con una
    URL que venga del exterior.

`FileBudget`/`FileEntry` mantienen la misma forma que la version local
para que `app/service.py` no tenga que cambiar su logica de negocio, solo
de donde viene el contenido.
"""

import base64
from dataclasses import dataclass

import httpx

from app.github_app import get_github_app_client

GITHUB_API_BASE = "https://api.github.com"

# Mismos directorios que la version local (app/tools/filesystem.py):
# nunca interesan para generar ejercicios y en un repo real pueden ser
# enormes.
_IGNORED_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    "dist",
    "build",
}


class GitHubRepoError(RuntimeError):
    """Fallo listando el arbol o leyendo el contenido de un repositorio."""


class FileBudgetExceeded(RuntimeError):
    """Se intento leer un fichero por encima del limite de la tarea."""


class FileBudget:
    """Cuenta los ficheros leidos en una tarea A2A; agota a los 10 (por diseno)."""

    def __init__(self, max_calls: int = 10) -> None:
        self.max_calls = max_calls
        self.used = 0

    def consume(self) -> None:
        if self.used >= self.max_calls:
            raise FileBudgetExceeded(
                f"se alcanzo el limite de {self.max_calls} ficheros leidos de esta tarea"
            )
        self.used += 1


@dataclass
class FileEntry:
    path: str  # relativa, POSIX, igual que la version local
    size_bytes: int


def _is_ignored(path: str) -> bool:
    return any(part in _IGNORED_DIRS for part in path.split("/"))


async def _authorized_headers(owner: str, repo: str) -> dict[str, str]:
    token = await get_github_app_client().get_installation_token(owner, repo)
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}


async def list_files(owner: str, repo: str, commit_sha: str) -> list[FileEntry]:
    """Listado completo de ficheros del repositorio en `commit_sha`, en
    una sola llamada a la Git Trees API recursiva (requisito "Listado del
    arbol en una sola llamada"), filtrando `_IGNORED_DIRS`."""
    headers = await _authorized_headers(owner, repo)
    async with httpx.AsyncClient(base_url=GITHUB_API_BASE, timeout=20.0) as http_client:
        response = await http_client.get(
            f"/repos/{owner}/{repo}/git/trees/{commit_sha}",
            params={"recursive": "1"},
            headers=headers,
        )
    if response.status_code >= 400:
        raise GitHubRepoError(
            f"no se pudo listar el arbol de {owner}/{repo}@{commit_sha}: "
            f"{response.status_code} {response.text}"
        )
    data = response.json()
    entries = [
        FileEntry(path=item["path"], size_bytes=item.get("size") or 0)
        for item in data.get("tree", [])
        if item.get("type") == "blob" and not _is_ignored(item["path"])
    ]
    return sorted(entries, key=lambda e: e.path)


async def read_file(owner: str, repo: str, commit_sha: str, path: str, budget: FileBudget) -> str:
    """Lee el contenido de texto de `path` en `commit_sha`, descontando del
    `budget` ANTES de intentar leer (igual que la version local): si el
    budget ya esta agotado, no se hace ninguna llamada; si la lectura
    falla despues de descontar, el intento igualmente cuenta como
    gastado.

    Usa la Contents API (devuelve el contenido en base64); si el fichero
    supera su limite de tamano (no trae "content"), cae a la Blobs API
    con el `sha` que la propia respuesta de Contents ya incluye.
    """
    budget.consume()
    headers = await _authorized_headers(owner, repo)
    async with httpx.AsyncClient(base_url=GITHUB_API_BASE, timeout=20.0) as http_client:
        response = await http_client.get(
            f"/repos/{owner}/{repo}/contents/{path}",
            params={"ref": commit_sha},
            headers=headers,
        )
        if response.status_code == 404:
            raise FileNotFoundError(f"{path!r} no existe en {owner}/{repo}@{commit_sha}")
        if response.status_code >= 400:
            raise GitHubRepoError(
                f"no se pudo leer {path!r} de {owner}/{repo}@{commit_sha}: "
                f"{response.status_code} {response.text}"
            )
        data = response.json()
        if isinstance(data, list):
            raise GitHubRepoError(f"{path!r} es un directorio, no un fichero")

        encoded = data.get("content")
        if encoded is not None:
            return base64.b64decode(encoded).decode("utf-8", errors="replace")

        blob_response = await http_client.get(
            f"/repos/{owner}/{repo}/git/blobs/{data['sha']}",
            headers=headers,
        )
    if blob_response.status_code >= 400:
        raise GitHubRepoError(
            f"no se pudo leer el blob de {path!r} de {owner}/{repo}@{commit_sha}: "
            f"{blob_response.status_code} {blob_response.text}"
        )
    blob_data = blob_response.json()
    if blob_data.get("encoding") != "base64":
        raise GitHubRepoError(f"codificacion inesperada leyendo el blob de {path!r}")
    return base64.b64decode(blob_data["content"]).decode("utf-8", errors="replace")
