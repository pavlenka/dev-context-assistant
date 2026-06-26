"""Lectura de líneas exactas de un fichero indexado (compartido por tool y endpoint).

Resuelve la ruta relativa a su `abs_path` (guardado en los metadatos al indexar) y devuelve
las líneas pedidas, o un error estructurado si la ruta no está indexada o no se puede leer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.rag.vector_store import VectorStore


def read_indexed_lines(store: VectorStore, path: str, start: int, end: int) -> dict[str, Any]:
    """Devuelve `{path, start, end, content}` del rango [start, end] o `{error}`."""
    try:
        metadatas = store.get_by_path(path)
    except Exception as exc:
        return {"error": f"Fallo al resolver la ruta: {exc}"}
    abs_path = next((m.get("abs_path") for m in metadatas if m.get("abs_path")), None)
    if not abs_path:
        return {"error": f"La ruta no está indexada: {path}"}
    try:
        lines = Path(str(abs_path)).read_text(encoding="utf-8").split("\n")
    except OSError as exc:
        return {"error": f"No se pudo leer {path}: {exc}"}
    start = max(1, start)
    end = min(len(lines), end)
    if start > end:
        return {"error": f"Rango inválido {start}-{end} para {path}"}
    return {"path": path, "start": start, "end": end, "content": "\n".join(lines[start - 1 : end])}
