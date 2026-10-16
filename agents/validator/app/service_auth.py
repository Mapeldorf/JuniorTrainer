"""Middleware de autenticacion de servicio backend -> agente.

Requisito de `specs/agent-auth/spec.md` (change `autenticacion-backend-agentes`):
toda peticion HTTP a este agente -- incluidas las rutas JSON-RPC y la Agent
Card -- debe llevar la cabecera `X-Agent-Service-Token` con el mismo valor
que `Settings.agent_service_token`, o se rechaza con 401 antes de ejecutar
ninguna logica de negocio (sin invocar al LLM).

Identico a `agents/evaluator/app/service_auth.py`; la comparacion usa
`hmac.compare_digest` en tiempo constante.
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
