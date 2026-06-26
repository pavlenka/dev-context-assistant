"""Detección de lenguaje por extensión y registro de lenguajes con parser tree-sitter.

El diseño permite añadir lenguajes sin tocar el resto del pipeline: basta con ampliar
`EXTENSION_LANGUAGE` y, si tiene parser, `_TREE_SITTER_LANGUAGES`.
"""

from __future__ import annotations

from pathlib import Path

# Extensión (en minúsculas, con punto) -> nombre de lenguaje canónico.
EXTENSION_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
}

# Lenguajes con chunking por símbolo (tree-sitter). El resto usa fallback por líneas.
_TREE_SITTER_LANGUAGES: frozenset[str] = frozenset({"python", "javascript", "typescript", "tsx"})


def detect_language(path: str | Path) -> str | None:
    """Devuelve el lenguaje según la extensión, o None si es desconocida."""
    return EXTENSION_LANGUAGE.get(Path(path).suffix.lower())


def has_tree_sitter_parser(language: str | None) -> bool:
    """Indica si el lenguaje tiene parser tree-sitter (chunking por símbolo)."""
    return language in _TREE_SITTER_LANGUAGES
