from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Variables de entorno del backend. Ver infra/.env.example."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str

    # Origen del frontend, para CORS y para el redirect_to de las invitaciones.
    frontend_url: str = "http://localhost:4200"


@lru_cache
def get_settings() -> Settings:
    return Settings()
