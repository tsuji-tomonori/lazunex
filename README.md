# Lazunex

Lazunex is an internal API Hub and API access control service built with FastAPI.

## Local Setup

```bash
uv sync
uv run fastapi dev src/app/main.py
```

## Checks

```bash
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked pyright
uv run --locked mypy src tests
uv run --locked pytest
```

## Docker

```bash
docker compose up --build
```
