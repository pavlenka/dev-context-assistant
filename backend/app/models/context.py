"""Schema del contexto recuperado y ensamblado para el prompt del agente."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.chunk import RetrievedChunk


class AssembledContext(BaseModel):
    """Bloque de contexto listo para el prompt, con los chunks que lo componen.

    `text` se inyecta en el prompt; `chunks` permite al agente citar el origen exacto.
    """

    text: str = Field(description="Snippets formateados con cabecera `path:inicio-fin`.")
    chunks: list[RetrievedChunk] = Field(
        default_factory=list,
        description="Chunks incluidos en `text`, en orden de relevancia.",
    )
