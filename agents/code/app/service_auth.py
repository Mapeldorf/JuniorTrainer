"""Middleware de autenticacion de servicio backend -> agente.

Requisito de `specs/agent-auth/spec.md` (change `autenticacion-backend-agentes`):
toda peticion HTTP a este agente -- incluidas las rutas JSON-RPC y la Agent
Card -- debe llevar la cabecera `X-Agent-Service-Token` con el mismo valor
que `Settings.agent_service_token`, o se rechaza con 401 antes de ejecutar
ninguna logica de negocio (sin invocar al LLM, sin leer GitHub/Tavily, sin
tocar la base de datos).

Un `BaseHTTPMiddleware` (en vez de `Depends` por ruta) porque
`add_a2a_routes_to_fastapi` registra las rutas A2A internamente sin exponer
un punto donde inyectar `Depends`; el middleware intercepta toda peticion a
la app con independencia de como el SDK defina sus rutas (ver design.md,
decision "Punto de verificacion").

La comparacion usa `hmac.compare_digest` (tiempo constante) en vez de `==`
para no abrir un canal de temporizacion que facilite adivinar la credencial
por fuerza bruta remota.
"""

import hmac

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import get_settings

_HEADER_NAME = "X-Agent-Service-Token"


class ServiceAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        expected = get_settings().agent_service_token
        received = request.headers.get(_HEADER_NAME, "")
        if not received or not hmac.compare_digest(received, expected):
            return JSONResponse(
                status_code=401,
                content={"error": "credencial de servicio ausente o invalida"},
            )
        return await call_next(request)
