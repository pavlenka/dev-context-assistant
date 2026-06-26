"""Construcción del agente LangGraph: 3 tools, memoria de sesión y system prompt.

El agente decide cuándo usar las tools vs. responder desde contexto. La memoria por
sesión la da el checkpointer (clave `thread_id`). El streaming token a token lo consume
la API en Fase 4 (`stream_mode="messages"`).
"""

from __future__ import annotations

from typing import Any

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import MemorySaver

from app.agent.tools import make_tools
from app.core.settings import Settings, get_settings
from app.rag.retriever import Retriever
from app.rag.vector_store import VectorStore

_MAX_TOKENS = 4096

_SYSTEM_PROMPT = """Eres Dev Context Assistant, un asistente que responde preguntas técnicas \
sobre una base de código ya indexada.

Herramientas:
- search_code: búsqueda semántica para localizar código relevante.
- list_symbols: funciones/clases/métodos indexados de un fichero.
- read_file_range: líneas exactas de un fichero para citar con precisión.

Reglas:
- Fundamenta tus respuestas en el código real usando las tools; no respondas de memoria \
cuando la pregunta sea sobre el código indexado.
- Cita SIEMPRE cada afirmación basada en código con el formato `path:inicio-fin` \
(p. ej. `app/main.py:10-19`), usando las rutas y líneas que devuelven las tools.
- Si no encuentras contexto relevante, dilo explícitamente; NUNCA inventes rutas, líneas \
ni contenido.
- Responde en español, de forma concisa y técnica."""


def build_agent(
    retriever: Retriever,
    store: VectorStore,
    *,
    settings: Settings | None = None,
    model: BaseChatModel | None = None,
    checkpointer: Any | None = None,
) -> Any:
    """Construye el agente compilado. `model` y `checkpointer` se inyectan en los tests.

    En producción crea `ChatAnthropic` con `claude-sonnet-4-6`, validando la clave (error
    claro si falta `ANTHROPIC_API_KEY`).
    """
    settings = settings or get_settings()
    if model is None:
        from langchain_anthropic import ChatAnthropic

        model = ChatAnthropic(
            model_name=settings.anthropic_model,
            api_key=settings.require_anthropic_key(),  # type: ignore[arg-type]
            max_tokens_to_sample=_MAX_TOKENS,
            timeout=None,
            stop=None,
        )
    return create_agent(
        model,
        make_tools(retriever, store),
        system_prompt=_SYSTEM_PROMPT,
        checkpointer=checkpointer or MemorySaver(),
    )


def answer(agent: Any, question: str, *, thread_id: str) -> str:
    """Ejecuta un turno y devuelve el texto de la respuesta final (helper para tests/smoke)."""
    result = agent.invoke(
        {"messages": [("user", question)]},
        {"configurable": {"thread_id": thread_id}},
    )
    return str(result["messages"][-1].content)
