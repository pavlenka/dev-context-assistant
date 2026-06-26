"""Tests de detección de lenguaje y registro de parsers."""

from __future__ import annotations

import pytest

from app.ingestion.languages import detect_language, has_tree_sitter_parser


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("foo.py", "python"),
        ("foo.pyi", "python"),
        ("foo.js", "javascript"),
        ("foo.jsx", "javascript"),
        ("foo.mjs", "javascript"),
        ("foo.ts", "typescript"),
        ("foo.tsx", "tsx"),
        ("foo.txt", None),
        ("Makefile", None),
    ],
)
def test_detect_language(filename: str, expected: str | None) -> None:
    assert detect_language(filename) == expected


def test_has_tree_sitter_parser() -> None:
    assert has_tree_sitter_parser("python") is True
    assert has_tree_sitter_parser("tsx") is True
    assert has_tree_sitter_parser("text") is False
    assert has_tree_sitter_parser(None) is False
