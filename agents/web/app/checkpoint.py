"""Memoria corta del agente web: un checkpoint de LangGraph por tarea A2A.

Requisitos (`tasks.md` 3.5, `proposal.md`): `PostgresSaver` de corto plazo,
clave (`thread_id`) = id de generacion + nombre del agente. El id de
generacion es el `task_id` que A2A asigna a cada tarea (una tarea A2A =
una generacion), asi que `thread_id = f"{task_id}:web"`.

A diferencia de la memoria larga (`app/memory.py`, que persiste entre
tareas), esta memoria es efimera: sus checkpoints SHALL borrarse en cuanto
la tarea termina, tanto si acaba bien (Ready) como si falla (error) — por
eso `adelete_thread()` va en un `finally`, para que se ejecute en ambos
casos. Que la tarea anterior haya fallado no debe dejar un checkpoint
huerfano que una tarea futura con el mismo `task_id` (no deberia
reutilizarse, pero por si acaso) encuentre por error.

Se envuelve `research()` en un grafo de LangGraph de un solo nodo solo
porque `AsyncPostgresSaver` exige un grafo compilado (no es una tabla
key-value de uso libre vía API publica) — no para reanudar pasos a medias.
El estado del grafo guarda `result` como dict plano (via `dataclasses.
asdict`), no como las dataclasses `WebResearchResult`/`Source`
directamente: el serializador de checkpoints de LangGraph solo reconoce
sin avisos los tipos JSON-nativos (dict/list/str/bool/...), y trata
cualquier otro tipo como "no registrado" (advertencia hoy, error en
futuras versiones).
"""

import logging
from dataclasses import asdict
from typing import TypedDict

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.graph import END, StateGraph

from app.db import conn_string
from app.service import WebResearchResult, research
from app.tools.tavily_search import Source

logger = logging.getLogger(__name__)

_AGENT_NAME = "web"


class _GraphState(TypedDict):
    technologies: list[str]
    trace_id: str | None
    result: dict | None


def thread_id_for(task_id: str) -> str:
    return f"{task_id}:{_AGENT_NAME}"


async def _research_node(state: _GraphState) -> _GraphState:
    result = await research(state["technologies"], state.get("trace_id"))
    return {"result": asdict(result)}


def _build_graph(checkpointer: AsyncPostgresSaver):
    graph = StateGraph(_GraphState)
    graph.add_node("research", _research_node)
    graph.set_entry_point("research")
    graph.add_edge("research", END)
    return graph.compile(checkpointer=checkpointer)


async def research_with_checkpoint(
    task_id: str, technologies: list[str], trace_id: str | None = None
) -> WebResearchResult:
    """Como `research()`, con un checkpoint de corto plazo durante la tarea.

    El checkpoint se borra siempre al terminar la tarea, acabe bien o mal:
    si `research()` lanza una excepcion, se repropaga tal cual despues de
    borrar el checkpoint (nunca se traga el error). `trace_id` (tarea 3.6)
    solo se reenvia a `research()`; este modulo no toca Langfuse.
    """
    thread_id = thread_id_for(task_id)
    config = {"configurable": {"thread_id": thread_id}}
    async with AsyncPostgresSaver.from_conn_string(conn_string()) as saver:
        await saver.setup()
        graph = _build_graph(saver)
        try:
            final_state = await graph.ainvoke(
                {"technologies": technologies, "trace_id": trace_id, "result": None}, config
            )
        finally:
            try:
                await saver.adelete_thread(thread_id)
            except Exception:
                logger.warning(
                    "fallo borrando memoria corta del agente web (thread_id=%s)",
                    thread_id,
                    exc_info=True,
                )
    raw = final_state["result"]
    return WebResearchResult(
        summary=raw["summary"],
        sources=[Source(**s) for s in raw["sources"]],
        memory_hit=raw["memory_hit"],
    )


async def count_checkpoints(task_id: str) -> int:
    """Solo para verificacion manual: cuantos checkpoints quedan para esta tarea."""
    thread_id = thread_id_for(task_id)
    config = {"configurable": {"thread_id": thread_id}}
    async with AsyncPostgresSaver.from_conn_string(conn_string()) as saver:
        await saver.setup()
        return len([_ async for _ in saver.alist(config)])
