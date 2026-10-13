"""Memoria larga del agente de codigo: cache de analisis por repo+tecnologias.

Requisitos de `specs/agent-memory/spec.md`:
  - "El agente de codigo no relee el mismo repositorio"
  - "Un acierto de memoria no consume los limites de la tarea" (ficheros leidos)
  - "Una memoria caida no bloquea la generacion" (lectura Y escritura)
  - "La memoria no guarda datos de alumnos" (aqui no hay ninguno: solo
    resumenes y fragmentos de codigo del propio repositorio analizado)

Clave: `sha256("{owner}/{repo}@{commit_sha}" + "|" + tecnologias
normalizadas)`. El change `acceso-repo-github-tool` simplifica esto
respecto a la version anterior: el commit ya llega resuelto por el
orquestador (una sola vez por generacion, ver
`backend/app/github_client.py`), asi que no hace falta inspeccionar
ningun `.git` local por subprocess -- `owner`/`repo`/`commit_sha` YA SON
la identidad del repositorio, sin fallback. Dos repos distintos con las
mismas tecnologias siguen sin compartir cache. TTL: 30 dias, con refresco
en cada lectura (igual que el agente web).
"""

import hashlib
import logging
from dataclasses import asdict

from langgraph.store.base import TTLConfig
from langgraph.store.postgres import AsyncPostgresStore

from app.db import conn_string
from app.models import CodeFragment

logger = logging.getLogger(__name__)

_NAMESPACE = ("code_analysis",)
_TTL_MINUTES = 30 * 24 * 60  # 30 dias


def normalize_technologies(technologies: list[str]) -> str:
    return "|".join(sorted({t.strip().lower() for t in technologies if t.strip()}))


def cache_key(owner: str, repo: str, commit_sha: str, technologies: list[str]) -> str:
    raw = f"{owner}/{repo}@{commit_sha}|{normalize_technologies(technologies)}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _store_cm():
    return AsyncPostgresStore.from_conn_string(
        conn_string(),
        ttl=TTLConfig(default_ttl=_TTL_MINUTES, refresh_on_read=True, omit_expired=True),
    )


async def get_cached_analysis(
    owner: str, repo: str, commit_sha: str, technologies: list[str]
) -> dict | None:
    """Devuelve el analisis guardado (como dict) o None.

    Cualquier fallo (red, auth, lo que sea) se trata como "no habia nada
    guardado": nunca propaga la excepcion, para que una memoria caida no
    bloquee la generacion.
    """
    key = cache_key(owner, repo, commit_sha, technologies)
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
    owner: str,
    repo: str,
    commit_sha: str,
    technologies: list[str],
    summary: str,
    detected_technologies: list[str],
    fragments: list[CodeFragment],
) -> None:
    """Guarda el resultado. Un fallo aqui se ignora sin interrumpir la tarea."""
    key = cache_key(owner, repo, commit_sha, technologies)
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
