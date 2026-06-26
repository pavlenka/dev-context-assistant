"""Configuración del backend cargada desde variables de entorno / `.env`.

Las claves de API son opcionales al cargar y se validan al usarse, con un error claro
que nombra la variable que falta. Nunca se piden ni se escriben claves en el código.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Raíz del repo: backend/app/core/settings.py -> parents[3].
_REPO_ROOT = Path(__file__).resolve().parents[3]


class MissingSettingError(RuntimeError):
    """Una funcionalidad necesita una variable de entorno que no está configurada."""


class Settings(BaseSettings):
    """Settings tipadas del backend. Lee `.env` de la raíz del repo o variables de entorno."""

    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # LLM (Anthropic)
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-6"

    # Embeddings
    embeddings_provider: Literal["voyage", "openai"] = "voyage"
    voyage_api_key: str | None = None
    voyage_model: str = "voyage-3"
    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"

    # Vector store (ChromaDB local)
    chroma_persist_dir: str = "./.chroma"
    chroma_collection: str = "dev_context"

    def require_anthropic_key(self) -> str:
        """Devuelve la clave de Anthropic o falla nombrando la variable que falta."""
        if not self.anthropic_api_key:
            raise MissingSettingError(
                "Falta ANTHROPIC_API_KEY, requerida para el agente LLM. "
                "Añádela a .env (ver .env.example)."
            )
        return self.anthropic_api_key

    def require_embedding_key(self) -> str:
        """Devuelve la clave del proveedor de embeddings activo o falla con mensaje claro."""
        if self.embeddings_provider == "voyage":
            if not self.voyage_api_key:
                raise MissingSettingError(
                    "Falta VOYAGE_API_KEY, requerida porque EMBEDDINGS_PROVIDER=voyage."
                )
            return self.voyage_api_key
        if not self.openai_api_key:
            raise MissingSettingError(
                "Falta OPENAI_API_KEY, requerida porque EMBEDDINGS_PROVIDER=openai."
            )
        return self.openai_api_key


@lru_cache
def get_settings() -> Settings:
    """Settings cacheadas (un único objeto por proceso)."""
    return Settings()
