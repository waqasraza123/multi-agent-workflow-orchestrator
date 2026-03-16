# Contributing

## Scope

This repository is a backend first Python platform focused on clean contracts, explicit repository boundaries, deterministic orchestration, and provider backed execution.

## Local setup

Bootstrap the repo:

    uv sync --group dev

Run the main quality gate:

    make check

Run the full local release gate:

    make release-check

Run the API locally:

    uv run uvicorn multi_agent_platform.main:app --reload

## Development rules

- keep changes cohesive and production grade
- follow the existing architecture and naming conventions
- prefer small focused functions and explicit contracts
- keep storage boundaries and service boundaries clear
- avoid hidden coupling and hardcoded behavior
- add or update tests with behavior changes
- keep commit messages short and descriptive

## Pull requests

Before opening a pull request:

1. run `make check`
2. run the relevant smoke flow
3. update docs if behavior or configuration changed
4. keep the pull request scoped to one meaningful change
