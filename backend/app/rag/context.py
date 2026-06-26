"""Ensamblado del contexto recuperado dentro de un presupuesto de tokens.

Concatena los chunks más relevantes (cada uno con su cabecera `path:inicio-fin` para que
el agente pueda citar) cortando siempre por chunks completos, nunca a media línea.
"""

from __future__ import annotations

import math

from app.models.chunk import RetrievedChunk
from app.models.context import AssembledContext

_DEFAULT_CHARS_PER_TOKEN = 3.5
_DEFAULT_TOKEN_BUDGET = 4000


def estimate_tokens(text: str, chars_per_token: float = _DEFAULT_CHARS_PER_TOKEN) -> int:
    """Estima los tokens de un texto con una heurística offline (caracteres / ratio).

    Sustituible por un conteo exacto del tokenizador del modelo si se requiere precisión.
    """
    if not text:
        return 0
    return math.ceil(len(text) / chars_per_token)


def _format_block(chunk: RetrievedChunk) -> str:
    """Formatea un chunk con cabecera citable `# path:inicio-fin (símbolo)`."""
    header = f"# {chunk.path}:{chunk.start_line}-{chunk.end_line}"
    if chunk.symbol_name:
        header += f"  ({chunk.symbol_name})"
    return f"{header}\n{chunk.snippet}"


def assemble_context(
    chunks: list[RetrievedChunk],
    token_budget: int = _DEFAULT_TOKEN_BUDGET,
    chars_per_token: float = _DEFAULT_CHARS_PER_TOKEN,
) -> AssembledContext:
    """Ensambla los chunks más relevantes en un bloque acotado por presupuesto de tokens.

    Ordena por score descendente y añade chunks completos mientras quepan; siempre incluye
    al menos el primero (aunque exceda el presupuesto). Sin chunks → contexto vacío.
    """
    ordered = sorted(chunks, key=lambda c: c.score, reverse=True)
    included: list[RetrievedChunk] = []
    blocks: list[str] = []
    total = 0
    for chunk in ordered:
        block = _format_block(chunk)
        cost = estimate_tokens(block, chars_per_token)
        if included and total + cost > token_budget:
            break
        included.append(chunk)
        blocks.append(block)
        total += cost
    return AssembledContext(text="\n\n".join(blocks), chunks=included)
