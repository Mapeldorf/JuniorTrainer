from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Unico .env del proyecto: el de la raiz del repo (ver .env.example).
# Se resuelve por ruta absoluta, no relativa al cwd, para que funcione
# igual si el proceso se lanza desde backend/ (venv local), desde la raiz
# o dentro del contenedor Docker (donde ademas las variables ya llegan
# como entorno real via env_file en docker-compose.yml, que tiene
# prioridad sobre este fichero).
_REPO_ROOT_ENV = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Variables de entorno del backend. Ver .env.example en la raiz del repo."""

    model_config = SettingsConfigDict(env_file=_REPO_ROOT_ENV, extra="ignore")

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Origen del frontend, para CORS y para el redirect_to de las invitaciones.
    frontend_url: str = "http://localhost:4200"

    # URLs internas de los tres agentes de generacion (grupo 6), red interna
    # de docker-compose (grupo 7) -- mismos valores por defecto que cada
    # agente anuncia en su propia Agent Card (ver agents/*/app/config.py).
    agent_web_url: str = "http://agent-web:8010/"
    agent_code_url: str = "http://agent-code:8011/"
    agent_exercises_url: str = "http://agent-exercises:8012/"

    # Langfuse Cloud: el backend genera un trace_id por generacion (tarea
    # 6.7) y abre su propio span de orquestacion bajo esa traza.
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_base_url: str = "https://cloud.langfuse.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
