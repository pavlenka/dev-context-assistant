"""Test de recuperación de punta a punta con un repo de ejemplo pequeño (offline)."""

from __future__ import annotations

from pathlib import Path

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
    "def delete_user(db, uid):\n"
    "    return db.pop(uid)\n"
)


def _seed_store(tmp_path: Path) -> tuple[Retriever, FakeEmbedder]:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "users.py").write_text(SOURCE)
    store = ChromaVectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="test")
    embedder = FakeEmbedder()
    response = index_path(repo, embedder=embedder, store=store)
    assert response.chunks_indexed >= 2
    return Retriever(embedder, store), embedder


def test_search_recupera_el_simbolo_relevante(tmp_path: Path) -> None:
    retriever, _ = _seed_store(tmp_path)
    # El embedder determinista hace que consultar con el contenido exacto de un símbolo
    # lo devuelva como mejor resultado (distancia 0 → score 1).
    chunks = chunk_file("users.py", SOURCE, "python")
    target = next(c for c in chunks if c.symbol_name == "find_user")

    results = retriever.search(target.content, top_k=5)
    assert results[0].symbol_name == "find_user"
    assert results[0].path == "users.py"
    assert results[0].score == 1.0


def test_search_respeta_top_k(tmp_path: Path) -> None:
    retriever, _ = _seed_store(tmp_path)
    assert len(retriever.search("def", top_k=1)) == 1


def test_search_consulta_vacia_devuelve_lista_vacia(tmp_path: Path) -> None:
    retriever, _ = _seed_store(tmp_path)
    assert retriever.search("   ", top_k=5) == []
    assert retriever.search("def", top_k=0) == []
