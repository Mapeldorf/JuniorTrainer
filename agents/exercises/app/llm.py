"""Cliente del modelo `generator` via el proxy de LiteLLM.

Identico a `agents/web/app/llm.py` y `agents/code/app/llm.py`: decision de
design.md, `langchain-openai` contra el endpoint OpenAI-compatible de
LiteLLM, autenticado con `LITELLM_MASTER_KEY`. El agente no habla con
OpenRouter directamente ni conoce el proveedor real.
"""

from langchain_openai import ChatOpenAI

from app.config import get_settings


def build_generator_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.generator_model,
        base_url=settings.litellm_base_url,
        api_key=settings.litellm_master_key,
    )
