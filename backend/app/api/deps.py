"""Dependencias compartidas de la API (embedder, vector store y agente).

Se exponen como funciones para poder sobreescribirlas en los tests
(`app.dependency_overrides`) y servir sin red ni claves reales. El store está cacheado por
proceso, de modo que `/ingest` y `/chat` operan sobre el mismo índice.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from fastapi import HTTPException

from app.agent.graph import build_agent
from app.core.settings import MissingSettingError, get_settings
from app.rag.embedder import Embedder, get_embedder
from app.rag.retriever import Retriever
from app.rag.vector_store import ChromaVectorStore, VectorStore


def get_embedder_dependency() -> Embedder:
    """Embedder del proveedor activo; 503 con mensaje claro si falta la clave."""
    try:
        return get_embedder()
    except MissingSettingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@lru_cache
def _default_store() -> VectorStore:
    settings = get_settings()
    return ChromaVectorStore(settings.chroma_persist_dir, settings.chroma_collection)


def get_store_dependency() -> VectorStore:
    """Vector store por defecto (ChromaDB), cacheado por proceso."""
    return _default_store()


@lru_cache
def _default_agent() -> Any:
    store = _default_store()
    return build_agent(Retriever(get_embedder(), store), store)


def get_agent_dependency() -> Any:
    """Agente LangGraph cacheado; 503 con mensaje claro si falta una clave de API."""
    try:
        return _default_agent()
    except MissingSettingError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
