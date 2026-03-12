# Toolchain baseline

This repository uses a root Python tooling baseline before any product code is added.

## Selected tools

- Python 3.12
- uv
- Ruff
- mypy
- pytest

## Local commands

- Bootstrap: `uv sync --group dev`
- Full local check: `make check`
- Lint only: `uv  check .`
- Format check only: `uv run ruff format --check .`
- Typecheck current code: `uv run mypy tests`
- Run tests: `uv run pytest -q`

## Current scope

The repository currently typechecks only `tests` because product code has not been created yet. Typecheck targets will expand once real modules exist under `apps`, `services`, and `packages`.
