# Release summary

## Version

v0.1.0

## Project overview

Multi-Agent Platform is a backend-first multi-agent research and execution system. It turns a user goal into a persisted run, generates a deterministic plan, advances tasks through deterministic turns, executes deterministic tools, records evidence, supports approval workflows, verifies completion, and produces a final output.

## Implemented scope

- run creation and listing
- deterministic plan generation
- task registration and lifecycle
- deterministic turn advancement
- deterministic tool execution
- evidence capture and persistence
- approval request and decision flow
- verification reports
- final output synthesis
- in-memory storage backend
- SQL-backed durable storage backend
- FastAPI endpoints for the current execution workflow
- unit and integration coverage for the implemented spine

## Storage modes

### Memory mode

Fast local iteration with in-process state.

Environment:
- STORAGE_BACKEND=memory

### SQL mode

Durable local persistence using SQLite through SQLAlchemy with a PostgreSQL-ready repository boundary.

Environment:
- STORAGE_BACKEND=sql
- DATABASE_URL=sqlite:///./.workdir/multi_agent_platform.db

## Main API flow

1. POST /runs
2. POST /runs/{run_id}/plan
3. POST /runs/{run_id}/turns/advance
4. Repeat turn advancement until verifying
5. POST /runs/{run_id}/verify
6. POST /runs/{run_id}/finalize
7. GET /runs/{run_id}/state
8. GET /runs/{run_id}/outputs/latest

## Supporting API areas

- GET /runs
- GET /runs/{run_id}
- GET /runs/{run_id}/events
- GET /runs/{run_id}/turns
- GET /runs/{run_id}/tool-calls
- GET /runs/{run_id}/plans/latest
- GET /runs/{run_id}/verifications/latest
- GET /runs/{run_id}/approvals
- POST /runs/{run_id}/approvals
- POST /runs/{run_id}/approvals/{approval_id}/decide
- POST /runs/{run_id}/tasks
- POST /runs/{run_id}/tasks/{task_id}/start
- POST /runs/{run_id}/tasks/{task_id}/complete
- POST /runs/{run_id}/evidence

## Standard local commands

Bootstrap:
    uv sync --group dev

Quality gate:
    make check

Full release-ready validation:
    make release-check

Run API locally:
    uv run uvicorn multi_agent_platform.main:app --reload

## Smoke commands

Memory mode:
    make smoke-memory

SQL mode:
    make smoke-sql

## Current limitations

- deterministic runtime only
- no external LLM provider execution yet
- no Alembic migrations yet
- no PostgreSQL deployment profile yet
- no auth or RBAC
- no frontend operator console
- no observability stack
- no distributed worker layer

## Recommended next roadmap

- add Alembic migrations
- add PostgreSQL environment profile
- add provider-backed planning and execution
- add richer tool adapters
- add authentication and authorization
- add observability and tracing
- add frontend operator console

## Release note

This version is the first presentable backend MVP. It is suitable for demos, portfolio presentation, client walkthroughs, and the next production-hardening phase.
