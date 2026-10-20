"""Ejecuta la skill `validar_tecnologias` (ver app/agent_card.py)."""

import dataclasses

from a2a.helpers.proto_helpers import new_data_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue_v2 import EventQueue
from a2a.types import Role

from app.input import parse_context, parse_technologies
from app.service import validate_technologies
from app.tracing import record_task, resolve_trace_id


class ValidatorAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        technologies = parse_technologies(context.message)
        validation_context = parse_context(context.message)
        trace_id = resolve_trace_id(context.message.metadata)
        result = await validate_technologies(technologies, validation_context, trace_id)
        record_task(trace_id, result.valid)

        reply = new_data_message(
            dataclasses.asdict(result),
            role=Role.ROLE_AGENT,
            context_id=context.context_id,
            task_id=context.task_id,
        )
        await event_queue.enqueue_event(reply)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("el agente validador no soporta cancelacion de tareas")
