"""Recorrido de ficheros fuente: filtra directorios ruidosos y ficheros no-texto."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from app.ingestion.languages import detect_language

# Directorios que nunca se indexan (dependencias, artefactos, control de versiones).
IGNORED_DIRS: frozenset[str] = frozenset(
    {
        "node_modules",
        ".venv",
        "venv",
        ".git",
        "dist",
        "build",
        "__pycache__",
        ".chroma",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
    }
)


def iter_source_files(root: str | Path) -> Iterator[Path]:
    """Itera ficheros con extensión reconocida bajo `root` (carpeta o fichero único).

    Salta los directorios de `IGNORED_DIRS` y cualquier ruta con extensión desconocida.
    """
    root_path = Path(root)
    if root_path.is_file():
        if detect_language(root_path) is not None:
            yield root_path
        return

    for path in sorted(root_path.rglob("*")):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if detect_language(path) is None:
            continue
        yield path


def read_text(path: str | Path) -> str | None:
    """Lee el fichero como UTF-8. Devuelve None si no es texto decodificable."""
    try:
        return Path(path).read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None
