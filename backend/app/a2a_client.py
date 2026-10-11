"""Cliente A2A para que FastAPI envie tareas sincronas (sin streaming) a los
tres agentes de generacion (tarea 6.1).

Patron de cliente confirmado en `design.md` ("Patron de cableado A2A
confirmado", tarea 2.2, y su ampliacion para DATA en la tarea 6.1): se
reutiliza tal cual, sustituyendo `new_text_message`/`get_stream_response_text`
(texto) por `new_data_message`/una extraccion de DATA propia, porque el SDK
no trae un helper equivalente al de texto para datos estructurados.
"""

import asyncio
import logging

import httpx
from a2a.client import ClientConfig, create_client
from a2a.helpers.proto_helpers import get_data_parts, new_data_message
from a2a.types import Role
from a2a.types.a2a_pb2 import SendMessageRequest, StreamResponse

logger = logging.getLogger(__name__)

# Limite por tarea A2A individual (tarea 6.6, "Limites de tiempo de la
# generacion"): 2 minutos. Vive aqui (no en orchestrator.py) para que
# cualquier llamada A2A, presente o futura, tenga el mismo valor por
# defecto sin tener que repetirlo en cada punto de llamada.
DEFAULT_TASK_TIMEOUT_SECONDS = 120.0


class A2ATaskError(RuntimeError):
    """Una tarea A2A ha fallado: rechazo del agente, error de transporte, o
    una respuesta sin ninguna parte de datos."""


class A2ATaskTimeout(A2ATaskError):
    """La tarea A2A no respondio dentro del limite de tiempo."""


def _extract_data(response: StreamResponse) -> list:
    """Analogo a `get_stream_response_text` (helper que SI trae el SDK) pero
    para DATA parts, que el SDK no cubre. Un `StreamResponse` en modo sin
    streaming siempre llega como `message` (nuestro caso: los tres agentes
    responden con `event_queue.enqueue_event(new_data_message(...))`, nunca
    con una `Task` de varios pasos), pero tambien se cubre `task` por si un
    agente futuro devolviera artefactos en vez de un mensaje directo."""
    if response.HasField("message"):
        return get_data_parts(response.message.parts)
    if response.HasField("task"):
        parts: list = []
        for artifact in response.task.artifacts:
            parts.extend(get_data_parts(artifact.parts))
        return parts
    return []


async def send_a2a_task(
    url: str,
    data: dict,
    *,
    trace_id: str | None = None,
    timeout: float = DEFAULT_TASK_TIMEOUT_SECONDS,
) -> dict:
    """Envia `data` como una unica parte de datos a la Agent Card publicada
    en `url`, espera la respuesta (sin streaming) y devuelve su primera
    parte de datos como `dict`.

    `trace_id`, si se indica, viaja en los metadatos del mensaje -- el mismo
    sitio donde cada agente lo busca (`resolve_trace_id`, tareas 3.6/4.5/5.5):
    `context.message.metadata.get("trace_id")`. Se deja opcional aqui porque
    la tarea 6.1 solo pide el transporte; la 6.7 es quien decide generar un
    `trace_id` por generacion y pasarlo en cada llamada.

    Lanza `A2ATaskTimeout` si se supera `timeout`, o `A2ATaskError` para
    cualquier otro fallo (agente inalcanzable, Agent Card invalida, rechazo
    del agente, respuesta sin parte de datos) -- una unica familia de
    excepciones para que el orquestador (6.4/6.5) no tenga que distinguir
    el tipo exacto de fallo de transporte, solo "este agente ha fallado".
    """

    async def _call() -> dict:
        try:
            # `create_client` sin `httpx_client` propio monta un
            # `httpx.AsyncClient()` A SECAS -- y el timeout por defecto de
            # httpx es de 5 SEGUNDOS (`httpx._config.DEFAULT_TIMEOUT_CONFIG`),
            # muchisimo menos que una tarea real (busqueda web + resumen con
            # el modelo facilmente pasa de eso). Sin esto, el `asyncio.wait_for`
            # de mas abajo nunca llega a activarse: httpx corta antes, por
            # debajo, con un generico "Client Request timed out" en vez del
            # mensaje de `A2ATaskTimeout`. Encontrado por el usuario
            # verificando 6.7 en vivo contra el agente web real.
            async with httpx.AsyncClient(timeout=httpx.Timeout(timeout)) as httpx_client:
                client = await create_client(
                    url, client_config=ClientConfig(streaming=False, httpx_client=httpx_client)
                )
                message = new_data_message(data, role=Role.ROLE_USER)
                # `new_data_message` no acepta `metadata=` (confirmado inspeccionando
                # la firma real del SDK, ver design.md -- corrige una nota anterior
                # que asumia lo contrario sin haberlo probado). `Message.metadata`
                # es un campo `Struct` normal del propio protobuf: se rellena
                # despues de construir el mensaje, con `.update(...)`.
                if trace_id:
                    message.metadata.update({"trace_id": trace_id})
                request = SendMessageRequest(message=message)

                results: list = []
                async for response in client.send_message(request):
                    results.extend(_extract_data(response))
        except Exception as exc:  # noqa: BLE001 - se homogeneiza a proposito, ver docstring
            raise A2ATaskError(f"fallo llamando al agente en {url}: {exc}") from exc

        if not results:
            raise A2ATaskError(f"el agente en {url} respondio sin ninguna parte de datos")
        return results[0]

    try:
        return await asyncio.wait_for(_call(), timeout=timeout)
    except TimeoutError as exc:
        raise A2ATaskTimeout(f"el agente en {url} no respondio en {timeout:.0f}s") from exc
