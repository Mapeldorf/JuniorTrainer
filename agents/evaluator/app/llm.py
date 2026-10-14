"""Cliente del modelo `evaluator` via el proxy de LiteLLM.

Identico en estructura a `agents/exercises/app/llm.py`: `langchain-openai`
contra el endpoint OpenAI-compatible de LiteLLM, autenticado con la virtual
key propia de este agente (propuesta litellm-virtual-keys), restringida en
LiteLLM al modelo "evaluator". El agente no habla con OpenRouter
directamente ni conoce el proveedor real.
"""

from langchain_openai import ChatOpenAI

from app.config import get_settings

# Alias logico fijo (ver infra/litellm/config.yaml model_list), no Settings:
# ver nota en app/config.py (propuesta fix-agent-model-env-collision).
_MODEL_NAME = "evaluator"


def build_evaluator_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=_MODEL_NAME,
        base_url=settings.litellm_base_url,
        api_key=settings.agent_evaluator_litellm_key,
        # Sin esto, una llamada colgada al proxy LiteLLM no falla por si
        # sola, y la tarea queda bloqueada hasta que el backend la corte
        # desde fuera a los 120s (change resiliencia-agentes).
        timeout=45.0,
    )
