"""Smoke tests de la app FastAPI y de la validación de settings (Fase 0)."""

import pytest
from fastapi.testclient import TestClient

from app.core.settings import MissingSettingError, Settings
from app.main import app

client = TestClient(app)


def test_health_ok() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_require_anthropic_key_falla_nombrando_la_variable() -> None:
    settings = Settings(anthropic_api_key=None)
    with pytest.raises(MissingSettingError, match="ANTHROPIC_API_KEY"):
        settings.require_anthropic_key()


def test_require_embedding_key_voyage_falla_sin_clave() -> None:
    settings = Settings(embeddings_provider="voyage", voyage_api_key=None)
    with pytest.raises(MissingSettingError, match="VOYAGE_API_KEY"):
        settings.require_embedding_key()
