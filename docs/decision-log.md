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
- No runtime dependencies in the earliest foundation state
- `uv.lock` is committed

## Working mode decision

- ChatGPT is the primary technical execution partner
- Cursor is used onlrepository inspection when current file context is needed

## Implementation structure decision

- Product code starts in `src/multi_agent_platform/`
- Domain boundaries are represented as internal subpackages first
- Top-level `packages/` remains reserved for future extraction if repository growth justifies it
- This avoids premature packaging complexity while preserving clean boundaries

## Core runtime dependency

- Pydantic is the first runtime dependency
- It is used for typed contracts and validation at the system boundary

## Still intentionally undecided

- API framework structure
- Worker implementation details
- Database technology
- Queueing and background execution strategy
- Deployment model
- Release workflow design
