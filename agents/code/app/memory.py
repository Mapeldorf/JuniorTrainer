"""Memoria larga del agente de codigo: cache de analisis por repo+tecnologias.

Requisitos de `specs/agent-memory/spec.md`:
  - "El agente de codigo no relee el mismo repositorio"
  - "Un acierto de memoria no consume los limites de la tarea" (ficheros leidos)
  - "Una memoria caida no bloquea la generacion" (lectura Y escritura)
  - "La memoria no guarda datos de alumnos" (aqui no hay ninguno: solo
    resumenes y fragmentos de codigo del propio repositorio analizado)

Clave (decision en design.md "Contrato de entrada del agente de codigo"):
`sha256(repo_identity + "|" + tecnologias normalizadas)`, donde
`repo_identity` es `git rev-parse HEAD` + `git remote get-url origin`
cuando `repo_path` es un repo git (el caso real: la prueba de aceptacion
del grupo 8 usa el repo real de Pokemon); si no es un repo git, cae a usar
el propio `repo_path`. A diferencia del agente web (clave = solo
tecnologias), aqui la identidad del repo importa tanto como las
tecnologias: dos repos distintos con las mismas tecnologias NO deben
compartir cache. TTL: 30 dias, con refresco en cada lectura (igual que el
agente web).
"""

import hashlib
import logging
import subprocess
from dataclasses import asdict

from langgraph.store.base import TTLConfig
from langgraph.store.postgres import AsyncPostgresStore

from app.db import conn_string
from app.models import CodeFragment

logger = logging.getLogger(__name__)

_NAMESPACE = ("code_analysis",)
_TTL_MINUTES = 30 * 24 * 60  # 30 dias
_GIT_TIMEOUT_SECONDS = 5


def normalize_technologies(technologies: list[str]) -> str:
    return "|".join(sorted({t.strip().lower() for t in technologies if t.strip()}))


def _repo_identity(repo_path: str) -> str:
    """`git remote + commit` cuando `repo_path` es un repo git; si no (o si
    git no esta disponible, o no hay remoto `origin`), cae a usar el propio
    `repo_path` -- degradacion aceptable documentada en design.md, no es el
    camino principal de la spec."""
    try:
        commit = subprocess.run(
            ["git", "-C", repo_path, "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SECONDS,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return repo_path

    try:
        remote = subprocess.run(
            ["git", "-C", repo_path, "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_SECONDS,
            check=True,
        ).stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        remote = ""  # repo git sin remoto origin: el commit solo ya es identidad util

    return f"{remote}@{commit}"


def cache_key(repo_path: str, technologies: list[str]) -> str:
    raw = f"{_repo_identity(repo_path)}|{normalize_technologies(technologies)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _store_cm():
    return AsyncPostgresStore.from_conn_string(
        conn_string(),
        ttl=TTLConfig(default_ttl=_TTL_MINUTES, refresh_on_read=True, omit_expired=True),
    )


async def get_cached_analysis(repo_path: str, technologies: list[str]) -> dict | None:
    """Devuelve el analisis guardado (como dict) o None.

    Cualquier fallo (red, auth, lo que sea) se trata como "no habia nada
    guardado": nunca propaga la excepcion, para que una memoria caida no
    bloquee la generacion.
    """
    key = cache_key(repo_path, technologies)
    try:
        async with _store_cm() as store:
            await store.setup()
            item = await store.aget(_NAMESPACE, key)
    except Exception:
        logger.warning("fallo leyendo memoria larga del agente de codigo", exc_info=True)
        return None
    if item is None:
        logger.info("memoria larga: sin acierto para %r, se relee el repositorio", key)
        return None
    logger.info("memoria larga: acierto para %r, no se relee ningun fichero", key)
    return item.value


async def save_analysis(
    repo_path: str,
    technologies: list[str],
    summary: str,
    detected_technologies: list[str],
    fragments: list[CodeFragment],
) -> None:
    """Guarda el resultado. Un fallo aqui se ignora sin interrumpir la tarea."""
    key = cache_key(repo_path, technologies)
    value = {
        "summary": summary,
        "technologies": detected_technologies,
        "fragments": [asdict(f) for f in fragments],
    }
    try:
        async with _store_cm() as store:
            await store.setup()
            await store.aput(_NAMESPACE, key, value)
    except Exception:
        logger.warning("fallo escribiendo memoria larga del agente de codigo", exc_info=True)
