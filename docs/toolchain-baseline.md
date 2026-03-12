# Toolchain baseline

This document describes the pre-implementation tooling baseline for the repository. No runtime or product code is implied; this is the shared environment for local development and quality gates.

## Selected baseline

- **Python 3.12** — Single supported version; pinned in `.python-version` and `pyproject.toml`.
- **uv** — Package and environment manager. Used to install dev dependencies and run tools.
- **Ruff** — Linter and formatter. Replaces separate lint/format tools.
- **mypy** — Static type checker. Strict mode for apps, services, packages, tests.
- **pytest** — Test runner. Used for unit and integration tests.

## Local commands

Bootstrap and run quality gates locally:

```bash
uv sync --group dev
uv run ruff check .
uv run ruff format --check .
uv run mypy apps services packages tests
uv run pytest -q
```

If `apps`, `services`, or `packages` do not exist yet, run mypy only on existing paths (e.g. `uv run mypy tests`).

Run format with fix:

```bash
uv run ruff format .
```

## Assumptions

- `uv` is installed (e.g. via `curl -LsSf https://astral.sh/uv/install.sh | sh` or package manager).
- No virtualenv is created manually; `uv sync` manages the environment.
- `uv.lock` is committed so all contributors use the same dependency versions.
