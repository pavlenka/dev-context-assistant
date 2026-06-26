# PLAN — Dev Context Assistant

Plan vivo por fases. Se actualiza al cerrar cada fase. No se avanza de fase sin cerrar
la anterior (commit + resumen).

## Fase 0 — Setup ✅
- [x] 3 skills del proyecto creadas (`code-ingestion`, `rag-retrieval`, `agent-tools`) · `skill-creator` oficial: comandos entregados, lo instala el usuario
- [x] `uv init` backend (Python 3.12), scaffold de carpetas, `ruff` + `pytest` configurados
- [x] Scaffold frontend (Vite + React + TS) · Node fijado en `frontend/.nvmrc` (22.23.1)
- [x] `.env.example` y `core/settings.py` (validación de variables con error claro)

## Fase 1 — Ingestión e indexación
- [ ] Parser con tree-sitter (Python, JS/TS) + fallback por líneas
- [ ] Chunking con metadatos (path, líneas, símbolo, lenguaje)
- [ ] Embeddings (Voyage por defecto) + persistencia en ChromaDB
- [ ] Endpoint `POST /ingest` + tests

## Fase 2 — Retrieval / RAG
- [ ] Búsqueda semántica top-k + ensamblado de contexto con presupuesto de tokens
- [ ] Interfaz `VectorStore` desacoplada (ChromaDB hoy, pgvector mañana)
- [ ] Tests de recuperación con un repo de ejemplo pequeño

## Fase 3 — Agente con tools
- [ ] Grafo LangGraph con las 3 tools (`search_code`, `list_symbols`, `read_file_range`)
- [ ] Citas de origen verificables en la respuesta
- [ ] Memoria de sesión + tests del flujo del agente

## Fase 4 — API FastAPI
- [ ] `POST /chat` con streaming (SSE)
- [ ] Manejo de errores y CORS para el frontend
- [ ] Tests de integración de los endpoints

## Fase 5 — Frontend React/TS
- [ ] Drag & drop de ficheros → llamada a `/ingest`
- [ ] Chat con streaming de tokens
- [ ] Panel de citas (clic en cita → muestra el fragmento)

## Fase 6 — Polish y entrega
- [ ] `Dockerfile` del backend + instrucciones de arranque
- [ ] README con diagrama de arquitectura y pasos de demo
- [ ] Dogfooding: indexar este repo + 3 preguntas de ejemplo en el README
- [ ] (Opcional) GIF de la demo
