"""Cabeceras de seguridad HTTP basicas (propuesta cabeceras-seguridad-http).

Middleware ASGI puro, igual que `app.body_size_limit`: solo envuelve
`send()` para interceptar el mensaje `http.response.start` y añadir las
cabeceras antes de que salga por el socket. Al ser el middleware mas
exterior de la cadena (añadido el ultimo en `main.py`), cubre tambien las
respuestas generadas por `ServerErrorMiddleware`/`ExceptionMiddleware` y
por el resto de middlewares de la app (rate limiting, limite de body).
"""

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_SECURITY_HEADERS: list[tuple[bytes, bytes]] = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
    (b"strict-transport-security", b"max-age=31536000; includeSubDomains"),
]


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                existing = {key.lower() for key, _ in message.get("headers", [])}
                headers = list(message.get("headers", []))
                for key, value in _SECURITY_HEADERS:
                    if key not in existing:
                        headers.append((key, value))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
