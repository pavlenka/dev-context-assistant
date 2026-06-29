"""Tests del recorrido y lectura de ficheros fuente."""

from __future__ import annotations

from pathlib import Path

from app.ingestion.loader import iter_source_files, read_text


def test_iter_source_files_filtra_dirs_y_extensiones(tmp_path: Path) -> None:
    (tmp_path / "a.py").write_text("x = 1\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.js").write_text("const x = 1;\n")
    (tmp_path / "notes.md").write_text("# nope\n")  # extensión no reconocida
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dep.py").write_text("y = 2\n")  # dir ignorado
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "lib.py").write_text("z = 3\n")  # dir ignorado

    found = {p.relative_to(tmp_path).as_posix() for p in iter_source_files(tmp_path)}
    assert found == {"a.py", "sub/b.js"}


def test_iter_source_files_salta_deps_y_worktrees(tmp_path: Path) -> None:
    (tmp_path / "mod.py").write_text("x = 1\n")
    for ignored in ("site-packages", ".tox", "pkg.egg-info", "proj.worktrees"):
        d = tmp_path / ignored
        d.mkdir()
        (d / "dep.py").write_text("y = 2\n")

    found = {p.relative_to(tmp_path).as_posix() for p in iter_source_files(tmp_path)}
    assert found == {"mod.py"}


def test_iter_source_files_fichero_unico(tmp_path: Path) -> None:
    target = tmp_path / "solo.py"
    target.write_text("x = 1\n")
    assert list(iter_source_files(target)) == [target]


def test_read_text_devuelve_none_en_binario(tmp_path: Path) -> None:
    binary = tmp_path / "weird.py"
    binary.write_bytes(b"\xff\xfe\x00\x01")
    assert read_text(binary) is None


def test_read_text_lee_utf8(tmp_path: Path) -> None:
    target = tmp_path / "a.py"
    target.write_text("café = 1\n", encoding="utf-8")
    assert read_text(target) == "café = 1\n"
