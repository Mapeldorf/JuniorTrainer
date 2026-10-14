"""Cliente del modelo `generator` via el proxy de LiteLLM.

Decision de design.md: `langchain-openai` contra el endpoint OpenAI-compatible
de LiteLLM (`http://litellm:4000/v1`), autenticado con la virtual key propia
de este agente (propuesta litellm-virtual-keys), restringida en LiteLLM al
modelo "generator". Los agentes no hablan con OpenRouter directamente ni
conocen el proveedor real; solo conocen el proxy y el nombre logico del
modelo.
"""

from langchain_openai import ChatOpenAI

from app.config import get_settings

# Alias logico fijo (ver infra/litellm/config.yaml model_list), no Settings:
# ver nota en app/config.py (propuesta fix-agent-model-env-collision).
_MODEL_NAME = "generator"


def build_generator_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=_MODEL_NAME,
        base_url=settings.litellm_base_url,
        api_key=settings.agent_web_litellm_key,
        # Sin esto, una llamada colgada al proxy LiteLLM no falla por si
        # sola, y la tarea queda bloqueada hasta que el backend la corte
        # desde fuera a los 120s (change resiliencia-agentes).
        timeout=45.0,
    )
