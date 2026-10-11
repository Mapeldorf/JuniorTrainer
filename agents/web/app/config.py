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


@lru_cache
def get_settings() -> Settings:
    return Settings()
