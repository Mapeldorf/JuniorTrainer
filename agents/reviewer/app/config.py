from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT_ENV = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Variables de entorno del agente revisor. Ver .env.example en la raiz del repo."""

    model_config = SettingsConfigDict(env_file=_REPO_ROOT_ENV, extra="ignore")

    agent_reviewer_host: str = "0.0.0.0"
    agent_reviewer_port: int = 8014
    agent_reviewer_url: str = "http://agent-reviewer:8014/"

    # Modelo logico "reviewer", ya predefinido en infra/litellm/config.yaml,
    # resuelto por LiteLLM via REVIEWER_MODEL/REVIEWER_API_KEY.
    litellm_base_url: str = "http://litellm:4000/v1"
    litellm_master_key: str
    reviewer_model: str = "reviewer"

    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_base_url: str = "https://cloud.langfuse.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
