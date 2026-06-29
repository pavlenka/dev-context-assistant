"""Factory del chat model del agente según `LLM_PROVIDER`.

- `anthropic` (por defecto): `claude-sonnet-4-6` vía langchain-anthropic (requiere clave).
- `ollama`: modelo local vía langchain-ollama (sin clave). El modelo debe soportar tool
  calling (p. ej. `gemma3`) para que el agente pueda usar las herramientas.
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel

from app.core.settings import Settings, get_settings

_MAX_TOKENS = 4096


def get_chat_model(settings: Settings | None = None) -> BaseChatModel:
    """Construye el chat model del proveedor activo."""
    settings = settings or get_settings()
    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            num_predict=_MAX_TOKENS,
        )

    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(
        model_name=settings.anthropic_model,
        api_key=settings.require_anthropic_key(),  # type: ignore[arg-type]
        max_tokens_to_sample=_MAX_TOKENS,
        timeout=None,
        stop=None,
    )
