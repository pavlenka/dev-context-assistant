"""Tests de `POST /ingest/upload` y `GET /source` (offline, dependencias sobreescritas)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import ingest as ingest_api
from app.api.deps import get_embedder_dependency, get_store_dependency
from app.core.settings import Settings
from app.main import app
from app.rag.vector_store import ChromaVectorStore
from tests.fakes import FakeEmbedder


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    store = ChromaVectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="test")
    app.dependency_overrides[get_embedder_dependency] = FakeEmbedder
    app.dependency_overrides[get_store_dependency] = lambda: store
    monkeypatch.setattr(
        ingest_api, "get_settings", lambda: Settings(uploads_dir=str(tmp_path / "uploads"))
    )
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_upload_indexa_y_source_lee_el_fragmento(client: TestClient) -> None:
    files = [("files", ("pkg/mod.py", b"def foo(x):\n    return x\n", "text/x-python"))]
    resp = client.post("/ingest/upload", files=files)
    assert resp.status_code == 200
    assert resp.json()["chunks_indexed"] >= 1

    # El fichero subido quedó indexado y se puede leer su fragmento exacto.
    src = client.get("/source", params={"path": "pkg/mod.py", "start": 1, "end": 2})
    assert src.status_code == 200
    assert src.json()["content"] == "def foo(x):\n    return x"


def test_source_ruta_desconocida_da_404(client: TestClient) -> None:
    resp = client.get("/source", params={"path": "no/existe.py", "start": 1, "end": 5})
    assert resp.status_code == 404
