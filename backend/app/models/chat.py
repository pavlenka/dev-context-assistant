"""Schema de la petición de chat."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Mensaje del usuario y, opcionalmente, el id de sesión (memoria por `thread_id`)."""

    message: str = Field(min_length=1, description="Pregunta del usuario.")
    session_id: str | None = Field(
        default=None,
        description="Id de sesión para conservar la memoria; se genera si falta.",
    )
