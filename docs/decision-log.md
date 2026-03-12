# Decision log

## Initial assumptions

- Monorepo layout with `apps/`, `services/`, `packages/`, `tests/`, `infra/`, and `docs/`
- One step at a time
- Smallest safe change set
- Human review before commit

## Toolchain baseline

- Pyly
- uv for environment and dependency management
- Ruff for linting and formatting
- mypy for static type checking
- pytest for test execution
- No runtime dependencies yet
- `uv.lock` is committed

## Working mode decision

- ChatGPT is the primary technical execution partner
- Cursor is used only for repository inspection when current file context is needed

## Foundation normalization

This step restores the missing repository governance files, adds `.editorconfig`, aligns documentation with the current workflow, strengthens the smoke test, and updates ignore rules for mypy and Ruff caches.

## Still intentionally undecided

- API framework structure
- Worker implementation details
- Database technology
- Queueing and background execution strategy
- Deployment model
- CI provider and workflow design
