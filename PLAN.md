# PLAN — Dev Context Assistant

Plan vivo por fases. Se actualiza al cerrar cada fase. No se avanza de fase sin cerrar
la anterior (commit + resumen).

## Fase 0 — Setup ✅
- [x] 3 skills del proyecto creadas (`code-ingestion`, `rag-retrieval`, `agent-tools`) · `skill-creator` oficial: comandos entregados, lo instala el usuario
- [x] `uv init` backend (Python 3.12), scaffold de carpetas, `ruff` + `pytest` configurados
- [x] Scaffold frontend (Vite + React + TS) · Node fijado en `frontend/.nvmrc` (22.23.1)
- [x] `.env.example` y `core/settings.py` (validación de variables con error claro)

## Fase 1 — Ingestión e indexación ✅
- [x] Parser con tree-sitter (Python, JS/TS) + fallback por líneas · gramáticas de
  `tree-sitter-language-pack` con el API estándar de `tree_sitter` (offline, sin descargas)
- [x] Chunking con metadatos (path, líneas, símbolo, lenguaje) · `ingestion/chunker.py`
- [x] Embeddings (Voyage por defecto, OpenAI alternativa) tras interfaz `Embedder` +
  persistencia en ChromaDB tras interfaz `VectorStore`
- [x] Endpoint `POST /ingest` (ruta de carpeta/fichero; multipart → Fase 5) + tests offline
  (28 tests verde, `FakeEmbedder` determinista; ruff + mypy limpios)

## Fase 2 — Retrieval / RAG ✅
- [x] Búsqueda semántica top-k (`rag/retriever.py`) + ensamblado de contexto con
  presupuesto de tokens (`rag/context.py`, cabeceras citables `path:inicio-fin`)
- [x] Interfaz `VectorStore` desacoplada (ChromaDB hoy, pgvector mañana) · ya cumplida en
  Fase 1 (`rag/vector_store.py`)
- [x] Tests de recuperación con repo de ejemplo pequeño (`test_retriever.py`,
  `test_context.py`); 36 tests verde, ruff + mypy limpios

## Fase 3 — Agente con tools ✅
- [x] Grafo LangGraph con las 3 tools (`search_code`, `list_symbols`, `read_file_range`)
  · `agent/tools.py` + `agent/graph.py` con `langchain.agents.create_agent` (API no
  deprecada) y `ChatAnthropic` (`claude-sonnet-4-6`)
- [x] Citas de origen verificables (`path:inicio-fin`) impuestas por el system prompt;
  `read_file_range` lee líneas exactas vía `abs_path` indexado
- [x] Memoria de sesión (`MemorySaver`, clave `thread_id`) + tests del flujo con chat
  model guionizado (`ScriptedChatModel`); 43 tests verde, ruff + mypy limpios

## Fase 4 — API FastAPI ✅
- [x] `POST /chat` con streaming SSE (`api/chat.py`): eventos `token`/`done`/`error`,
  `done` con `session_id` + citas `path:inicio-fin` parseadas
- [x] Manejo de errores (503 claro si falta clave, evento `error` en el stream) y CORS
  (`CORSMiddleware`, orígenes configurables) · dependencias compartidas en `api/deps.py`
- [x] Tests de integración de endpoints (`test_chat_endpoint.py` con agente guionizado);
  47 tests verde, ruff + mypy limpios

## Fase 5 — Frontend React/TS ✅
- [x] Drag & drop de carpetas/ficheros → `POST /ingest/upload` (multipart) ·
  `components/FileDrop.tsx` con recorrido de carpetas y filtro por extensión
- [x] Chat con streaming de tokens (`components/Chat.tsx` + `lib/api.ts` parseando SSE
  sobre fetch); memoria por `session_id`
- [x] Panel de citas (`components/Citations.tsx`): clic en cita → `GET /source` muestra el
  fragmento exacto · backend: `/ingest/upload`, `/source`, `rag/source.py` (DRY con la tool)
- Backend: 49 tests verde, ruff + mypy limpios. Frontend: `npm run build` (tsc) + oxlint OK;
  render verificado con Preview.

## Fase 6 — Polish y entrega
- [ ] `Dockerfile` del backend + instrucciones de arranque
- [ ] README con diagrama de arquitectura y pasos de demo
- [ ] Dogfooding: indexar este repo + 3 preguntas de ejemplo en el README
- [ ] (Opcional) GIF de la demo
