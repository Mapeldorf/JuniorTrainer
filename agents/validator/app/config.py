from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Mismo .env unico del proyecto que usan el backend y los otros agentes
# (ver .env.example en la raiz del repo).
_REPO_ROOT_ENV = Path(__file__).resolve().parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    """Variables de entorno del agente validador de tecnologias. Ver
    .env.example en la raiz del repo."""

    model_config = SettingsConfigDict(env_file=_REPO_ROOT_ENV, extra="ignore")

    # Host/puerto donde este servicio escucha, y la URL publica (dentro de
    # la red de docker-compose) que se anuncia en su Agent Card.
    agent_validator_host: str = "0.0.0.0"
    agent_validator_port: int = 8015
    agent_validator_url: str = "http://agent-validator:8015/"

    # Credencial de servicio backend -> agentes (change
    # autenticacion-backend-agentes): el backend la envia en la cabecera
    # X-Agent-Service-Token en toda llamada A2A; este agente la verifica
    # antes de ejecutar cualquier logica de negocio (ver app/service_auth.py).
    agent_service_token: str

    # Proxy de LiteLLM: modelo logico "validator", definido en
    # infra/litellm/config.yaml, resuelto por LiteLLM via
    # VALIDATOR_MODEL/VALIDATOR_API_KEY. Virtual key propia de este agente
    # (infra/litellm/provision_keys.py), restringida al modelo "validator"
    # y su fallback.
    # Sin campo para el nombre del modelo real (mismo motivo que en los
    # demas agentes, propuesta fix-agent-model-env-collision): el alias
    # logico es una constante en app/llm.py, no Settings -- VALIDATOR_MODEL
    # es una variable que SOLO debe leer infra/litellm/config.yaml.
    litellm_base_url: str = "http://litellm:4000/v1"
    agent_validator_litellm_key: str

    # Conexion directa a Postgres: rol agents_validator_reader, solo SELECT
    # sobre public.technology (change validador-duplicados-tecnologias, ver
    # infra/supabase/migrations/0010_agents_validator_reader.sql y
    # app/tools/technology_catalog.py). El pooler de Supabase exige el
    # project ref como sufijo del usuario, mismo patron que los demas
    # agentes con conexion directa.
    agents_pg_host: str
    agents_pg_port: int = 5432
    agents_pg_database: str = "postgres"
    agents_validator_reader_password: str
    supabase_project_ref: str

    # Langfuse Cloud: igual que el resto de agentes (ver app/tracing.py).
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_base_url: str = "https://cloud.langfuse.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
