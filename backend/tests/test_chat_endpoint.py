"""Tests de integración de `POST /chat` (SSE) con agente guionizado, sin red."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import MemorySaver

from app.agent.graph import build_agent
from app.api.deps import get_agent_dependency
from app.ingestion.indexer import index_path
from app.main import app
from app.rag.retriever import Retriever
from app.rag.vector_store import ChromaVectorStore
from tests.fakes import FakeEmbedder, ScriptedChatModel

SOURCE = "def find_user(db, uid):\n    return db.get(uid)\n"


def _parse_sse(body: str) -> list[dict[str, Any]]:
    events = []
    for block in body.strip().split("\n\n"):
        line = block.strip()
        if line.startswith("data:"):
            events.append(json.loads(line[len("data:") :].strip()))
    return events


def _build_scripted_agent(tmp_path: Path, answer: str) -> Any:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "users.py").write_text(SOURCE)
    store = ChromaVectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="test")
    embedder = FakeEmbedder()
    index_path(repo, embedder=embedder, store=store)
    model = ScriptedChatModel(responses=[AIMessage(content=answer)])
    return build_agent(Retriever(embedder, store), store, model=model, checkpointer=MemorySaver())


@pytest.fixture
def client() -> Iterator[TestClient]:
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_chat_streamea_tokens_y_done_con_citas(client: TestClient, tmp_path: Path) -> None:
    agent = _build_scripted_agent(tmp_path, "`find_user` se define en users.py:1-2.")
    app.dependency_overrides[get_agent_dependency] = lambda: agent

    resp = client.post("/chat", json={"message": "¿dónde está find_user?", "session_id": "s1"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")

    events = _parse_sse(resp.text)
    tokens = [e for e in events if e["type"] == "token"]
    done = [e for e in events if e["type"] == "done"]
    assert "".join(e["content"] for e in tokens) == "`find_user` se define en users.py:1-2."
    assert done[0]["session_id"] == "s1"
    assert {"path": "users.py", "start_line": 1, "end_line": 2} in done[0]["citations"]


def test_chat_emite_evento_error_si_falla(client: TestClient) -> None:
    class _BoomAgent:
        async def astream(self, *args: Any, **kwargs: Any) -> AsyncIterator[Any]:
            raise RuntimeError("boom")
            yield  # pragma: no cover  (convierte el método en generador async)

    app.dependency_overrides[get_agent_dependency] = lambda: _BoomAgent()

    resp = client.post("/chat", json={"message": "hola"})
    events = _parse_sse(resp.text)
    assert events[-1]["type"] == "error"
    assert "boom" in events[-1]["detail"]


def test_chat_mensaje_vacio_da_422(client: TestClient) -> None:
    app.dependency_overrides[get_agent_dependency] = lambda: object()
    assert client.post("/chat", json={"message": ""}).status_code == 422


def test_cors_header_presente(client: TestClient) -> None:
    resp = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert resp.headers.get("access-control-allow-origin") == "http://localhost:5173"
