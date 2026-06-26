"""Embeddings tras una interfaz `Embedder` para poder cambiar de proveedor.

Voyage (`voyage-3`) es el proveedor por defecto; OpenAI es la alternativa configurable
por `EMBEDDINGS_PROVIDER` en `.env`. Las claves se validan al construir el embedder, con
un error claro que nombra la variable que falta (ver `core/settings.py`).
"""

from __future__ import annotations

from typing import Protocol, cast

from app.core.settings import Settings, get_settings


class Embedder(Protocol):
    """Convierte texto en vectores. Documentos y consulta pueden usar prompts distintos."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Vectoriza un lote de documentos (chunks de código)."""
        ...

    def embed_query(self, text: str) -> list[float]:
        """Vectoriza una consulta de búsqueda."""
        ...


class VoyageEmbedder:
    """Embeddings con Voyage AI."""

    def __init__(self, api_key: str, model: str) -> None:
        import voyageai

        self._client = voyageai.Client(api_key=api_key)
        self._model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        result = self._client.embed(texts, model=self._model, input_type="document")
        return cast(list[list[float]], result.embeddings)

    def embed_query(self, text: str) -> list[float]:
        result = self._client.embed([text], model=self._model, input_type="query")
        return cast(list[float], result.embeddings[0])


class OpenAIEmbedder:
    """Embeddings con OpenAI (alternativa configurable)."""

    def __init__(self, api_key: str, model: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        resp = self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in resp.data]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


def get_embedder(settings: Settings | None = None) -> Embedder:
    """Construye el embedder del proveedor activo, validando su clave de API."""
    settings = settings or get_settings()
    api_key = settings.require_embedding_key()
    if settings.embeddings_provider == "voyage":
        return VoyageEmbedder(api_key=api_key, model=settings.voyage_model)
    return OpenAIEmbedder(api_key=api_key, model=settings.openai_embedding_model)
