"""Tests del vector store ChromaDB con embedder determinista (sin red)."""

from __future__ import annotations

from pathlib import Path

from app.models.chunk import CodeChunk
from app.rag.vector_store import ChromaVectorStore
from tests.fakes import FakeEmbedder


def _chunks() -> list[CodeChunk]:
    return [
        CodeChunk(
            path="a.py",
            start_line=1,
            end_line=3,
            symbol_name="parse_config",
            kind="function",
            language="python",
            content="def parse_config(path):\n    return load(path)",
        ),
        CodeChunk(
            path="b.py",
            start_line=10,
            end_line=20,
            symbol_name=None,
            kind=None,
            language="python",
            content="import os\nLEVEL = 'INFO'",
        ),
    ]


def test_add_query_y_round_trip_de_metadatos(tmp_path: Path) -> None:
    store = ChromaVectorStore(persist_dir=str(tmp_path), collection_name="test")
    embedder = FakeEmbedder()
    chunks = _chunks()

    store.add(chunks, embedder.embed_documents([c.content for c in chunks]))
    assert store.count() == 2

    # Consultar con el embedding del primer chunk lo devuelve como mejor resultado.
    results = store.query(embedder.embed_query(chunks[0].content), top_k=2)
    assert results[0].path == "a.py"
    assert results[0].symbol_name == "parse_config"
    assert results[0].start_line == 1
    assert results[0].score == 1.0  # coseno: distancia 0 → similitud 1
    # El centinela de metadatos None se reconstruye como None.
    paths = {r.path: r for r in results}
    assert paths["b.py"].symbol_name is None


def test_upsert_es_idempotente(tmp_path: Path) -> None:
    store = ChromaVectorStore(persist_dir=str(tmp_path), collection_name="test")
    embedder = FakeEmbedder()
    chunks = _chunks()
    embeddings = embedder.embed_documents([c.content for c in chunks])

    store.add(chunks, embeddings)
    store.add(chunks, embeddings)  # re-ingesta del mismo contenido
    assert store.count() == 2
