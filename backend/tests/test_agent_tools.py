"""Tests de las 3 tools del agente contra el índice real (offline, sin LLM)."""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import BaseTool

from app.agent.tools import make_tools
from app.ingestion.chunker import chunk_file
from app.ingestion.indexer import index_path
from app.rag.retriever import Retriever
from app.rag.vector_store import ChromaVectorStore
from tests.fakes import FakeEmbedder

SOURCE = (
    "def find_user(db, uid):\n"
    "    return db.get(uid)\n"
    "\n"
    "\n"
    "class Repo:\n"
    "    def save(self, item):\n"
    "        return item\n"
)


def _tools(tmp_path: Path) -> tuple[BaseTool, BaseTool, BaseTool]:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "users.py").write_text(SOURCE)
    store = ChromaVectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="test")
    embedder = FakeEmbedder()
    index_path(repo, embedder=embedder, store=store)
    search_code, list_symbols, read_file_range = make_tools(Retriever(embedder, store), store)
    return search_code, list_symbols, read_file_range


def test_search_code_devuelve_chunks(tmp_path: Path) -> None:
    search_code, _, _ = _tools(tmp_path)
    chunks = chunk_file("users.py", SOURCE, "python")
    target = next(c for c in chunks if c.symbol_name == "find_user")
    results = search_code.invoke({"query": target.content, "top_k": 3})

    assert results[0]["path"] == "users.py"
    assert {"path", "start_line", "end_line", "snippet", "score"} == set(results[0])
    assert results[0]["score"] == 1.0


def test_list_symbols_lista_simbolos_del_fichero(tmp_path: Path) -> None:
    _, list_symbols, _ = _tools(tmp_path)
    symbols = list_symbols.invoke({"path": "users.py"})
    names = {s["symbol_name"] for s in symbols}

    assert "find_user" in names
    assert "Repo" in names
    assert symbols == sorted(symbols, key=lambda s: s["start_line"])  # ordenado por línea


def test_list_symbols_ruta_desconocida_vacia(tmp_path: Path) -> None:
    _, list_symbols, _ = _tools(tmp_path)
    assert list_symbols.invoke({"path": "no/existe.py"}) == []


def test_read_file_range_lineas_exactas(tmp_path: Path) -> None:
    _, _, read_file_range = _tools(tmp_path)
    result = read_file_range.invoke({"path": "users.py", "start": 1, "end": 2})

    assert result["content"] == "def find_user(db, uid):\n    return db.get(uid)"
    assert result["start"] == 1
    assert result["end"] == 2


def test_read_file_range_ruta_no_indexada_da_error(tmp_path: Path) -> None:
    _, _, read_file_range = _tools(tmp_path)
    result = read_file_range.invoke({"path": "no/existe.py", "start": 1, "end": 5})
    assert "error" in result
