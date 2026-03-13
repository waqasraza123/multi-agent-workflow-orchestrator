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

## Turn execution decision

- Turn execution is modeled as explicit turn records
- Turn advancement is deterministic at this stage
- The next ready task is automatically started when no task is active
- A deterministic agent runtime executes one task per turn
- Each turn can record evidence and complete the active task
- Turn execution is recorded in both turn storage and the run event timeline

## Still intentionally undecided

- Database technology
- Queueing and background execution strategy
- Worker implementation details
- Deployment model
- Release workflow design
