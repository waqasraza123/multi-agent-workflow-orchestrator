# Phase status

## Current phase: Toolchain baseline (Step 2) — In progress

Foundation (Step 1) established repo layout, docs, and Cursor rules. Step 2 locks the Python toolchain and local quality gates only; no product code, CI, or Docker.

### Exit criteria for Step 2

- [ ] `pyproject.toml` defines Python 3.12, dev group (ruff, mypy, pytest), and tool config.
- [ ] `.python-version` pins 3.12.
- [ ] `.env.example` exists and is minimal (no product secrets or speculative vars).
- [ ] `docs/toolchain-baseline.md` documents baseline and local commands.
- [ ] `tests/unit/test_repo_foundation.py` passes and asserts repo structure and key files.
- [ ] `.gitignore` ignores `.venv` and common Python caches; does not ignore `uv.lock`.
- [ ] `uv sync --group dev` succeeds; `ruff check`, `ruff format --check`, `mypy`, and `pytest -q` run without errors on the current tree.
- [ ] Human review and approval of Step 2 changes.

### Completed

- Foundation setup (Step 1): README, .gitignore, .editorconfig, execution charter, architecture overview, decision log, phase status, Cursor rules.
