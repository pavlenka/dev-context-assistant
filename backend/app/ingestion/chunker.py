"""Troceado de código en chunks indexables.

Estrategia (ver skill `code-ingestion`):
1. Por símbolo (preferido) con tree-sitter: funciones/clases top-level y métodos = 1 chunk.
   Clases grandes se parten en cabecera + un chunk por método. Símbolos enormes se
   subdividen por ventana de líneas conservando sus metadatos.
2. Fallback por líneas (ventana 60 / solape 10) cuando no hay parser para el lenguaje.
"""

from __future__ import annotations

from dataclasses import dataclass

from tree_sitter import Node, Parser
from tree_sitter_language_pack import get_language

from app.ingestion.languages import has_tree_sitter_parser
from app.models.chunk import CodeChunk

# Presupuesto de líneas por chunk. Por encima de esto, se subdivide por ventana.
MAX_CHUNK_LINES = 120
WINDOW_LINES = 60
OVERLAP_LINES = 10


@dataclass(frozen=True)
class _Grammar:
    """Tipos de nodo tree-sitter relevantes para un lenguaje."""

    function_types: frozenset[str]
    class_types: frozenset[str]
    method_types: frozenset[str]
    wrapper_types: frozenset[str]  # nodos a desenvolver (decoradores, export)


_PY = _Grammar(
    function_types=frozenset({"function_definition"}),
    class_types=frozenset({"class_definition"}),
    method_types=frozenset({"function_definition"}),
    wrapper_types=frozenset({"decorated_definition"}),
)
_JS = _Grammar(
    function_types=frozenset({"function_declaration", "generator_function_declaration"}),
    class_types=frozenset({"class_declaration"}),
    method_types=frozenset({"method_definition"}),
    wrapper_types=frozenset({"export_statement"}),
)
_TS = _Grammar(
    function_types=_JS.function_types
    | frozenset({"interface_declaration", "enum_declaration", "type_alias_declaration"}),
    class_types=frozenset({"class_declaration", "abstract_class_declaration"}),
    method_types=frozenset({"method_definition"}),
    wrapper_types=frozenset({"export_statement"}),
)

_GRAMMARS: dict[str, _Grammar] = {
    "python": _PY,
    "javascript": _JS,
    "typescript": _TS,
    "tsx": _TS,
}


def chunk_file(path: str, source: str, language: str) -> list[CodeChunk]:
    """Trocea el contenido de un fichero en chunks con metadatos para citar."""
    if not source.strip():
        return []
    if not has_tree_sitter_parser(language):
        return _chunk_by_lines(path, source, language, symbol_name=None, kind=None)
    return _chunk_with_tree_sitter(path, source, language)


def _chunk_with_tree_sitter(path: str, source: str, language: str) -> list[CodeChunk]:
    grammar = _GRAMMARS[language]
    parser = Parser(get_language(language))  # type: ignore[arg-type]
    root = parser.parse(source.encode("utf-8")).root_node
    lines = source.split("\n")

    chunks: list[CodeChunk] = []
    buffer: tuple[int, int] | None = None  # rango (start, end) de código module-level

    def flush_buffer() -> None:
        nonlocal buffer
        if buffer is not None:
            chunks.extend(_window_chunks(path, language, buffer[0], buffer[1], lines, None, None))
            buffer = None

    for node in root.named_children:
        symbol = _classify(node, grammar)
        if symbol.type in grammar.class_types:
            flush_buffer()
            chunks.extend(_chunk_class(path, language, node, symbol, grammar, lines))
        elif symbol.type in grammar.function_types:
            flush_buffer()
            chunks.extend(_emit_symbol(path, language, node, _name_of(symbol), "function", lines))
        else:
            start, end = _span(node)
            buffer = (buffer[0], end) if buffer else (start, end)
    flush_buffer()
    return chunks


def _chunk_class(
    path: str,
    language: str,
    span_node: Node,
    class_node: Node,
    grammar: _Grammar,
    lines: list[str],
) -> list[CodeChunk]:
    """Clase pequeña = 1 chunk; clase grande = cabecera + un chunk por método."""
    name = _name_of(class_node)
    start, end = _span(span_node)
    if end - start + 1 <= MAX_CHUNK_LINES:
        return [_make_chunk(path, language, start, end, name, "class", lines)]

    methods = _find_methods(class_node, grammar)
    if not methods:
        return _window_chunks(path, language, start, end, lines, name, "class")

    chunks: list[CodeChunk] = []
    first_method_start = _span(methods[0])[0]
    if first_method_start > start:  # cabecera: firma, docstring, atributos de clase
        chunks.append(
            _make_chunk(path, language, start, first_method_start - 1, name, "class", lines)
        )
    for method in methods:
        method_name = f"{name}.{_name_of(method)}" if name else _name_of(method)
        chunks.extend(_emit_symbol(path, language, method, method_name, "method", lines))
    return chunks


def _find_methods(class_node: Node, grammar: _Grammar) -> list[Node]:
    """Métodos directos del cuerpo de la clase (desenvolviendo decoradores)."""
    body = class_node.child_by_field_name("body")
    if body is None:
        return []
    methods: list[Node] = []
    for child in body.named_children:
        symbol = _classify(child, grammar)
        if symbol.type in grammar.method_types:
            methods.append(child)
    return methods


def _emit_symbol(
    path: str,
    language: str,
    node: Node,
    name: str | None,
    kind: str,
    lines: list[str],
) -> list[CodeChunk]:
    """Un símbolo = 1 chunk, o varios por ventana si excede el presupuesto."""
    start, end = _span(node)
    if end - start + 1 <= MAX_CHUNK_LINES:
        return [_make_chunk(path, language, start, end, name, kind, lines)]
    return _window_chunks(path, language, start, end, lines, name, kind)


def _classify(node: Node, grammar: _Grammar) -> Node:
    """Desenvuelve wrappers (export/decorated) para clasificar y nombrar el símbolo."""
    if node.type in grammar.wrapper_types:
        symbol_types = grammar.function_types | grammar.class_types | grammar.method_types
        for child in node.named_children:
            if child.type in symbol_types:
                return child
    return node


def _name_of(node: Node) -> str | None:
    name = node.child_by_field_name("name")
    return name.text.decode("utf-8") if name is not None and name.text else None


def _span(node: Node) -> tuple[int, int]:
    """Rango de líneas 1-indexed (inclusive) del nodo."""
    return node.start_point[0] + 1, node.end_point[0] + 1


def _chunk_by_lines(
    path: str, source: str, language: str, symbol_name: str | None, kind: str | None
) -> list[CodeChunk]:
    lines = source.split("\n")
    return _window_chunks(path, language, 1, len(lines), lines, symbol_name, kind)


def _window_chunks(
    path: str,
    language: str,
    start_line: int,
    end_line: int,
    lines: list[str],
    symbol_name: str | None,
    kind: str | None,
) -> list[CodeChunk]:
    """Trocea un rango por ventanas de WINDOW_LINES con OVERLAP_LINES de solape.

    Salta las ventanas que solo contienen espacios en blanco.
    """
    chunks: list[CodeChunk] = []
    current = start_line
    while current <= end_line:
        window_end = min(current + WINDOW_LINES - 1, end_line)
        if "\n".join(lines[current - 1 : window_end]).strip():
            chunks.append(
                _make_chunk(path, language, current, window_end, symbol_name, kind, lines)
            )
        if window_end == end_line:
            break
        current = window_end - OVERLAP_LINES + 1
    return chunks


def _make_chunk(
    path: str,
    language: str,
    start_line: int,
    end_line: int,
    symbol_name: str | None,
    kind: str | None,
    lines: list[str],
) -> CodeChunk:
    """Construye un chunk a partir del rango de líneas (1-indexed, inclusive)."""
    return CodeChunk(
        path=path,
        start_line=start_line,
        end_line=end_line,
        symbol_name=symbol_name,
        kind=kind,
        language=language,
        content="\n".join(lines[start_line - 1 : end_line]),
    )
