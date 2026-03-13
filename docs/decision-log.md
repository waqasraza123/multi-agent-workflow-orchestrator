# Decision log

## Initial assumptions

- Monorepo layout with `apps/`, `services/`, `packages/`, `tests/`, `infra/`, and `docs/`
- One step at a time
- Smallest safe change set
- Human review before commit

## Toolchain baseline

- Python 3.12 only
- uv for environment and dependency management
- Ruff for linting and formatting
- mypy for static type checking
- pytest for test execution
- `uv.lock` is committed

## Working mode decision

- ChatGPT is the primary technical execution partner
- Cursor is used only for repository inspection when current file context is needed

## Implementation structure decision

- Product code starts in `src/multi_agent_platform/`
- Domain boundaries are represented as internal subpackages first
- Top-level `packages/` remains reserved for future extraction if repository growth justifies it

## Core runtime dependencies

- Pydantic for typed contracts and validation
- FastAPI for the initial HTTP application surface
- Uvicorn for local ASGI serving

## Verification decision

- Run verification is modeled as an explicit report
- Verification is deterministic at this stage
- Verification reports are stored behind a dedicated repository abstraction
- Application services own verification generation and persistence
- Verification completion is also recorded in the run event timeline

## Still intentionally undecided

- Database technology
- Queueing and background execution strategy
- Worker implementation details
- Deployment model
- Release workflow design
