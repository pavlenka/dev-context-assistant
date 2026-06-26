"""Vector store tras una interfaz `VectorStore` para poder migrar de backend.

ChromaDB local es el backend del MVP; la interfaz (`add`, `query`, `count`) permite
cambiar a pgvector más adelante sin tocar el agente. Siempre pasamos los embeddings
explícitamente, por lo que la embedding function por defecto de Chroma nunca se invoca.
"""

from __future__ import annotations

from typing import Protocol, cast

from app.models.chunk import CodeChunk, RetrievedChunk

# Centinela para metadatos: Chroma no admite valores None.
_NONE = ""


class VectorStore(Protocol):
    """Almacén vectorial de chunks de código."""

    def add(self, chunks: list[CodeChunk], embeddings: list[list[float]]) -> None:
        """Inserta (o actualiza, upsert) chunks con sus embeddings."""
        ...

    def query(self, embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        """Devuelve los `top_k` chunks más similares al embedding de consulta."""
        ...

    def count(self) -> int:
        """Número de chunks almacenados."""
        ...


class ChromaVectorStore:
    """Implementación sobre ChromaDB persistente en disco (distancia coseno)."""

    def __init__(self, persist_dir: str, collection_name: str) -> None:
        import chromadb

        client = chromadb.PersistentClient(path=persist_dir)
        self._collection = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, chunks: list[CodeChunk], embeddings: list[list[float]]) -> None:
        if not chunks:
            return
        self._collection.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,  # type: ignore[arg-type]
            documents=[c.content for c in chunks],
            metadatas=[
                {
                    "path": c.path,
                    "start_line": c.start_line,
                    "end_line": c.end_line,
                    "symbol_name": c.symbol_name or _NONE,
                    "kind": c.kind or _NONE,
                    "language": c.language,
                }
                for c in chunks
            ],
        )

    def query(self, embedding: list[float], top_k: int) -> list[RetrievedChunk]:
        res = self._collection.query(
            query_embeddings=[embedding],  # type: ignore[arg-type]
            n_results=top_k,
        )
        documents = (res.get("documents") or [[]])[0]
        metadatas = (res.get("metadatas") or [[]])[0]
        distances = (res.get("distances") or [[]])[0]

        results: list[RetrievedChunk] = []
        for doc, meta, dist in zip(documents, metadatas, distances, strict=True):
            symbol_name = meta.get("symbol_name") or None
            results.append(
                RetrievedChunk(
                    path=str(meta["path"]),
                    start_line=int(cast(int, meta["start_line"])),
                    end_line=int(cast(int, meta["end_line"])),
                    snippet=doc,
                    score=1.0 - float(dist),  # coseno: distancia -> similitud
                    symbol_name=str(symbol_name) if symbol_name else None,
                    language=str(meta.get("language") or "") or None,
                )
            )
        return results

    def count(self) -> int:
        return self._collection.count()
