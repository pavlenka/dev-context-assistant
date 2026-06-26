"""App FastAPI del Dev Context Assistant.

En la Fase 0 solo expone `/health`. Los routers de ingesta (`/ingest`) y chat (`/chat`)
se añaden en fases posteriores.
"""

from fastapi import FastAPI

from app.core.logging import configure_logging

configure_logging()

app = FastAPI(title="Dev Context Assistant", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Comprobación de salud del servicio."""
    return {"status": "ok"}
