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
- No runtime dependencies yet
- `uv.lock` is committed

## Working mode decision

- ChatGPT is the primary technical execution partner
- Cursor is used only for repository inspection when current file context is needed

## Foundation normalization

This step restored the missing repository governance files, added `.editorconfig`, aligned documentation with the current workflow, strengthened the smoke test, and updated ignore rules for mypy and Ruff caches.

## CI foundation

- GitHub Actions is the repository CI baseline
- `actions/setup-python@v6` uses `.python-version`
- `astral-sh/setup-uv@v7` installs uv and enables cache support
- CI uses `uv sync --locked --group dev`
- CI runs `make check`
- CI triggers on pushes to `main`, pull requests, and manual dispatch

## Still intentionally undecided

- API framework structure
- Worker implementation details
- Database technology
- Queueing and background execution strategy
- Deployment model
- Release workflow design
