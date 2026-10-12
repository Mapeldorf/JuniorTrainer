"""Herramientas de solo lectura del agente de codigo: `list_files`/`read_file`.

Requisito de `proposal.md`: "lee el repo preparado con list_files/read_file,
solo lectura", limitadas a la carpeta del repo (contrato en design.md
"Contrato de entrada del agente de codigo"). `read_file` cuenta contra un
limite de 10 ficheros leidos por tarea (`FileBudget`, mismo patron que
`SearchBudget` del agente web en `tavily_search.py`).
"""

from dataclasses import dataclass
from pathlib import Path

# Directorios que nunca interesan para generar ejercicios y que en un repo
# real pueden ser enormes (dependencias, entornos virtuales...). list_files
# los salta siempre; no es configurable por tarea.
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


class PathEscapesRepo(ValueError):
    """La ruta pedida cae fuera de la carpeta del repo (`repo_path`)."""


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
    path: str  # relativa, POSIX, a repo_path
    size_bytes: int


def _resolve_within(repo_root: Path, relative_path: str) -> Path:
    """Resuelve `relative_path` dentro de `repo_root`, o lanza `PathEscapesRepo`.

    Dos formas de escapar, cubiertas por separado:
      - "../../etc/passwd": `Path.resolve()` normaliza los ".." y el
        resultado cae fuera de `repo_root` -- lo detecta `relative_to()`.
      - "/etc/passwd" (una ruta ABSOLUTA pasada como si fuera relativa):
        `Path("/repo") / "/etc/passwd"` da `/etc/passwd` -- en `pathlib`,
        unir con una ruta absoluta reemplaza el join entero en vez de
        concatenar. `relative_to()` tambien lo detectaria mas abajo, pero
        se rechaza antes explicitamente: es un caso distinto (un intento
        directo), no una coincidencia del resuelto de "..".
    """
    if Path(relative_path).is_absolute():
        raise PathEscapesRepo(f"ruta absoluta no permitida: {relative_path!r}")
    root = repo_root.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        raise PathEscapesRepo(f"{relative_path!r} cae fuera de la carpeta del repo") from None
    return candidate


def list_files(repo_path: str) -> list[FileEntry]:
    """Rutas relativas (POSIX) de todos los ficheros del repo, sin los
    directorios de `_IGNORED_DIRS`. Sin limite propio (el limite de 10 es
    solo para `read_file`): listar no lee contenido."""
    root = Path(repo_path).resolve()
    entries = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if any(part in _IGNORED_DIRS for part in relative.parts):
            continue
        entries.append(FileEntry(path=relative.as_posix(), size_bytes=path.stat().st_size))
    return sorted(entries, key=lambda e: e.path)


def read_file(repo_path: str, relative_path: str, budget: FileBudget) -> str:
    """Lee el contenido de texto de `relative_path`, dentro de `repo_path`.

    Descuenta del budget ANTES de intentar leer (igual que
    `tavily_search()`): si el budget ya esta agotado, no se toca el disco;
    si la lectura falla despues de descontar (fichero borrado entre medias,
    etc.), el intento igualmente cuenta como gastado.
    """
    candidate = _resolve_within(Path(repo_path), relative_path)
    budget.consume()
    return candidate.read_text(encoding="utf-8", errors="replace")
