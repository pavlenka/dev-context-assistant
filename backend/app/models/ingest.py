"""Schemas de petición y respuesta del endpoint de ingesta."""

from __future__ import annotations

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    """Petición de ingesta: ruta a una carpeta o fichero del disco del servidor."""

    path: str = Field(description="Ruta absoluta o relativa a una carpeta o fichero.")


class IngestResponse(BaseModel):
    """Estadísticas del resultado de una ingesta."""

    files_indexed: int = Field(description="Ficheros leídos y troceados.")
    chunks_indexed: int = Field(description="Chunks generados y persistidos.")
    skipped: int = Field(description="Ficheros saltados (binarios, no decodificables).")
    languages: dict[str, int] = Field(
        default_factory=dict,
        description="Conteo de chunks por lenguaje.",
    )
