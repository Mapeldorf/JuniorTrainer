from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Mismo .env unico del proyecto que usa el backend (ver .env.example en la
# raiz del repo). Resuelto por ruta absoluta para que funcione igual desde
# agents/web/ (venv local) que dentro del contenedor Docker (donde las
# variables ya llegan como entorno real via env_file en docker-compose.yml).
_REPO_ROOT_ENV = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Variables de entorno del agente web. Ver .env.example en la raiz del repo."""

    model_config = SettingsConfigDict(env_file=_REPO_ROOT_ENV, extra="ignore")

    # Host/puerto donde este servicio escucha, y la URL publica (dentro de la
    # red de docker-compose) que se anuncia en su Agent Card.
    agent_web_host: str = "0.0.0.0"
    agent_web_port: int = 8010
    agent_web_url: str = "http://agent-web:8010/"

    tavily_api_key: str

    # Proxy de LiteLLM (seccion 11 de la especificacion): modelo logico
    # "generator", resuelto por LiteLLM via GENERATOR_MODEL/GENERATOR_API_KEY.
    litellm_base_url: str = "http://litellm:4000/v1"
    litellm_master_key: str
    generator_model: str = "generator"

    # Conexion directa a Postgres (esquema `memory`, rol agents_memory; ver
    # infra/supabase/migrations/0003_agents_memory.sql y design.md). El
    # pooler de Supabase exige el project ref como sufijo del usuario.
    agents_pg_host: str
    agents_pg_port: int = 5432
    agents_pg_database: str = "postgres"
    agents_memory_password: str
    supabase_project_ref: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
