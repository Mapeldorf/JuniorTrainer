"""Ejecuta la skill `analizar_repositorio` (ver app/agent_card.py).

Progresion por tarea (ver tasks.md del change `generacion-ejercicios-agentes`):
  - 4.1 (este fichero, por ahora): scaffold minimo -- valida la entrada y
    responde con un eco, solo para verificar que el servicio A2A arranca y
    sirve su Agent Card. Sin logica de negocio real todavia.
  - 4.2+: list_files/read_file, modelo, memoria, trace_id.
"""

import dataclasses

from a2a.helpers.proto_helpers import new_data_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue_v2 import EventQueue
from a2a.types import Role

from app.input import parse_repo_input


class CodeAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        repo_path, technologies = parse_repo_input(context.message)

        # Placeholder de la tarea 4.1: confirma que la entrada se parseo
        # bien, sin leer el repo todavia (eso llega en 4.2/4.3).
        reply = new_data_message(
            dataclasses.asdict(
                _EchoResult(repo_path=repo_path, technologies=technologies)
            ),
            role=Role.ROLE_AGENT,
            context_id=context.context_id,
            task_id=context.task_id,
        )
        await event_queue.enqueue_event(reply)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("el agente de codigo no soporta cancelacion de tareas")


@dataclasses.dataclass
class _EchoResult:
    repo_path: str
    technologies: list[str]
