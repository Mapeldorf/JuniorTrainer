"""Cabeceras de seguridad HTTP basicas (propuesta cabeceras-seguridad-http).

Middleware ASGI puro, igual que `app.body_size_limit`: solo envuelve
`send()` para interceptar el mensaje `http.response.start` y añadir las
cabeceras antes de que salga por el socket. Al ser el middleware mas
exterior de la cadena (añadido el ultimo en `main.py`), cubre tambien las
respuestas generadas por `ServerErrorMiddleware`/`ExceptionMiddleware` y
por el resto de middlewares de la app (rate limiting, limite de body).

Esta API es JSON puro: ninguna respuesta de negocio se renderiza como HTML,
asi que el `default-src 'none'` de la CSP de abajo es mas bien
defensa-en-profundidad (p.ej. si algun dia una respuesta de error se
sirviera como HTML). Las unicas paginas HTML reales que sirve este backend
son Swagger (`/docs`) y ReDoc (`/redoc`), que cargan su JS/CSS desde
cdn.jsdelivr.net e inyectan un `<script>`/`<style>` inline generado por
FastAPI -- por eso tienen su propia CSP mas permisiva, acotada a esas dos
rutas, en lugar de relajar la del resto de la API.
"""

from starlette.types import ASGIApp, Message, Receive, Scope, Send

_DOCS_PATHS = {"/docs", "/redoc"}

_DEFAULT_CSP = (
    "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
)

# Swagger UI y ReDoc necesitan cargar su bundle desde cdn.jsdelivr.net y
# ejecutar un <script> inline que FastAPI genera con la URL del
# openapi.json -- no es un valor fijo que se pueda hashear.
_DOCS_CSP = (
    "default-src 'none'; "
    "script-src 'self' https://cdn.jsdelivr.net 'unsafe-inline'; "
    "style-src 'self' https://cdn.jsdelivr.net https://fonts.googleapis.com 'unsafe-inline'; "
    "font-src https://fonts.gstatic.com; "
    "img-src 'self' data: https://fastapi.tiangolo.com; "
    "connect-src 'self'; "
    "frame-ancestors 'none'; "
    "base-uri 'none'"
)

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

        path = scope["path"]
        csp = _DOCS_CSP if path in _DOCS_PATHS else _DEFAULT_CSP

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                existing = {key.lower() for key, _ in message.get("headers", [])}
                headers = list(message.get("headers", []))
                for key, value in _SECURITY_HEADERS:
                    if key not in existing:
                        headers.append((key, value))
                if b"content-security-policy" not in existing:
                    headers.append((b"content-security-policy", csp.encode()))
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_with_headers)
