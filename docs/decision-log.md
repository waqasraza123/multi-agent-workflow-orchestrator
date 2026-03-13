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

## Approval workflow decision

- Approval requests are modeled as explicit records
- Approval records are stored behind a dedicated repository abstraction
- Application services own approval creation and decision handling
- Approval decisions are immutable after the first non-pending decision
- Approval actions are recorded in the run event timeline

## Still intentionally undecided

- Database technology
- Queueing and background execution strategy
- Worker implementation details
- Deployment model
- Release workflow design
