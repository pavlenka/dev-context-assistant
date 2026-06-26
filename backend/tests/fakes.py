"""Dobles de prueba: embedder determinista para tests sin red ni claves."""

from __future__ import annotations

import hashlib

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
