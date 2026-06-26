"""App FastAPI del Dev Context Assistant.

Expone `/health` y el router de ingesta (`/ingest`). El chat (`/chat`) se añade en
fases posteriores.
"""

from fastapi import FastAPI

from app.api import ingest
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title="Dev Context Assistant", version="0.1.0")
app.include_router(ingest.router)


@app.get("/health")
def health() -> dict[str, str]:
    """Comprobación de salud del servicio."""
    return {"status": "ok"}
