from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Mismo .env unico del proyecto que usa el backend y los otros dos agentes
# (ver .env.example en la raiz del repo).
_REPO_ROOT_ENV = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Variables de entorno del agente de ejercicios. Ver .env.example en la raiz del repo."""

    model_config = SettingsConfigDict(env_file=_REPO_ROOT_ENV, extra="ignore")

    # Host/puerto donde este servicio escucha, y la URL publica (dentro de la
    # red de docker-compose) que se anuncia en su Agent Card.
    agent_exercises_host: str = "0.0.0.0"
    agent_exercises_port: int = 8012
    agent_exercises_url: str = "http://agent-exercises:8012/"

    # Proxy de LiteLLM (seccion 11 de la especificacion): modelo logico
    # "generator", resuelto por LiteLLM via GENERATOR_MODEL/GENERATOR_API_KEY.
    litellm_base_url: str = "http://litellm:4000/v1"
    litellm_master_key: str
    generator_model: str = "generator"

    # Conexion directa a Postgres: agents_memory (esquema `memory`, memoria
    # larga de enunciados ya propuestos, tarea 5.4) y agents_exercise_reader
    # (solo SELECT sobre public.exercise, tarea 5.2) -- dos roles distintos,
    # ver infra/supabase/migrations/0003_agents_memory.sql y design.md
    # "Contrato de entrada/salida del agente de ejercicios". El pooler de
    # Supabase exige el project ref como sufijo del usuario en ambos casos.
    agents_pg_host: str
    agents_pg_port: int = 5432
    agents_pg_database: str = "postgres"
    agents_memory_password: str
    agents_exercise_reader_password: str
    supabase_project_ref: str

    # Langfuse Cloud: el SDK lee os.environ por su cuenta, pero este
    # servicio las pasa explicitamente al construir el cliente (ver
    # app/tracing.py), igual que el resto de credenciales.
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_base_url: str = "https://cloud.langfuse.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
