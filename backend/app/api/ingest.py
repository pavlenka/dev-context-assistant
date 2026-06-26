"""Router de ingesta: `POST /ingest` indexa una carpeta o fichero del disco."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_embedder_dependency, get_store_dependency
from app.ingestion.indexer import index_path
from app.models.ingest import IngestRequest, IngestResponse
from app.rag.embedder import Embedder
from app.rag.vector_store import VectorStore

router = APIRouter(tags=["ingest"])


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
