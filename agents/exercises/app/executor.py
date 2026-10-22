"""Ejecuta la skill `generar_ejercicios` (ver app/agent_card.py).

Progresion por tarea (ver tasks.md del change `generacion-ejercicios-agentes`):
  - 5.1: scaffold -- validaba la entrada y respondia con un eco.
  - 5.2: search_saved_exercises (ver app/tools/saved_exercises.py).
  - 5.3: decision y redaccion real via app/service.py.
  - 5.4 (memoria larga propia, eliminada por el change
    `eliminar-memoria-agente-ejercicios`: ver app/service.py).
  - 5.5 (este fichero, ahora): `trace_id` de Langfuse (ver
    app/tracing.py), igual que en los otros dos agentes.
"""

import dataclasses

from a2a.helpers.proto_helpers import new_data_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue_v2 import EventQueue
from a2a.types import Role

from app.input import parse_exercise_request
from app.service import generate_exercises
from app.tracing import record_task, resolve_trace_id


class ExercisesAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        exercise_type, count, web_result, code_result = parse_exercise_request(context.message)
        # trace_id (tarea 5.5): lo pone el orquestador en los metadatos del
        # mensaje; si no hay ninguno (agente en solitario, sin orquestador),
        # resolve_trace_id() genera uno nuevo para que la traza exista igual.
        trace_id = resolve_trace_id(context.message.metadata)
        result = await generate_exercises(exercise_type, count, web_result, code_result, trace_id)
        record_task(
            trace_id,
            exercise_type,
            count,
            memory_hit=result.memory_hit,
            candidates=len(result.candidates),
        )

        reply = new_data_message(
            dataclasses.asdict(result),
            role=Role.ROLE_AGENT,
            context_id=context.context_id,
            task_id=context.task_id,
        )
        await event_queue.enqueue_event(reply)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("el agente de ejercicios no soporta cancelacion de tareas")
