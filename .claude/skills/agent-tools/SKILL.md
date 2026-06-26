---
name: agent-tools
description: Cómo definir, documentar y registrar las herramientas del agente LangGraph. Úsala al implementar o modificar backend/app/agent: firma de tools, descripción para el LLM, manejo de errores, resultado estructurado y el contrato de las 3 tools del proyecto.
---

# Agent Tools (LangGraph)

## Principios
- Cada tool: firma tipada (anotaciones / Pydantic), docstring claro que el LLM usa para
  decidir cuándo llamarla, y **resultado estructurado** (no texto libre).
- Manejo de errores: capturar y devolver un error estructurado (`{"error": "..."}`),
  nunca lanzar una excepción que rompa el grafo.
- Determinismo: misma entrada → misma salida; sin efectos secundarios ocultos.

## Contrato de tools (Sección 5 del brief)

### `search_code(query: str, top_k: int = 8)`
Búsqueda semántica en el índice vectorial.
→ lista de `{path, start_line, end_line, snippet, score}`.

### `list_symbols(path: str)`
Lista funciones/clases/métodos de un fichero indexado.
→ lista de `{symbol_name, kind, start_line, end_line}`.

### `read_file_range(path: str, start: int, end: int)`
Devuelve las líneas exactas para que el agente cite con precisión.
→ `{path, start, end, content}`.

## Registro en LangGraph
- Registrar las tools en el nodo de herramientas del grafo; el LLM (`claude-sonnet-4-6`)
  decide cuándo llamarlas vs. responder desde el contexto.
- La respuesta final debe incluir citas `path:start_line-end_line` para cada afirmación
  basada en código. Si no hay contexto relevante, decirlo explícitamente; no inventar.
