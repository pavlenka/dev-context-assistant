---
name: code-ingestion
description: Convenciones para parsear y trocear código fuente en chunks indexables. Úsala al implementar o modificar la ingestión (backend/app/ingestion): chunking con tree-sitter por símbolo, metadatos por chunk y fallback por ventana de líneas.
---

# Code Ingestion

Cómo convertir ficheros de código en chunks listos para embeddings.

## Estrategia de chunking
1. **Por símbolo (preferido):** usar tree-sitter para extraer funciones, clases y
   métodos como unidades. Cada símbolo de nivel superior (y los métodos de una clase) = 1 chunk.
2. **Fallback por líneas:** si no hay parser tree-sitter para el lenguaje, trocear por
   ventana de líneas (p. ej. 60 líneas con 10 de solape).

## Metadatos obligatorios por chunk
- `path` — ruta relativa a la raíz indexada.
- `start_line`, `end_line` — 1-indexed, inclusivas.
- `symbol_name` — nombre de la función/clase/método (`null` en fallback por líneas).
- `language` — lenguaje detectado (por extensión).

## Lenguajes objetivo (MVP)
Python, JavaScript, TypeScript. Diseñar el detector de lenguaje y el registro de parsers
para poder añadir más sin tocar el resto del pipeline.

## Reglas
- No trocear a mitad de un símbolo cuando hay parser disponible.
- Símbolos enormes (mayores que el presupuesto): subdividir por líneas conservando metadatos.
- Ignorar binarios y ficheros no-texto; saltar `node_modules/`, `.venv/`, `.git/`, `dist/`.
- Los metadatos deben permitir reconstruir la cita exacta `path:start_line-end_line`.
