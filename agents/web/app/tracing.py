"""Trazas de Langfuse del agente web (tarea 3.6).

El orquestador (grupo 6, todavia no implementado) crea la traza de una
generacion completa y le pasa su `trace_id` a cada agente en los metadatos
del mensaje A2A (`message.metadata["trace_id"]`, ver design.md "Metadatos
y `trace_id`"). Este modulo:

  - Lee ese `trace_id` (`resolve_trace_id`). Si no viene ninguno -- p. ej.
    al ejecutar este agente en solitario, sin orquestador, como en los
    scripts de verificacion -- genera uno nuevo, para que el agente
    funcione igual sin depender de el.
  - Marca en esa traza que el agente web paso por aqui y si la respuesta
    vino de memoria (`record_task`), requisito "Un acierto de memoria
    queda marcado en la traza" de `specs/agent-memory/spec.md`. Esto hace
    falta incluso en un acierto de memoria: en ese caso no hay ninguna
    llamada al modelo (ver app/service.py), asi que sin este span la
    traza de esa tarea no tendria ninguna entrada en Langfuse.
  - Da el `extra_body` que hay que pasarle a la llamada al modelo
    (`litellm_trace_metadata`) para que, cuando SI hay llamada (fallo de
    cache), LiteLLM agrupe esa generacion bajo la misma traza en vez de
    crear una nueva por su cuenta (via la clave `existing_trace_id`, que
    es la que exige LiteLLM para continuar una traza existente en vez de
    crearla -- ver la integracion de Langfuse de LiteLLM).

Un fallo escribiendo a Langfuse (red, credenciales, lo que sea) nunca debe
bloquear la generacion -- igual que un fallo de memoria (`app/memory.py`,
`app/checkpoint.py`): se registra y se ignora.
"""

import logging
from functools import lru_cache

from langfuse import Langfuse, get_client

from app.config import get_settings

logger = logging.getLogger(__name__)

_AGENT_NAME = "web"


@lru_cache
def init_client() -> None:
    """Construye el cliente Langfuse una sola vez por proceso, con las
    credenciales de `Settings` (no de `os.environ`: el `.env` del repo lo
    lee `pydantic-settings`, no llega al entorno real del proceso).
    `get_client()` lo devuelve luego como singleton. No se guarda el
    resultado: solo importa que se haya llamado una vez antes de usar
    `get_client()` -- cualquier llamador que vaya a usar `get_client()`
    directamente (como `record_task` o un script de verificacion) debe
    llamar a esta funcion primero.
    """
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
    crear una traza nueva. Vacio si no hay `trace_id` (p. ej. un uso del
    modelo fuera del flujo de una tarea A2A)."""
    if not trace_id:
        return {}
    return {"metadata": {"existing_trace_id": trace_id}}


def record_task(trace_id: str, technologies: list[str], *, memory_hit: bool, sources: int) -> None:
    """Marca en Langfuse que esta tarea (`trace_id`) paso por el agente web.

    Se abre (y cierra en el acto) un span bajo la traza existente -- nunca
    una traza nueva -- con `memory_hit` en sus metadatos. Un fallo aqui
    (red, credenciales) se registra y se ignora: la tarea ya ha terminado
    y no debe bloquearse por esto.
    """
    try:
        init_client()
        client = get_client()
        with client.start_as_current_observation(
            name=f"agente-{_AGENT_NAME}",
            as_type="span",
            trace_context={"trace_id": trace_id},
            input={"technologies": technologies},
            output={"memory_hit": memory_hit, "fuentes": sources},
            metadata={"memory_hit": memory_hit},
        ):
            pass
    except Exception:
        logger.warning(
            "fallo marcando memory_hit en la traza de Langfuse (trace_id=%s)",
            trace_id,
            exc_info=True,
        )
