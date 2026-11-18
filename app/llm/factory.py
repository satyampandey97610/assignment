"""LLM factory initializing chat models based on environment configuration."""

from typing import Any
from langchain.chat_models import init_chat_model
from langchain_core.language_models.chat_models import BaseChatModel

from app.config import settings

_chat_model: BaseChatModel | None = None


def get_chat_model(
    model: str | None = None,
    provider: str | None = None,
    temperature: float = 0.0,
    **kwargs: Any,
) -> BaseChatModel:
    """Initialize or return provider-agnostic ChatModel via LangChain init_chat_model."""
    target_model = model or settings.LLM_MODEL
    target_provider = provider or settings.LLM_PROVIDER

    extra_kwargs = dict(kwargs)
    if target_provider == "openai" and settings.OPENAI_API_KEY:
        extra_kwargs["api_key"] = settings.OPENAI_API_KEY
    elif target_provider == "anthropic" and settings.ANTHROPIC_API_KEY:
        extra_kwargs["api_key"] = settings.ANTHROPIC_API_KEY

    return init_chat_model(
        model=target_model,
        model_provider=target_provider,
        temperature=temperature,
        **extra_kwargs,
    )
