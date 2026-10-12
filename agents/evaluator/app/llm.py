"""Cliente del modelo `evaluator` via el proxy de LiteLLM.

Identico en estructura a `agents/exercises/app/llm.py`: `langchain-openai`
contra el endpoint OpenAI-compatible de LiteLLM, autenticado con
`LITELLM_MASTER_KEY`. El agente no habla con OpenRouter directamente ni
conoce el proveedor real.
"""

from langchain_openai import ChatOpenAI

from app.config import get_settings


def build_evaluator_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.evaluator_model,
        base_url=settings.litellm_base_url,
        api_key=settings.litellm_master_key,
    )
