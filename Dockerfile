# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:0.11.17 AS uv

FROM python:3.14-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/src"

WORKDIR /app

COPY --from=uv /uv /uvx /bin/

RUN useradd --create-home --uid 10001 appuser

FROM base AS builder

RUN apt-get update \
    && apt-get install --no-install-recommends -y build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock README.md ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY src ./src
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

FROM base AS runtime

COPY --from=builder /app/.venv /app/.venv
COPY src ./src
COPY alembic.ini ./alembic.ini
COPY migrations ./migrations

USER appuser

EXPOSE 8000

CMD ["fastapi", "run", "src/app/main.py", "--port", "8000"]
