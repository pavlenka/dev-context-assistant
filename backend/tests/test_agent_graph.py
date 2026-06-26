"""Tests del grafo del agente con un chat model guionizado (offline, sin LLM real).

Validan el cableado del loop de tools, que la respuesta lleva cita `path:inicio-fin` y que
la memoria de sesión se conserva entre turnos del mismo `thread_id`.
"""

from __future__ import annotations

import re
from pathlib import Path

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

from app.agent.graph import build_agent
from app.ingestion.indexer import index_path
from app.rag.retriever import Retriever
from app.rag.vector_store import ChromaVectorStore
from tests.fakes import FakeEmbedder, ScriptedChatModel

SOURCE = "def find_user(db, uid):\n    return db.get(uid)\n"
CITATION = re.compile(r"\w+\.py:\d+-\d+")


def _agent(tmp_path: Path, responses: list[AIMessage]):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "users.py").write_text(SOURCE)
    store = ChromaVectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="test")
    embedder = FakeEmbedder()
    index_path(repo, embedder=embedder, store=store)
    model = ScriptedChatModel(responses=responses)
    return build_agent(Retriever(embedder, store), store, model=model, checkpointer=MemorySaver())


def test_agente_llama_tool_y_cita_origen(tmp_path: Path) -> None:
    responses = [
        AIMessage(
            content="",
            tool_calls=[{"name": "search_code", "args": {"query": "find_user"}, "id": "c1"}],
        ),
        AIMessage(content="`find_user` se define en users.py:1-2."),
    ]
    agent = _agent(tmp_path, responses)
    result = agent.invoke(
        {"messages": [("user", "¿dónde está find_user?")]},
        {"configurable": {"thread_id": "s1"}},
    )

    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert tool_messages, "la tool search_code debería haberse ejecutado"
    assert "users.py" in str(tool_messages[0].content)  # resultado real, no guionizado
    assert CITATION.search(str(result["messages"][-1].content))  # cita path:inicio-fin


def test_memoria_de_sesion_entre_turnos(tmp_path: Path) -> None:
    responses = [
        AIMessage(content="users.py:1-2 define find_user."),
        AIMessage(content="Como dije, users.py:1-2."),
    ]
    agent = _agent(tmp_path, responses)
    cfg = {"configurable": {"thread_id": "s1"}}

    first = agent.invoke({"messages": [("user", "primera pregunta")]}, cfg)
    second = agent.invoke({"messages": [("user", "repite")]}, cfg)

    # El historial se conserva: el segundo turno incluye los mensajes del primero.
    assert len(second["messages"]) > len(first["messages"])
    assert second["messages"][0].content == "primera pregunta"
