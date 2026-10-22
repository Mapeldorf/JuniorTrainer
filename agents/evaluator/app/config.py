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

    # Credencial de servicio backend -> agentes (change
    # autenticacion-backend-agentes): el backend la envia en la cabecera
    # X-Agent-Service-Token en toda llamada A2A; este agente la verifica
    # antes de ejecutar cualquier logica de negocio (ver app/service_auth.py).
    agent_service_token: str

    # Proxy de LiteLLM (seccion 11 de la especificacion): modelo logico
    # "evaluator", ya predefinido en infra/litellm/config.yaml, resuelto
    # por LiteLLM via EVALUATOR_MODEL/EVALUATOR_API_KEY.
    # Virtual key propia de este agente (propuesta litellm-virtual-keys),
    # restringida en LiteLLM al modelo "evaluator": ya no se usa la
    # LITELLM_MASTER_KEY compartida para llamadas de negocio.
    # Sin campo para el nombre del modelo logico (propuesta
    # fix-agent-model-env-collision): es una constante en app/llm.py, no
    # Settings -- EVALUATOR_MODEL es una variable que SOLO debe leer
    # infra/litellm/config.yaml; como env_file: .env tambien se la pasa a
    # este contenedor, un campo Settings con ese mismo nombre de variable
    # (por convencion de pydantic-settings) acababa leyendo por error el
    # nombre de proveedor real en vez del alias logico fijo.
    litellm_base_url: str = "http://litellm:4000/v1"
    agent_evaluator_litellm_key: str

    # Presidio autoalojado (change guardarrailes-por-capas): este agente
    # redacta la respuesta del alumno al montar el prompt, no en el proxy,
    # porque es la unica capa que sabe que campo escribio una persona (ver
    # app/redaction.py). A diferencia de EVALUATOR_MODEL, aqui NO hay
    # colision de nombres con la configuracion de LiteLLM: el valor es el
    # mismo para los dos consumidores (la URL del servicio) y significa lo
    # mismo, asi que leerlo de la misma variable es correcto.
    presidio_analyzer_api_base: str = "http://presidio-analyzer:3000"
    presidio_anonymizer_api_base: str = "http://presidio-anonymizer:3000"

    # Langfuse Cloud: igual que el resto de agentes (ver app/tracing.py).
    langfuse_public_key: str
    langfuse_secret_key: str
    langfuse_base_url: str = "https://cloud.langfuse.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()
