"""Cliente del modelo `reviewer` via el proxy de LiteLLM. Identico en
estructura a `agents/evaluator/app/llm.py`."""

from langchain_openai import ChatOpenAI

from app.config import get_settings

# Alias logico fijo (ver infra/litellm/config.yaml model_list), no Settings:
# ver nota en app/config.py (propuesta fix-agent-model-env-collision).
_MODEL_NAME = "reviewer"


def build_reviewer_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=_MODEL_NAME,
        base_url=settings.litellm_base_url,
        api_key=settings.agent_reviewer_litellm_key,
        # Sin esto, una llamada colgada al proxy LiteLLM no falla por si
        # sola, y la tarea queda bloqueada hasta que el backend la corte
        # desde fuera a los 120s (change resiliencia-agentes).
        timeout=45.0,
    )
