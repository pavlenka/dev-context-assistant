"""Orquestación de la ingesta: ficheros → chunks → embeddings → vector store.

El embedder y el store se inyectan, de modo que la lógica es testeable sin red ni claves.
"""

from __future__ import annotations

import logging
from pathlib import Path

from app.ingestion.chunker import chunk_file
from app.ingestion.languages import detect_language
from app.ingestion.loader import iter_source_files, read_text
from app.models.chunk import CodeChunk
from app.models.ingest import IngestResponse
from app.rag.embedder import Embedder
from app.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)

# Tamaño de lote para llamar al proveedor de embeddings.
_BATCH_SIZE = 64


def index_path(path: str | Path, *, embedder: Embedder, store: VectorStore) -> IngestResponse:
    """Indexa una carpeta o fichero: trocea, embebe y persiste; devuelve estadísticas."""
    root = Path(path)
    base_dir = root if root.is_dir() else root.parent

    all_chunks: list[CodeChunk] = []
    files_indexed = 0
    skipped = 0
    languages: dict[str, int] = {}

    for file_path in iter_source_files(root):
        source = read_text(file_path)
        if source is None:
            skipped += 1
            continue
        language = detect_language(file_path)
        assert language is not None  # iter_source_files ya filtró extensiones desconocidas
        rel_path = file_path.relative_to(base_dir).as_posix()
        abs_path = str(file_path.resolve())
        chunks = chunk_file(rel_path, source, language)
        files_indexed += 1
        for chunk in chunks:
            chunk.abs_path = abs_path
            languages[chunk.language] = languages.get(chunk.language, 0) + 1
        all_chunks.extend(chunks)

    for start in range(0, len(all_chunks), _BATCH_SIZE):
        batch = all_chunks[start : start + _BATCH_SIZE]
        embeddings = embedder.embed_documents([c.content for c in batch])
        store.add(batch, embeddings)

    logger.info(
        "Ingesta completada: %d ficheros, %d chunks, %d saltados",
        files_indexed,
        len(all_chunks),
        skipped,
    )
    return IngestResponse(
        files_indexed=files_indexed,
        chunks_indexed=len(all_chunks),
        skipped=skipped,
        languages=languages,
    )
