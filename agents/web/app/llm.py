"""Cliente del modelo `generator` via el proxy de LiteLLM.

Decision de design.md: `langchain-openai` contra el endpoint OpenAI-compatible
de LiteLLM (`http://litellm:4000/v1`), autenticado con `LITELLM_MASTER_KEY`.
Los agentes no hablan con OpenRouter directamente ni conocen el proveedor
real; solo conocen el proxy y el nombre logico del modelo.
"""

from langchain_openai import ChatOpenAI

from app.config import get_settings


def build_generator_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.generator_model,
        base_url=settings.litellm_base_url,
        api_key=settings.litellm_master_key,
        # Sin esto, una llamada colgada al proxy LiteLLM no falla por si
        # sola, y la tarea queda bloqueada hasta que el backend la corte
        # desde fuera a los 120s (change resiliencia-agentes).
        timeout=45.0,
    )
