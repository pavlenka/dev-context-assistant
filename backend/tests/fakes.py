"""Dobles de prueba: embedder y chat model deterministas para tests sin red ni claves."""

from __future__ import annotations

import hashlib
from typing import Any

from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel

_DIM = 32


def _vector(text: str) -> list[float]:
    """Vector determinista en [0, 1) derivado del hash del texto (mismo texto → mismo vector)."""
    digest = hashlib.sha256(text.encode("utf-8")).digest()  # 32 bytes
    return [byte / 255.0 for byte in digest[:_DIM]]


class FakeEmbedder:
    """Embedder determinista: `embed_query(t)` == `embed_documents([t])[0]`."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [_vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return _vector(text)


class ScriptedChatModel(FakeMessagesListChatModel):
    """Chat model falso que devuelve mensajes guionizados y soporta `bind_tools`.

    `create_agent` llama a `bind_tools`; los fakes de langchain no lo implementan, así que
    lo sobreescribimos para devolver el propio modelo. El loop de tools lo dirigen los
    `tool_calls` de los `AIMessage` guionizados; las tools reales se ejecutan igual.
    """

    def bind_tools(self, tools: Any, **kwargs: Any) -> Any:
        return self
