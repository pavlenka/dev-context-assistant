"""Router de chat: `POST /chat` responde en streaming (SSE) con citas de origen.

Cada evento es una línea `data: {json}\\n\\n` con un campo `type`:
- `token`: fragmento de texto de la respuesta.
- `done`: fin del turno, con `session_id` y `citations` (path:inicio-fin parseadas).
- `error`: fallo durante la generación.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from collections.abc import AsyncIterator
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage

from app.api.deps import get_agent_dependency
from app.models.chat import ChatRequest

logger = logging.getLogger(__name__)
router = APIRouter(tags=["chat"])

# Cita de origen: ruta de fichero + rango de líneas (p. ej. app/main.py:10-19).
_CITATION = re.compile(r"([\w./-]+\.[A-Za-z0-9]+):(\d+)-(\d+)")


def _sse(event_type: str, **data: Any) -> str:
    """Serializa un evento SSE: `data: {json}\\n\\n`."""
    return f"data: {json.dumps({'type': event_type, **data}, ensure_ascii=False)}\n\n"


def _text_of(chunk: AIMessage) -> str:
    """Extrae el texto de un chunk del asistente (content str o lista de bloques)."""
    content = chunk.content
    if isinstance(content, str):
        return content
    parts = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
    return "".join(parts)


def _parse_citations(text: str) -> list[dict[str, Any]]:
    """Extrae citas `path:inicio-fin` del texto, sin duplicados y en orden de aparición."""
    seen: set[tuple[str, int, int]] = set()
    citations: list[dict[str, Any]] = []
    for path, start, end in _CITATION.findall(text):
        key = (path, int(start), int(end))
        if key not in seen:
            seen.add(key)
            citations.append({"path": path, "start_line": int(start), "end_line": int(end)})
    return citations


async def _stream_answer(agent: Any, message: str, thread_id: str) -> AsyncIterator[str]:
    """Genera los eventos SSE de un turno de chat."""
    config = {"configurable": {"thread_id": thread_id}}
    answer: list[str] = []
    try:
        async for chunk, _meta in agent.astream(
            {"messages": [("user", message)]}, config, stream_mode="messages"
        ):
            if isinstance(chunk, AIMessage):
                text = _text_of(chunk)
                if text:
                    answer.append(text)
                    yield _sse("token", content=text)
    except Exception as exc:
        logger.exception("Fallo generando la respuesta del chat")
        yield _sse("error", detail=str(exc))
        return
    yield _sse("done", session_id=thread_id, citations=_parse_citations("".join(answer)))


@router.post("/chat")
def chat(
    request: ChatRequest,
    agent: Annotated[Any, Depends(get_agent_dependency)],
) -> StreamingResponse:
    """Responde la pregunta en streaming (SSE), citando el origen en el código."""
    thread_id = request.session_id or str(uuid.uuid4())
    return StreamingResponse(
        _stream_answer(agent, request.message, thread_id),
        media_type="text/event-stream",
    )
