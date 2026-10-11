"""Trazas de Langfuse del agente de ejercicios (tarea 5.5).

Identico en estructura a `agents/web/app/tracing.py` y
`agents/code/app/tracing.py` (ver esos ficheros para la explicacion
completa del contrato trace_id/existing_trace_id/span) -- solo cambia el
nombre del agente y que `record_task()` recibe `exercise_type`/`count`
en vez de `technologies`/`repo_path`.
"""

import logging
from functools import lru_cache

from langfuse import Langfuse, get_client

from app.config import get_settings

logger = logging.getLogger(__name__)

_AGENT_NAME = "exercises"


@lru_cache
def init_client() -> None:
    """Construye el cliente Langfuse una sola vez por proceso, con las
    credenciales de `Settings` (no de `os.environ`). `get_client()` lo
    devuelve luego como singleton. Cualquier llamador que vaya a usar
    `get_client()` directamente (como `record_task` o un script de
    verificacion) debe llamar a esta funcion primero."""
    settings = get_settings()
    Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_base_url,
    )


def new_trace_id() -> str:
    return Langfuse.create_trace_id()


def resolve_trace_id(message_metadata: dict | None) -> str:
    """El `trace_id` recibido del orquestador, o uno nuevo si no hay."""
    trace_id = (message_metadata or {}).get("trace_id")
    return trace_id if trace_id else new_trace_id()


def litellm_trace_metadata(trace_id: str | None) -> dict:
    """`extra_body` para pasarle a `model.ainvoke(...)` (ver app/service.py)
    de forma que LiteLLM agrupe esta generacion bajo `trace_id` en vez de
    crear una traza nueva. Vacio si no hay `trace_id`."""
    if not trace_id:
        return {}
    return {"metadata": {"existing_trace_id": trace_id}}


def record_task(
    trace_id: str, exercise_type: str, count: int, *, memory_hit: bool, candidates: int
) -> None:
    """Marca en Langfuse que esta tarea (`trace_id`) paso por el agente de
    ejercicios. Un fallo aqui se registra y se ignora: la tarea ya ha
    terminado."""
    try:
        init_client()
        client = get_client()
        with client.start_as_current_observation(
            name=f"agente-{_AGENT_NAME}",
            as_type="span",
            trace_context={"trace_id": trace_id},
            input={"exercise_type": exercise_type, "count": count},
            output={"memory_hit": memory_hit, "candidates": candidates},
            metadata={"memory_hit": memory_hit},
        ):
            pass
    except Exception:
        logger.warning(
            "fallo marcando memory_hit en la traza de Langfuse (trace_id=%s)",
            trace_id,
            exc_info=True,
        )
