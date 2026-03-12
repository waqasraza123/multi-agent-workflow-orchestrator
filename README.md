# Multi-Agent Platform

Production-grade multi-agent research and execution platform.

**Status:** Foundation only. Repository governance and Python toolchain baseline are in place. No product implementation has started yet.

## Repository structure

- `apps/` — User-facing applications
- `services/` — Long-running backendvices and workers
- `packages/` — Shared libraries and domain modules
- `tests/` — Unit, integration, and evaluation tests
- `infra/` — Deployment and environment assets
- `docs/` — Specifications, decisions, and runbooks

## Working mode

- **ChatGPT** — Primary execution partner for planning, code, tests, debugging, and review
- **Cursor** — Repo inspection only when current file state or diffs are needed

## Local setup

- Bootstrap: `uv sync --group dev`
- Quality gate: `make check`
- Format with fixes: `make format`

## Current foundation scope

- Root Python toolchain baseline
- Repository governance documents
- Local developer command surface
- Repository smoke tests

See `docs/toolchain-baseline.md`, `docs/execution-charter.md`, and `docs/architecture-overview.md` for the current foundation source of truth.
