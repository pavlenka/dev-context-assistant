"""Configuración de logging del backend."""

import logging


def configure_logging(level: int = logging.INFO) -> None:
    """Configura el logging raíz con un formato simple (idempotente)."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
