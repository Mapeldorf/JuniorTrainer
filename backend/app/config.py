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


@lru_cache
def get_settings() -> Settings:
    return Settings()
