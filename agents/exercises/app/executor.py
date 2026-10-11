"""Ejecuta la skill `generar_ejercicios` (ver app/agent_card.py).

Progresion por tarea (ver tasks.md del change `generacion-ejercicios-agentes`):
  - 5.1 (este fichero, ahora): scaffold -- valida la entrada y responde con
    un eco, para verificar el cableado A2A antes de implementar nada real.
  - 5.2: search_saved_exercises (ver app/tools/saved_exercises.py).
  - 5.3: decision y redaccion real via app/service.py.
  - 5.4/5.5: memoria larga y trace_id (todavia no aqui).
"""

from a2a.helpers.proto_helpers import new_data_message
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events.event_queue_v2 import EventQueue
from a2a.types import Role

from app.input import parse_exercise_request


class ExercisesAgentExecutor(AgentExecutor):
    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        exercise_type, count, web_result, code_result = parse_exercise_request(context.message)

        reply = new_data_message(
            {
                "echo": True,
                "exercise_type": exercise_type,
                "count": count,
                "has_web_result": web_result is not None,
                "has_code_result": code_result is not None,
            },
            role=Role.ROLE_AGENT,
            context_id=context.context_id,
            task_id=context.task_id,
        )
        await event_queue.enqueue_event(reply)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("el agente de ejercicios no soporta cancelacion de tareas")
