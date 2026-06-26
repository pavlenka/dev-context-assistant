---
name: rag-retrieval
description: Convenciones de embeddings y recuperación para el RAG. Úsala al implementar o ajustar backend/app/rag: modelo de embeddings, tamaño/solape de chunk, top_k y ensamblado del contexto recuperado dentro del presupuesto de tokens.
---

# RAG Retrieval

## Embeddings
- Proveedor por defecto: **Voyage** (`voyage-3`). Alternativa: OpenAI
  (`text-embedding-3-small`), seleccionable por `EMBEDDINGS_PROVIDER` en `.env`.
- Aislar el proveedor tras una interfaz `Embedder` para poder cambiarlo sin tocar el resto.

## Parámetros
- `top_k` por defecto: **8**.
- Chunk: por símbolo (ver skill `code-ingestion`); fallback ~60 líneas / 10 de solape.

## Vector store
- ChromaDB local para el MVP, detrás de una interfaz `VectorStore` (`add`, `query`) para
  permitir migrar a pgvector más adelante sin tocar el agente.

## Ensamblado de contexto
- Recuperar `top_k`, ordenar por score y concatenar snippets hasta un **presupuesto de
  tokens** configurable. Cortar por chunks completos, nunca a media línea.
- Cada chunk inyectado conserva su cabecera `path:start_line-end_line` para que el agente cite.
- Si no hay resultados relevantes, devolver vacío y que el agente lo diga; no inventar rutas.
