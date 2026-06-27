# Backend del Dev Context Assistant. Contexto de build: backend/
# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# 1) Dependencias (capa cacheable: solo se reinstala si cambian pyproject/uv.lock).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 2) Código de la app + instalación del proyecto.
COPY README.md ./
COPY app ./app
RUN uv sync --frozen --no-dev

EXPOSE 8000
CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
