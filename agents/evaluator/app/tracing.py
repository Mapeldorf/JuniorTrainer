"""Trazas de Langfuse del agente evaluador.

Identico en estructura a `agents/exercises/app/tracing.py` (ver ese
fichero para la explicacion completa del contrato
trace_id/existing_trace_id/span) -- solo cambia el nombre del agente y
que `record_task()` recibe `verdict` en vez de `memory_hit`/`candidates`.
"""

import logging
from functools import lru_cache

from langfuse import Langfuse, get_client

from app.config import get_settings

logger = logging.getLogger(__name__)

_AGENT_NAME = "evaluator"


@lru_cache
def init_client() -> None:
    settings = get_settings()
    Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_base_url,
    )


def new_trace_id() -> str:
    return Langfuse.create_trace_id()


def resolve_trace_id(message_metadata) -> str:
    """Igual que `resolve_trace_id` del agente de ejercicios (ver su
    docstring): `message_metadata` es un `Struct` de protobuf cuando el
    mensaje viene de verdad por A2A, por eso se usa `in`+`[...]` en vez
    de `.get()`."""
    if message_metadata and "trace_id" in message_metadata:
        trace_id = message_metadata["trace_id"]
    else:
        trace_id = None
    return trace_id if trace_id else new_trace_id()


def litellm_trace_metadata(trace_id: str | None) -> dict:
    if not trace_id:
        return {}
    return {"metadata": {"existing_trace_id": trace_id}}


def record_task(trace_id: str, verdict: str) -> None:
    """Marca en Langfuse que esta tarea (`trace_id`) paso por el agente
    evaluador. Un fallo aqui se registra y se ignora: la tarea ya ha
    terminado."""
    try:
        init_client()
        client = get_client()
        with client.start_as_current_observation(
            name=f"agente-{_AGENT_NAME}",
            as_type="span",
            trace_context={"trace_id": trace_id},
            output={"verdict": verdict},
            metadata={"verdict": verdict},
        ):
            pass
    except Exception:
        logger.warning(
            "fallo marcando el verdict en la traza de Langfuse (trace_id=%s)",
            trace_id,
            exc_info=True,
        )
