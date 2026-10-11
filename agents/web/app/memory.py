"""Memoria larga del agente web: cache de investigaciones por tecnologias.

Requisitos de `specs/agent-memory/spec.md`:
  - "El agente web no repite busquedas para las mismas tecnologias"
  - "Un acierto de memoria no consume los limites de la tarea"
  - "Una memoria caida no bloquea la generacion" (lectura Y escritura)
  - "La memoria no guarda datos de alumnos" (aqui no hay ninguno: solo
    resumenes y fuentes publicas de internet)

Clave: tecnologias normalizadas (minusculas, sin espacios de mas, orden
alfabetico), para que ["React", "FastAPI"] y ["fastapi", " React"] compartan
entrada. TTL: 30 dias, con refresco en cada lectura (una tecnologia que se
sigue pidiendo se sigue sirviendo desde cache; una que deja de pedirse
caduca sola).
"""

import logging
from dataclasses import asdict

from langgraph.store.base import TTLConfig
from langgraph.store.postgres import AsyncPostgresStore

from app.db import conn_string
from app.tools.tavily_search import Source

logger = logging.getLogger(__name__)

_NAMESPACE = ("web_research",)
_TTL_MINUTES = 30 * 24 * 60  # 30 dias


def normalize_technologies(technologies: list[str]) -> str:
    return "|".join(sorted({t.strip().lower() for t in technologies if t.strip()}))


def _store_cm():
    return AsyncPostgresStore.from_conn_string(
        conn_string(),
        ttl=TTLConfig(default_ttl=_TTL_MINUTES, refresh_on_read=True, omit_expired=True),
    )


async def get_cached_research(technologies: list[str]) -> dict | None:
    """Devuelve el `WebResearchResult` guardado (como dict) o None.

    Cualquier fallo (red, auth, lo que sea) se trata como "no habia nada
    guardado": nunca propaga la excepcion, para que una memoria caida no
    bloquee la generacion.
    """
    key = normalize_technologies(technologies)
    if not key:
        return None
    try:
        async with _store_cm() as store:
            await store.setup()
            item = await store.aget(_NAMESPACE, key)
    except Exception:
        logger.warning("fallo leyendo memoria larga del agente web", exc_info=True)
        return None
    if item is None:
        logger.info("memoria larga: sin acierto para %r, se busca de nuevo", key)
        return None
    logger.info("memoria larga: acierto para %r, no se llama a tavily_search", key)
    return item.value


async def save_research(technologies: list[str], summary: str, sources: list[Source]) -> None:
    """Guarda el resultado. Un fallo aqui se ignora sin interrumpir la tarea."""
    key = normalize_technologies(technologies)
    if not key:
        return
    value = {"summary": summary, "sources": [asdict(s) for s in sources]}
    try:
        async with _store_cm() as store:
            await store.setup()
            await store.aput(_NAMESPACE, key, value)
    except Exception:
        logger.warning("fallo escribiendo memoria larga del agente web", exc_info=True)
