"""App FastAPI del Dev Context Assistant.

Expone `/health`, ingesta (`/ingest`) y chat con streaming (`/chat`), con CORS para el
frontend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, ingest
from app.core.logging import configure_logging
from app.core.settings import get_settings

configure_logging()

app = FastAPI(title="Dev Context Assistant", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins_list,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ingest.router)
app.include_router(chat.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Comprobación de salud del servicio."""
    return {"status": "ok"}
