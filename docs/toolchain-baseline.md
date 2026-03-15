# Toolchain baseline

## Runtime and tooling

- Python 3.12
- uv
- Ruff
- mypy
- pytest
- FastAPI
- SQLAlchemy

## Standard commands

Bootstrap:

    uv sync --group dev

Quality gates:

    uv run ruff check .
    uv run ruff format --check .
    uv run mypy src tests
    uv run pytest -q
    make check

## Storage modes

Memory mode is the default local developer path.

SQL mode is enabled with:

    STORAGE_BACKEND=sql
    DATABASE_URL=sqlite:///./.workdir/multi_agent_platform.db

## Notes

The platform is backend-first and API-driven.
The current repo is suitable for continued backend expansion and later production hardening.
