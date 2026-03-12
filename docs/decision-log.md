# Decision log

## Initial assumptions (foundation)

- Monorepo layout: `apps/`, `services/`, `packages/`, `tests/`, `infra/`, `docs/`.
- One step at a time; smallest safe change set; human review before commit.
- Runtime and toolchain deferred until foundation is locked.

## Intentionally undecided (pre–Step 2)

- Python version, package manager, linter, formatter, type checker, test runner.
- CI, Docker, and deployment strategy.
- Product features and APIs.

## Step 2: Toolchain baseline

**Decisions:**

- **Python 3.12** — Single supported version; no 3.11 or 3.13 for now.
- **uv** — Package and environment manager. Fast, PEP-compliant; replaces pip/venv and optional pip-tools for dev.
- **Ruff** — Linter and formatter. One tool for lint + format; replaces flake8/black/isort.
- **mypy** — Static typing in strict mode for `apps`, `services`, `packages`, `tests`.
- **pytest** — Test runner; default for Python ecosystem.
- **No runtime deps** — `pyproject.toml` has only dev dependency group; no build backend or publish config.
- **uv.lock committed** — Reproducible installs; all contributors use same versions.

**Assumptions:**

- Contributors install `uv` themselves.
- Quality gates run locally; CI to be added in a later step.
- `apps/`, `services/`, `packages/` may be empty; mypy/pytest config still targets them so future code is covered.

**Why runtime/toolchain was deferred:** Foundation (docs, rules, repo shape) was defined first; toolchain is the next discrete step so the baseline is explicit and reviewable before any product code.
