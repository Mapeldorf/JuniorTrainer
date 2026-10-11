"""Memoria larga PROPIA del agente de ejercicios: enunciados ya propuestos
por tipo (no solo los guardados -- eso lo cubre `search_saved_exercises`,
ver app/tools/saved_exercises.py).

Requisito de `specs/agent-memory/spec.md`: "El agente de ejercicios no
repite temas ya propuestos" -- usa "su propio historial ademas de los
ejercicios guardados". Decision de diseno (design.md "Contrato de
entrada/salida del agente de ejercicios"): clave = `exercise_type`,
SIN TTL (a diferencia de la memoria de web/codigo, que caduca a los 30
dias -- aqui no hay `TTLConfig`, por eso no caduca), lista de hasta los
20 enunciados mas recientes, recortada por el principio (los mas
antiguos) al escribir.
"""

import logging

from langgraph.store.postgres import AsyncPostgresStore

from app.db import conn_string

logger = logging.getLogger(__name__)

_NAMESPACE = ("exercise_history",)
_MAX_RECENT = 20


def _store_cm():
    # Sin `ttl=`: a diferencia de web/codigo, esta memoria no caduca.
    return AsyncPostgresStore.from_conn_string(conn_string())


async def get_recent_statements(exercise_type: str) -> list[str]:
    """Hasta los 20 enunciados mas recientes ya propuestos para ese tipo.

    Cualquier fallo (red, auth, lo que sea) se trata como "no hay
    historial": nunca propaga la excepcion, para que una memoria caida no
    bloquee la generacion.
    """
    try:
        async with _store_cm() as store:
            await store.setup()
            item = await store.aget(_NAMESPACE, exercise_type)
    except Exception:
        logger.warning("fallo leyendo el historial de enunciados propuestos", exc_info=True)
        return []
    if item is None:
        return []
    statements = item.value.get("statements", [])
    return statements if isinstance(statements, list) else []


async def save_statements(exercise_type: str, new_statements: list[str]) -> None:
    """Añade `new_statements` al historial de ese tipo, recortando por el
    principio para quedarse con los 20 mas recientes. Un fallo aqui se
    ignora sin interrumpir la tarea (igual que `save_analysis`/
    `save_research` de los otros dos agentes)."""
    if not new_statements:
        return
    try:
        async with _store_cm() as store:
            await store.setup()
            item = await store.aget(_NAMESPACE, exercise_type)
            existing = item.value.get("statements", []) if item is not None else []
            if not isinstance(existing, list):
                existing = []
            combined = [*existing, *new_statements][-_MAX_RECENT:]
            await store.aput(_NAMESPACE, exercise_type, {"statements": combined})
    except Exception:
        logger.warning("fallo escribiendo el historial de enunciados propuestos", exc_info=True)
