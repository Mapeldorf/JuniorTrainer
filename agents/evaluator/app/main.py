from fastapi import FastAPI

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.routes.fastapi_routes import add_a2a_routes_to_fastapi
from a2a.server.tasks import InMemoryTaskStore

from app.agent_card import build_agent_card
from app.executor import EvaluatorAgentExecutor


def build_app() -> FastAPI:
    card = build_agent_card()
    handler = DefaultRequestHandler(
        agent_executor=EvaluatorAgentExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=card,
    )
    app = FastAPI(title="JuniorTrainer - Agente Evaluador")
    add_a2a_routes_to_fastapi(
        app,
        agent_card_routes=create_agent_card_routes(card),
        jsonrpc_routes=create_jsonrpc_routes(handler, rpc_url="/"),
    )
    return app


app = build_app()
