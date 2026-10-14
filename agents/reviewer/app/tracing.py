"""Trazas de Langfuse del agente revisor. Identico en estructura a
`agents/evaluator/app/tracing.py` -- solo cambia el nombre del agente y
que `record_task()` no recibe `verdict` (este agente no lo decide)."""

import logging
from functools import lru_cache

from langfuse import Langfuse, get_client

from app.config import get_settings

logger = logging.getLogger(__name__)

_AGENT_NAME = "reviewer"


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
    if message_metadata and "trace_id" in message_metadata:
        trace_id = message_metadata["trace_id"]
    else:
        trace_id = None
    return trace_id if trace_id else new_trace_id()


def litellm_trace_metadata(
    trace_id: str | None, *, mask_input: bool = False, mask_output: bool = False
) -> dict:
    """`mask_input`/`mask_output` (change redaccion-trazas-langfuse):
    LiteLLM sustituye el prompt/la respuesta por "redacted-by-litellm" en
    Langfuse para esta llamada, sin afectar la llamada real al LLM ni el
    resto de metadata de la traza -- para las llamadas que interpolan la
    respuesta de un alumno (ver app/service.py, requisito de
    specs/agent-trace-privacy). El `metadata` se construye siempre a
    partir de estos argumentos, no solo de `trace_id`."""
    metadata: dict = {}
    if trace_id:
        metadata["existing_trace_id"] = trace_id
    if mask_input:
        metadata["mask_input"] = True
    if mask_output:
        metadata["mask_output"] = True
    return {"metadata": metadata} if metadata else {}


def record_task(trace_id: str) -> None:
    """Marca en Langfuse que esta tarea (`trace_id`) paso por el agente
    revisor. Un fallo aqui se registra y se ignora: la tarea ya ha
    terminado."""
    try:
        init_client()
        client = get_client()
        with client.start_as_current_observation(
            name=f"agente-{_AGENT_NAME}",
            as_type="span",
            trace_context={"trace_id": trace_id},
        ):
            pass
    except Exception:
        logger.warning(
            "fallo marcando la traza de Langfuse (trace_id=%s)",
            trace_id,
            exc_info=True,
        )
