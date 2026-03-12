# Toolchain baseline

This repository uses a root Python tooling baseline before higher-level product layers are added.

## Selected tools

- Python 3.12
- uv
- Ruff
- mypy
- pytest

## Local commands

- Bootstrap: `uv sync --group dev`
- Full local check: `make check`
- Lint only: `uv run ruff check .`
- Format check only: `uv run ruff format --check .`
- Typecheck current code: `uv run mypy src tests`
 `uv run pytest -q`

## Current scope

The repository now contains a root `src/` package with the first validated contracts and orchestration state logic. Typecheck targets have expanded to `src` and `tests`.
