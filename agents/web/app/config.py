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

    # Credencial de servicio backend -> agentes (change
    # autenticacion-backend-agentes): el backend la envia en la cabecera
    # X-Agent-Service-Token en toda llamada A2A; este agente la verifica
    # antes de ejecutar cualquier logica de negocio (ver app/service_auth.py).
    agent_service_token: str

    tavily_api_key: str

    # Proxy de LiteLLM (seccion 11 de la especificacion): modelo logico
    # "generator", resuelto por LiteLLM via GENERATOR_MODEL/GENERATOR_API_KEY.
    # Virtual key propia de este agente (propuesta litellm-virtual-keys),
    # restringida en LiteLLM al modelo "generator": ya no se usa la
    # LITELLM_MASTER_KEY compartida para llamadas de negocio.
    # Sin campo para el nombre del modelo logico (propuesta
    # fix-agent-model-env-collision): es una constante en app/llm.py, no
    # Settings -- GENERATOR_MODEL es una variable que SOLO debe leer
    # infra/litellm/config.yaml; como env_file: .env tambien se la pasa a
    # este contenedor, un campo Settings con ese mismo nombre de variable
    # (por convencion de pydantic-settings) acababa leyendo por error el
    # nombre de proveedor real en vez del alias logico fijo.
    litellm_base_url: str = "http://litellm:4000/v1"
    agent_web_litellm_key: str

    # Conexion directa a Postgres (esquema `memory`, rol agents_memory; ver
    # infra/supabase/migrations/0003_agents_memory.sql y design.md). El
    # pooler de Supabase exige el project ref como sufijo del usuario.
    agents_pg_host: str
    agents_pg_port: int = 5432
    agents_pg_database: str = "postgres"
    agents_memory_password: str
    supabase_project_ref: str

    # Langfuse Cloud (tarea 3.6): el SDK de Langfuse lee estas variables de
    # os.environ por su cuenta, pero este servicio las pasa explicitamente
    # al construir el cliente (app/tracing.py), igual que el resto de
    # credenciales -- no confiamos en que .env (leido solo por
    # pydantic-settings) haya llegado tambien al entorno real del proceso.
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_base_url: str = "https://cloud.langfuse.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
