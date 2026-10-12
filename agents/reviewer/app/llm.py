"""Cliente del modelo `reviewer` via el proxy de LiteLLM. Identico en
estructura a `agents/evaluator/app/llm.py`."""

from langchain_openai import ChatOpenAI

from app.config import get_settings


def build_reviewer_model() -> ChatOpenAI:
    settings = get_settings()
    return ChatOpenAI(
        model=settings.reviewer_model,
        base_url=settings.litellm_base_url,
        api_key=settings.litellm_master_key,
    )
