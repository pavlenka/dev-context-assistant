"""Tests del ensamblado de contexto con presupuesto de tokens."""

from __future__ import annotations

import math

from app.models.chunk import RetrievedChunk
from app.rag.context import assemble_context, estimate_tokens


def _rc(
    path: str, start: int, end: int, snippet: str, score: float, name: str | None = None
) -> RetrievedChunk:
    return RetrievedChunk(
        path=path, start_line=start, end_line=end, snippet=snippet, score=score, symbol_name=name
    )


def test_estimate_tokens() -> None:
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcdefg", chars_per_token=3.5) == math.ceil(7 / 3.5)


def test_ordena_por_score_y_formatea_cabeceras() -> None:
    chunks = [_rc("a.py", 1, 2, "AAA", 0.2, "a"), _rc("b.py", 5, 6, "BBB", 0.9, "b")]
    ctx = assemble_context(chunks, token_budget=1000)

    assert ctx.chunks[0].path == "b.py"  # mayor score primero
    assert ctx.text.startswith("# b.py:5-6  (b)")
    assert "# a.py:1-2  (a)" in ctx.text
    assert "BBB" in ctx.text and "AAA" in ctx.text


def test_presupuesto_corta_por_chunks_completos() -> None:
    big = "x" * 100  # ~111 chars con cabecera → ~32 tokens
    chunks = [_rc("a.py", 1, 1, big, 0.9), _rc("b.py", 2, 2, big, 0.5)]
    ctx = assemble_context(chunks, token_budget=40)
    assert len(ctx.chunks) == 1  # solo cabe el primero
    assert ctx.chunks[0].path == "a.py"


def test_incluye_siempre_el_primero_aunque_exceda() -> None:
    chunks = [_rc("a.py", 1, 50, "y" * 1000, 0.9)]
    ctx = assemble_context(chunks, token_budget=5)
    assert len(ctx.chunks) == 1
    assert ctx.text


def test_sin_chunks_contexto_vacio() -> None:
    ctx = assemble_context([], token_budget=1000)
    assert ctx.text == ""
    assert ctx.chunks == []
