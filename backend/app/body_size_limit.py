"""Limite de tamaño del body de las peticiones HTTP (propuesta
limite-tamano-body).

Middleware ASGI puro, no `starlette.middleware.base.BaseHTTPMiddleware`:
ese tipo bufferea el body para poder leerlo dos veces, lo que anularia el
objetivo de cortar antes de leer todo el body de una peticion grande.
Envolviendo `receive()` directamente se puede contar bytes y cortar en
cuanto se supera el limite, sin leer de mas.

Dos vias de rechazo, ambas con el mismo cuerpo generico (413, sin exponer
el limite configurado ni detalles de implementacion):
- `Content-Length` declarado por encima del limite: se rechaza sin
  invocar `receive()`, sin leer ningun byte del body.
- Sin `Content-Length` fiable (chunked, o declarado por debajo del real):
  se cuenta el tamaño real de cada mensaje `http.request` recibido y se
  corta en cuanto el acumulado supera el limite.
"""

from starlette.types import ASGIApp, Message, Receive, Scope, Send

MAX_BODY_SIZE = 1 * 1024 * 1024  # 1 MiB

_GENERIC_BODY = b'{"detail":"El cuerpo de la peticion es demasiado grande"}'


async def _send_413(send: Send) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": 413,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": _GENERIC_BODY})


class _BodyTooLarge(BaseException):
    """Señal interna: el body real supero el limite a mitad de lectura.

    Hereda de BaseException, no de Exception: FastAPI envuelve el parseo
    del body en un `except Exception` generico (routing.py) que, si esta
    clase heredara de Exception, la convertiria en un 400 "There was an
    error parsing the body" antes de que llegara a este middleware. Al
    heredar de BaseException esa captura generica no la atrapa, y sigue
    subiendo hasta el `except _BodyTooLarge` de este mismo middleware
    (nunca llega a ServerErrorMiddleware, que tambien captura solo
    Exception y devolveria un 500 generico en vez de nuestro 413).
    """


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_body_size: int = MAX_BODY_SIZE) -> None:
        self.app = app
        self.max_body_size = max_body_size

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        content_length = next(
            (value for key, value in scope.get("headers", []) if key == b"content-length"),
            None,
        )
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                declared_size = None
            if declared_size is not None and declared_size > self.max_body_size:
                await _send_413(send)
                return

        received_size = 0

        async def limited_receive() -> Message:
            nonlocal received_size
            message = await receive()
            if message["type"] == "http.request":
                received_size += len(message.get("body", b""))
                if received_size > self.max_body_size:
                    raise _BodyTooLarge()
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _BodyTooLarge:
            await _send_413(send)
