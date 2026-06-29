"""Recorrido de ficheros fuente: filtra directorios ruidosos y ficheros no-texto."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from app.ingestion.languages import detect_language

# Directorios que nunca se indexan (dependencias, artefactos, entornos, control de versiones).
IGNORED_DIRS: frozenset[str] = frozenset(
    {
        "node_modules",
        ".venv",
        "venv",
        "env",
        ".git",
        "dist",
        "build",
        "__pycache__",
        ".chroma",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        # Dependencias / entornos vendizados (no es código del usuario).
        "site-packages",
        ".tox",
        ".nox",
        ".eggs",
        "vendor",
        "target",
        ".next",
        ".gradle",
        ".terraform",
    }
)

# Sufijos de directorio a saltar (nombres variables: paquetes, worktrees de git).
IGNORED_DIR_SUFFIXES: tuple[str, ...] = (".egg-info", ".dist-info", ".worktrees")


def _is_ignored_dir(name: str) -> bool:
    return name in IGNORED_DIRS or name.endswith(IGNORED_DIR_SUFFIXES)


def iter_source_files(root: str | Path) -> Iterator[Path]:
    """Itera ficheros con extensión reconocida bajo `root` (carpeta o fichero único).

    Salta directorios de dependencias/entornos/artefactos y extensiones desconocidas.
    """
    root_path = Path(root)
    if root_path.is_file():
        if detect_language(root_path) is not None:
            yield root_path
        return

    for path in sorted(root_path.rglob("*")):
        if not path.is_file():
            continue
        if any(_is_ignored_dir(part) for part in path.parts):
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
