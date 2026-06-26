"""Schemas de los fragmentos de código (chunks) indexables y recuperados."""

from __future__ import annotations

import hashlib

from pydantic import BaseModel, Field


class CodeChunk(BaseModel):
    """Un fragmento de código listo para embeddings, con metadatos para citar el origen.

    Los metadatos permiten reconstruir la cita exacta `path:start_line-end_line`.
    """

    path: str = Field(description="Ruta relativa a la raíz indexada.")
    start_line: int = Field(description="Primera línea (1-indexed, inclusive).")
    end_line: int = Field(description="Última línea (1-indexed, inclusive).")
    symbol_name: str | None = Field(
        default=None,
        description="Nombre del símbolo (función/clase/método); None en fallback por líneas.",
    )
    kind: str | None = Field(
        default=None,
        description="Tipo de símbolo: 'function', 'class', 'method' o None (módulo/líneas).",
    )
    language: str = Field(description="Lenguaje detectado por extensión.")
    content: str = Field(description="Texto del fragmento.")

    @property
    def chunk_id(self) -> str:
        """ID estable y determinista para upsert idempotente al re-indexar."""
        raw = f"{self.path}:{self.start_line}-{self.end_line}:{self.symbol_name or ''}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()


class RetrievedChunk(BaseModel):
    """Resultado de una búsqueda semántica. Lo consume el retrieval/agente (Fase 2-3)."""

    path: str
    start_line: int
    end_line: int
    snippet: str
    score: float = Field(description="Similitud en [0, 1]; mayor es más relevante.")
    symbol_name: str | None = None
    language: str | None = None
