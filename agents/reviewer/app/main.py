from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.routes.fastapi_routes import add_a2a_routes_to_fastapi
from a2a.server.tasks import InMemoryTaskStore

from app.agent_card import build_agent_card
from app.executor import ReviewerAgentExecutor
from app.rate_limit import limiter
from app.service_auth import ServiceAuthMiddleware


def build_app() -> FastAPI:
    card = build_agent_card()
    handler = DefaultRequestHandler(
        agent_executor=ReviewerAgentExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    app = FastAPI(title="JuniorTrainer - Agente Revisor")
    app.state.limiter = limiter
    app.add_middleware(ServiceAuthMiddleware)
    # SlowAPIMiddleware anadido DESPUES de ServiceAuthMiddleware: en
    # Starlette, add_middleware inserta cada middleware al principio de la
    # lista interna, asi que el ultimo en anadirse es el mas exterior y se
    # ejecuta primero -- el rate limiting rechaza el exceso de peticiones
    # antes de comparar la credencial de servicio (change resiliencia-agentes).
    app.add_middleware(SlowAPIMiddleware)
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(card),
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/"),
    )

    @app.exception_handler(RateLimitExceeded)
    def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"error": "Demasiadas peticiones, intentalo mas tarde"},
        )

    return app


app = build_app()
