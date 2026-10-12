"""Ejecuta la skill `revisar_justificacion` (ver app/agent_card.py)."""

import dataclasses

from a2a.helpers.proto_helpers import new_data_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue_v2 import EventQueue
from a2a.types import Role

from app.input import parse_review_request
from app.service import review_justification
from app.tracing import record_task, resolve_trace_id


class ReviewerAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        statement, student_answer, verdict, justification = parse_review_request(context.message)
        trace_id = resolve_trace_id(context.message.metadata)
        result = await review_justification(statement, student_answer, verdict, justification, trace_id)
        record_task(trace_id)

        reply = new_data_message(
            dataclasses.asdict(result),
            role=Role.ROLE_AGENT,
            context_id=context.context_id,
            task_id=context.task_id,
        )
        await event_queue.enqueue_event(reply)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("el agente revisor no soporta cancelacion de tareas")
