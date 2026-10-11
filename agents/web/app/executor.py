import dataclasses

from a2a.helpers.proto_helpers import new_data_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue_v2 import EventQueue
from a2a.types import Role

from app.checkpoint import research_with_checkpoint
from app.input import parse_technologies


class WebAgentExecutor(AgentExecutor):
    """Ejecuta la skill `investigar_tecnologias` (ver app/agent_card.py)."""

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        technologies = parse_technologies(context.message)
        result = await research_with_checkpoint(context.task_id, technologies)

        reply = new_data_message(
            dataclasses.asdict(result),
            role=Role.ROLE_AGENT,
            context_id=context.context_id,
            task_id=context.task_id,
        )
        await event_queue.enqueue_event(reply)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("el agente web no soporta cancelacion de tareas")
