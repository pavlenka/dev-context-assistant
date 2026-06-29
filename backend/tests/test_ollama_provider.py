"""Tests del proveedor Ollama (construcción offline, sin servidor ni claves)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.agent.graph import build_agent
from app.agent.model import get_chat_model
from app.core.settings import MissingSettingError, Settings
from app.rag.embedder import get_embedder
from app.rag.retriever import Retriever
from app.rag.vector_store import ChromaVectorStore
from tests.fakes import FakeEmbedder


def test_get_chat_model_ollama_no_requiere_clave() -> None:
    model = get_chat_model(Settings(llm_provider="ollama", ollama_model="gemma3"))
    assert type(model).__name__ == "ChatOllama"
    assert model.model == "gemma3"


def test_get_chat_model_anthropic_sin_clave_falla() -> None:
    with pytest.raises(MissingSettingError, match="ANTHROPIC_API_KEY"):
        get_chat_model(Settings(llm_provider="anthropic", anthropic_api_key=None))


def test_get_embedder_ollama_no_requiere_clave() -> None:
    embedder = get_embedder(Settings(embeddings_provider="ollama"))
    assert type(embedder).__name__ == "OllamaEmbeddings"
    assert hasattr(embedder, "embed_query") and hasattr(embedder, "embed_documents")


def test_build_agent_con_ollama_construye_el_grafo(tmp_path: Path) -> None:
    store = ChromaVectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="test")
    retriever = Retriever(FakeEmbedder(), store)
    agent = build_agent(retriever, store, settings=Settings(llm_provider="ollama"))
    assert "tools" in agent.get_graph().nodes
