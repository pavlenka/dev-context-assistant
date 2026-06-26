"""Tests del troceado por símbolo y del fallback por líneas."""

from __future__ import annotations

import pytest

from app.ingestion import chunker
from app.ingestion.chunker import chunk_file

PY_SAMPLE = '''import os

CONST = 1


def top_level(x):
    return x + 1


class Foo:
    """Doc."""

    def method_a(self, b):
        return b

    def method_b(self):
        return 2
'''


def test_python_symbols_y_metadatos() -> None:
    chunks = chunk_file("sample.py", PY_SAMPLE, "python")
    by_name = {(c.symbol_name, c.kind) for c in chunks}

    # Función y clase top-level capturadas como símbolos.
    assert ("top_level", "function") in by_name
    assert ("Foo", "class") in by_name
    # Código module-level (imports/constantes) no se pierde: chunk sin símbolo.
    assert any(c.symbol_name is None and c.kind is None for c in chunks)
    # Todos los chunks tienen líneas 1-indexed coherentes y lenguaje correcto.
    for c in chunks:
        assert 1 <= c.start_line <= c.end_line
        assert c.language == "python"
        assert c.content.strip()


def test_clase_grande_se_parte_en_cabecera_y_metodos(monkeypatch: pytest.MonkeyPatch) -> None:
    # Forzamos el presupuesto bajo para que la clase de PY_SAMPLE exceda el umbral.
    monkeypatch.setattr(chunker, "MAX_CHUNK_LINES", 4)
    chunks = chunk_file("sample.py", PY_SAMPLE, "python")
    kinds = {c.kind for c in chunks}
    names = {c.symbol_name for c in chunks}

    assert "method" in kinds  # métodos extraídos como chunks propios
    assert "Foo.method_a" in names
    assert "Foo.method_b" in names
    # La cabecera de la clase se conserva como chunk de tipo 'class'.
    assert any(c.kind == "class" and c.symbol_name == "Foo" for c in chunks)


def test_simbolo_enorme_se_subdivide_por_ventana(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chunker, "MAX_CHUNK_LINES", 3)
    monkeypatch.setattr(chunker, "WINDOW_LINES", 3)
    monkeypatch.setattr(chunker, "OVERLAP_LINES", 1)
    body = "\n".join(f"    x{i} = {i}" for i in range(20))
    source = f"def big():\n{body}\n    return 0\n"

    chunks = chunk_file("big.py", source, "python")
    big_chunks = [c for c in chunks if c.symbol_name == "big"]
    assert len(big_chunks) > 1  # subdividido en varias ventanas
    assert all(c.kind == "function" for c in big_chunks)


def test_fallback_por_lineas_lenguaje_desconocido() -> None:
    source = "\n".join(f"line {i}" for i in range(5))
    chunks = chunk_file("notes.txt", source, "text")
    assert len(chunks) == 1
    assert chunks[0].symbol_name is None
    assert chunks[0].kind is None
    assert chunks[0].start_line == 1


def test_javascript_export_function_y_class() -> None:
    js = "export function f(a) { return a; }\nexport class C { m() { return 1; } }\n"
    chunks = chunk_file("x.js", js, "javascript")
    pairs = {(c.symbol_name, c.kind) for c in chunks}
    assert ("f", "function") in pairs
    assert ("C", "class") in pairs


def test_fichero_vacio_no_genera_chunks() -> None:
    assert chunk_file("empty.py", "   \n\n", "python") == []
