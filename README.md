# Dev Context Assistant

Agente que indexa una codebase y responde preguntas técnicas sobre ella (qué hace un
método, dependencias, dónde puede fallar, cómo migrar algo) **con citas al fichero y
línea de origen**. RAG real + agente con herramientas + full stack.

> 🚧 En construcción. Este README se completa en la Fase 6 (arquitectura + demo).

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12 (uv), FastAPI, Uvicorn |
| Agente | LangGraph + `claude-sonnet-4-6` |
| Embeddings | Voyage `voyage-3` (por defecto) · OpenAI `text-embedding-3-small` (alt.) |
| Vector store | ChromaDB local (interfaz desacoplada → pgvector futuro) |
| Parsing | tree-sitter (chunking por símbolo) + fallback por líneas |
| Frontend | React + TypeScript + Vite (chat con streaming) |
| Calidad | ruff, pytest, mypy (opcional) |

## Estructura

```
dev-context-assistant/
├── PLAN.md              # plan vivo por fases
├── .env.example         # variables de entorno documentadas
├── .claude/skills/      # skills del proyecto (code-ingestion, rag-retrieval, agent-tools)
├── backend/             # FastAPI + uv
│   ├── app/{api,ingestion,rag,agent,core,models}/
│   └── tests/
└── frontend/            # Vite + React + TS
```

## Arranque (desarrollo)

### Backend
```bash
cd backend
cp ../.env.example ../.env   # y rellena las claves
uv run uvicorn app.main:app --reload
# Salud: http://127.0.0.1:8000/health
uv run pytest      # tests
uv run ruff check  # lint
```

### Frontend

Requiere Node ≥ 22.12 (Vite 8). El repo fija la versión en [`frontend/.nvmrc`](frontend/.nvmrc):
```bash
cd frontend
nvm use          # activa la versión de .nvmrc (22.23.1)
npm install
npm run dev
```

## Configuración (`.env`)

Ver [`.env.example`](.env.example). Las claves no se piden en código: si falta una
variable requerida por una funcionalidad, el backend falla con un mensaje claro
indicando cuál.
