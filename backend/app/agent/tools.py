"""Las 3 tools del agente (brief §5) sobre el índice RAG.

Cada tool es tipada, con docstring que el LLM usa para decidir cuándo llamarla, devuelve
un resultado estructurado y nunca propaga excepciones que rompan el grafo: ante un fallo
devuelve `{"error": ...}` (skill `agent-tools`).
"""

from __future__ import annotations

from typing import Any, cast

from langchain_core.tools import BaseTool, tool

from app.rag.retriever import Retriever
from app.rag.source import read_indexed_lines
from app.rag.vector_store import VectorStore


def make_tools(retriever: Retriever, store: VectorStore) -> list[BaseTool]:
    """Crea las tools cerradas sobre el retriever y el store de esta sesión."""

    @tool
    def search_code(query: str, top_k: int = 8) -> list[dict[str, Any]]:
        """Busca semánticamente en el código indexado y devuelve los fragmentos más
        relevantes con su ubicación. Úsala para localizar dónde se implementa algo, hallar
        usos o reunir contexto antes de responder. Devuelve una lista de
        {path, start_line, end_line, snippet, score}."""
        try:
            hits = retriever.search(query, top_k=top_k)
        except Exception as exc:
            return [{"error": f"Fallo en la búsqueda: {exc}"}]
        return [
            {
                "path": h.path,
                "start_line": h.start_line,
                "end_line": h.end_line,
                "snippet": h.snippet,
                "score": round(h.score, 4),
            }
            for h in hits
        ]

    @tool
    def list_symbols(path: str) -> list[dict[str, Any]]:
        """Lista las funciones, clases y métodos indexados de un fichero. `path` es la ruta
        relativa tal como aparece en las citas (p. ej. 'app/main.py'). Devuelve
        [{symbol_name, kind, start_line, end_line}] ordenado por línea, o [] si la ruta no
        está indexada."""
        try:
            metadatas = store.get_by_path(path)
        except Exception as exc:
            return [{"error": f"Fallo al listar símbolos: {exc}"}]
        symbols = [
            {
                "symbol_name": meta.get("symbol_name") or None,
                "kind": meta.get("kind") or None,
                "start_line": int(meta["start_line"]),
                "end_line": int(meta["end_line"]),
            }
            for meta in metadatas
            if meta.get("symbol_name")
        ]
        symbols.sort(key=lambda s: cast(int, s["start_line"]))
        return symbols

    @tool
    def read_file_range(path: str, start: int, end: int) -> dict[str, Any]:
        """Devuelve las líneas exactas [start, end] (1-indexed, inclusive) de un fichero
        indexado, para citar con precisión. Devuelve {path, start, end, content}, o
        {"error": ...} si la ruta no está indexada o no se puede leer."""
        return read_indexed_lines(store, path, start, end)

    return [search_code, list_symbols, read_file_range]
