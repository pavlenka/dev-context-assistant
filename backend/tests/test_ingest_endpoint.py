"""Tests de integración del endpoint POST /ingest (dependencias sobreescritas, sin red)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api import ingest as ingest_api
from app.api.ingest import get_embedder_dependency, get_store_dependency
from app.core.settings import MissingSettingError
from app.main import app
from app.rag.vector_store import ChromaVectorStore
from tests.fakes import FakeEmbedder


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    store = ChromaVectorStore(persist_dir=str(tmp_path / "chroma"), collection_name="test")
    app.dependency_overrides[get_embedder_dependency] = FakeEmbedder
    app.dependency_overrides[get_store_dependency] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_ingest_carpeta_devuelve_stats(client: TestClient, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "mod.py").write_text(
        "def foo(x):\n    return x\n\n\nclass Bar:\n    def m(self):\n        return 1\n"
    )
    (repo / "util.js").write_text("export function add(a, b) { return a + b; }\n")

    resp = client.post("/ingest", json={"path": str(repo)})
    assert resp.status_code == 200
    body = resp.json()
    assert body["files_indexed"] == 2
    assert body["chunks_indexed"] >= 2
    assert body["languages"].get("python", 0) >= 1
    assert body["languages"].get("javascript", 0) >= 1


def test_ingest_ruta_inexistente_da_404(client: TestClient) -> None:
    resp = client.post("/ingest", json={"path": "/no/existe/aqui"})
    assert resp.status_code == 404


def test_get_embedder_dependency_mapea_clave_faltante_a_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _raise() -> None:
        raise MissingSettingError("Falta VOYAGE_API_KEY")

    monkeypatch.setattr(ingest_api, "get_embedder", _raise)
    with pytest.raises(HTTPException) as exc:
        get_embedder_dependency()
    assert exc.value.status_code == 503
    assert "VOYAGE_API_KEY" in str(exc.value.detail)
