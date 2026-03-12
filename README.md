# Multi-Agent Platform

Production-grade multi-agent research and execution platform. Monorepo; foundation and toolchain only—no product implementation yet.

**Status:** Foundation only. Toolchain baseline in progress.

## Repository structure

- `apps/` — User-facing applications
- `services/` — Backend services
- `packages/` — Shared libraries and utilities
- `tests/` — Unit and integration tests
- `infra/` — Deployment and infrastructure
- `docs/` — Design, decisions, and runbooks

## Working mode

- **ChatGPT** — Spec and design review.
- **Cursor** — Repo changes and implementation.

Runtime and toolchain choices are intentionally deferred until the foundation step is complete.

## Local setup

1. Install [uv](https://docs.astral.sh/uv/).
2. From repo root:

   ```bash
   uv sync --group dev
   ```

3. Run quality gates:

   ```bash
   uv run ruff check .
   uv run ruff format --check .
   uv run mypy apps services packages tests
   uv run pytest -q
   ```

See `docs/toolchain-baseline.md` for the full toolchain baseline.
