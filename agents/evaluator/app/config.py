from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Mismo .env unico del proyecto que usa el backend y los otros agentes
# (ver .env.example en la raiz del repo).
_REPO_ROOT_ENV = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Variables de entorno del agente evaluador. Ver .env.example en la raiz del repo."""

    model_config = SettingsConfigDict(env_file=_REPO_ROOT_ENV, extra="ignore")

    # Host/puerto donde este servicio escucha, y la URL publica (dentro de la
    # red de docker-compose) que se anuncia en su Agent Card.
    agent_evaluator_host: str = "0.0.0.0"
    agent_evaluator_port: int = 8013
    agent_evaluator_url: str = "http://agent-evaluator:8013/"

    # Proxy de LiteLLM (seccion 11 de la especificacion): modelo logico
    # "evaluator", ya predefinido en infra/litellm/config.yaml, resuelto
    # por LiteLLM via EVALUATOR_MODEL/EVALUATOR_API_KEY.
    litellm_base_url: str = "http://litellm:4000/v1"
    litellm_master_key: str
    evaluator_model: str = "evaluator"

    # Langfuse Cloud: igual que el resto de agentes (ver app/tracing.py).
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_base_url: str = "https://cloud.langfuse.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
