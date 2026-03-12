# Multi-Agent Platform

Production-grade multi-agent research and execution platform.

**Status:** Foundation complete. API scaffold, service layer, in-memory repository, and core orchestration state are implemented.

## Repository structure

- `src/multi_agent_platform/` — Application source package
- `apps/` — User-facing applications
- `services/` — Long-running backend services and wo- `packages/` — Reserved for future package extraction if justified
- `tests/` — Unit, integration, and evaluation tests
- `infra/` — Deployment and environment assets
- `docs/` — Specifications, decisions, and runbooks

## Working mode

- **ChatGPT** — Primary execution partner for planning, code, tests, debugging, and review
- **Cursor** — Repo inspection only when current file state or diffs are needed

## Local setup

- Bootstrap: `make bootstrap`
- Quality gate: `make check`
- Run API locally: `make run-api`
- Format with fixes: `make format`

## Current implemented scope

- Repository governance
- Python toolchain baseline
- Local developer command surface
- Core contracts and orchestration state scaffold
- FastAPI application scaffold
- In-memory run repository
- Run service and HTTP endpoints

See `docs/toolchain-baseline.md`, `docs/execution-charter.md`, and `docs/architecture-overview.md` for the current source of truth.
