"""Ejecuta la skill `analizar_repositorio` (ver app/agent_card.py).

Progresion por tarea (ver tasks.md del change `generacion-ejercicios-agentes`):
  - 4.1: scaffold (validaba la entrada y respondia con un eco).
  - 4.2: list_files/read_file (ver app/tools/filesystem.py).
  - 4.3: analisis real via app/service.py.
  - 4.4: memoria larga.
  - 4.5 (este fichero, ahora): `trace_id` de Langfuse (ver app/tracing.py),
    igual que en el agente web (ver app/executor.py de agents/web/).
"""

import dataclasses

from a2a.helpers.proto_helpers import new_data_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue_v2 import EventQueue
from a2a.types import Role

from app.input import parse_repo_input
from app.service import analyze_repo
from app.tracing import record_task, resolve_trace_id


class CodeAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        repo_path, technologies = parse_repo_input(context.message)
        # trace_id (tarea 4.5): lo pone el orquestador en los metadatos del
        # mensaje; si no hay ninguno (agente en solitario, sin orquestador),
        # resolve_trace_id() genera uno nuevo para que la traza exista igual.
        trace_id = resolve_trace_id(context.message.metadata)
        result = await analyze_repo(repo_path, technologies, trace_id)
        record_task(
            trace_id, repo_path, technologies, memory_hit=result.memory_hit, fragments=len(result.fragments)
        )

        reply = new_data_message(
            dataclasses.asdict(result),
            role=Role.ROLE_AGENT,
            context_id=context.context_id,
            task_id=context.task_id,
        )
        await event_queue.enqueue_event(reply)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("el agente de codigo no soporta cancelacion de tareas")
