# Phase status

## Current step

Step 6 — CI foundation

## Goal

Add a repository CI workflow that runs the existing local quality gate automatically on GitHub Actions.

## Exit criteria

- [ ] `.github/workflows/ci.yml` exists
- [ ] CI installs Python from `.python-version`
- [ ] CI installs uv with the official setup action
- [ ] CI runs `uv sync --locked --group dev`
- [ ] CI runs `make check`
- [ ] Repository smoke test enforces workflow presence
- [ ] `make check` passes locally
- [ ] Human review is complete
- [ ] Commit is created

## Completed

- Step 1 — Repository shell
- Step 2 — Python toolchain baselinep 3 — Local developer command surface
- Step 4 — Repository state capture
- Step 5 — Foundation normalization
