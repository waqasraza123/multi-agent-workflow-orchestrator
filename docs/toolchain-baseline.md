# Toolchain baseline

This repository uses a root Python tooling baseline before higher-level product layers are added.

## Selected tools

- Python 3.12
- uv
- Ruff
- mypy
- pytest
- FastAPI
- Uvicorn

## Local commands

- Bootstrap: `uv sync --group dev`
- Full local check: `make check`
- Run API locally: `make run-api`
- Lint only: `uv run ruff check .`
- Format check only: `uv run ruff format --check .`
- Typecheck current code: `uv run mypy src tests`
- Run tests: `uv run pytest -q`

## Current scope

The repository now contains a root `src/` package with contracts, orchestration state logic, application services, storage abstractionble FastAPI application backed by in-memory persistence.
