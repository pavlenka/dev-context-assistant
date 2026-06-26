"""Router de fragmentos: `GET /source` devuelve líneas exactas de un fichero indexado.

Lo usa el panel de citas del frontend (clic en una cita → muestra el fragmento).
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_store_dependency
from app.rag.source import read_indexed_lines
from app.rag.vector_store import VectorStore

router = APIRouter(tags=["source"])


@router.get("/source")
def source(
    store: Annotated[VectorStore, Depends(get_store_dependency)],
    path: Annotated[str, Query(description="Ruta relativa indexada.")],
    start: Annotated[int, Query(ge=1, description="Línea inicial (1-indexed).")],
    end: Annotated[int, Query(ge=1, description="Línea final (inclusive).")],
) -> dict[str, Any]:
    """Devuelve `{path, start, end, content}` o 404 si la ruta no está indexada/legible."""
    result = read_indexed_lines(store, path, start, end)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
