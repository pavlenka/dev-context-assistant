"""Router de ingesta: `POST /ingest` (ruta del servidor) y `POST /ingest/upload` (subida)."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import get_embedder_dependency, get_store_dependency
from app.core.settings import get_settings
from app.ingestion.indexer import index_path
from app.models.ingest import IngestRequest, IngestResponse
from app.rag.embedder import Embedder
from app.rag.vector_store import VectorStore

router = APIRouter(tags=["ingest"])


def _safe_relpath(filename: str) -> Path:
    """Convierte el nombre recibido en una ruta relativa segura (sin `..` ni raíz)."""
    parts = [p for p in filename.replace("\\", "/").split("/") if p not in ("", ".", "..")]
    return Path(*parts) if parts else Path("fichero")


@router.post("/ingest", response_model=IngestResponse)
def ingest(
    request: IngestRequest,
    embedder: Annotated[Embedder, Depends(get_embedder_dependency)],
    store: Annotated[VectorStore, Depends(get_store_dependency)],
) -> IngestResponse:
    """Indexa la ruta (carpeta o fichero) del disco del servidor."""
    path = Path(request.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"La ruta no existe: {request.path}")
    return index_path(path, embedder=embedder, store=store)


@router.post("/ingest/upload", response_model=IngestResponse)
async def ingest_upload(
    files: Annotated[list[UploadFile], File()],
    embedder: Annotated[Embedder, Depends(get_embedder_dependency)],
    store: Annotated[VectorStore, Depends(get_store_dependency)],
) -> IngestResponse:
    """Guarda los ficheros subidos (preservando su ruta relativa) y los indexa.

    Se conservan bajo `uploads_dir/<uuid>/` para poder leer fragmentos al citar.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No se subió ningún fichero.")
    dest = Path(get_settings().uploads_dir) / uuid4().hex
    for upload in files:
        target = dest / _safe_relpath(upload.filename or "fichero")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(await upload.read())
    return index_path(dest, embedder=embedder, store=store)
