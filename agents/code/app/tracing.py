"""Trazas de Langfuse del agente de codigo (tarea 4.5).

Identico en estructura a `agents/web/app/tracing.py` (ver ese fichero para
la explicacion completa del contrato trace_id/existing_trace_id/span) --
solo cambia el nombre del agente y que `record_task()` recibe tambien
`repo_identity` para dejarlo en el span.
"""

import logging
from functools import lru_cache

from langfuse import Langfuse, get_client

from app.config import get_settings

logger = logging.getLogger(__name__)

_AGENT_NAME = "code"


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


def resolve_trace_id(message_metadata) -> str:
    """El `trace_id` recibido del orquestador, o uno nuevo si no hay.

    `message_metadata` (`context.message.metadata`) llega como
    `google.protobuf.struct_pb2.Struct` cuando el mensaje viene de verdad
    por A2A -- NUNCA como `dict`, aunque la firma anterior lo sugiriera
    (nadie habia probado esta funcion contra un mensaje A2A real hasta el
    orquestador del grupo 6: 3.6/4.5/5.5 la verificaron llamando a la
    logica de negocio directamente, sin pasar `context.message.metadata`
    de verdad). `Struct` soporta `in` y `[...]` pero NO `.get()`
    (confirmado: `AttributeError: get` con protobuf 7.x) -- de ahi que se
    use `in`+`[...]` en vez de `.get()`, que funciona igual para un
    `Struct` real, para un `dict` (los scripts de verificacion que llaman
    a esta funcion con un dict a mano) y para `None`."""
    if message_metadata and "trace_id" in message_metadata:
        trace_id = message_metadata["trace_id"]
    else:
        trace_id = None
    return trace_id if trace_id else new_trace_id()


def litellm_trace_metadata(trace_id: str | None) -> dict:
    """`extra_body` para pasarle a `model.ainvoke(...)` (ver app/service.py)
    de forma que LiteLLM agrupe esta generacion bajo `trace_id` en vez de
    crear una traza nueva. Vacio si no hay `trace_id`."""
    if not trace_id:
        return {}
    return {"metadata": {"existing_trace_id": trace_id}}


def record_task(
    trace_id: str, repo_identity: str, technologies: list[str], *, memory_hit: bool, fragments: int
) -> None:
    """Marca en Langfuse que esta tarea (`trace_id`) paso por el agente de
    codigo. Igual que en el agente web, hace falta incluso en un acierto
    de memoria: ahi no hay ninguna llamada al modelo, asi que sin este
    span la traza de esa tarea no tendria ninguna entrada en Langfuse
    (requisito "Un acierto de memoria queda marcado en la traza"). Un
    fallo aqui se registra y se ignora: la tarea ya ha terminado."""
    try:
        init_client()
        client = get_client()
        with client.start_as_current_observation(
            name=f"agente-{_AGENT_NAME}",
            as_type="span",
            trace_context={"trace_id": trace_id},
            input={"repo": repo_identity, "technologies": technologies},
            output={"memory_hit": memory_hit, "fragments": fragments},
            metadata={"memory_hit": memory_hit},
        ):
            pass
    except Exception:
        logger.warning(
            "fallo marcando memory_hit en la traza de Langfuse (trace_id=%s)",
            trace_id,
            exc_info=True,
        )
