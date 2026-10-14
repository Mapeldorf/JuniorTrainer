"""Cliente del modelo `generator` via el proxy de LiteLLM.

Identico a `agents/web/app/llm.py`: decision de design.md, `langchain-openai`
contra el endpoint OpenAI-compatible de LiteLLM, autenticado con la virtual
key propia de este agente (propuesta litellm-virtual-keys), restringida en
LiteLLM al modelo "generator". El agente no habla con OpenRouter
directamente ni conoce el proveedor real.
"""

from langchain_openai import ChatOpenAI

from app.config import get_settings


def build_generator_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.generator_model,
        base_url=settings.litellm_base_url,
        api_key=settings.agent_code_litellm_key,
        # Sin esto, una llamada colgada al proxy LiteLLM no falla por si
        # sola, y la tarea queda bloqueada hasta que el backend la corte
        # desde fuera a los 120s (change resiliencia-agentes).
        timeout=45.0,
    )
