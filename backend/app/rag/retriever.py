"""Recuperación semántica: orquesta el embedder y el vector store.

Es la pieza que consumirá la tool `search_code` del agente (Fase 3).
"""

from __future__ import annotations

from app.models.chunk import RetrievedChunk
from app.rag.embedder import Embedder
from app.rag.vector_store import VectorStore


class Retriever:
    """Busca los chunks más relevantes para una consulta en lenguaje natural."""

    def __init__(self, embedder: Embedder, store: VectorStore) -> None:
        self._embedder = embedder
        self._store = store

    def search(self, query: str, top_k: int = 8) -> list[RetrievedChunk]:
        """Devuelve hasta `top_k` chunks ordenados por relevancia (mayor score primero)."""
        if not query.strip() or top_k <= 0:
            return []
        embedding = self._embedder.embed_query(query)
        return self._store.query(embedding, top_k)
