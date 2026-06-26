"""Router de ingesta: `POST /ingest` indexa una carpeta o fichero del disco.

El embedder y el vector store se exponen como dependencias para poder sobreescribirlos
en los tests (`app.dependency_overrides`) y servir sin red ni claves reales.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.settings import MissingSettingError, get_settings
from app.ingestion.indexer import index_path
from app.models.ingest import IngestRequest, IngestResponse
from app.rag.embedder import Embedder, get_embedder
from app.rag.vector_store import ChromaVectorStore, VectorStore

router = APIRouter(tags=["ingest"])


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


@router.post("/ingest", response_model=IngestResponse)
def ingest(
    request: IngestRequest,
    embedder: Annotated[Embedder, Depends(get_embedder_dependency)],
    store: Annotated[VectorStore, Depends(get_store_dependency)],
) -> IngestResponse:
    """Indexa la ruta indicada y devuelve estadísticas de la ingesta."""
    path = Path(request.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"La ruta no existe: {request.path}")
    return index_path(path, embedder=embedder, store=store)
