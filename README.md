# Multi-Agent Platform

Production-grade multi-agent research and execution platform with deterministic planning, provider-backed turn execution, tool calls, approvals, verification, final outputs, and switchable storage backends.

## Current status

Implemented and working:

- run creation and listing
- deterministic plan generation
- task registration and lifecycle
- deterministic turn advancement
- provider-backed LLM turn execution
- deterministic fallback when LLM execution fails
- deterministic tool call execution and storage
- evidence recording
- approval request and decision flow
- verification reports
- final output synthesis
- persisted LLM call artifacts and usage records
- in-memory storage backend
- SQL-backed durable storage backend
- FastAPI surface for the execution workflow
- unit and integration test coverage for the current platform spine

## Repository structure

- `src/multi_agent_platform/api` — API app, routes, dependency wiring
- `src/multi_agent_platform/application` — service layer and response builders
- `src/multi_agent_platform/contracts` — request, response, and domain contracts
- `src/multi_agent_platform/orchestration` — run state transitions
- `src/multi_agent_platform/planning` — deterministic plan generation
- `src/multi_agent_platform/agents` — deterministic and provider-backed turn execution
- `src/multi_agent_platform/tools` — deterministic tool registry
- `src/multi_agent_platform/storage` — in-memory and SQL persistence layers
- `src/multi_agent_platform/config` — runtime settings
- `tests/unit` — unit coverage for contracts, repositories, application, and API
- `tests/integration` — integration coverage for SQL persistence and LLM execution API flows

## Storage backends

The platform supports two backends:

- `memory` for fast local iteration
- `sql` for durable local persistence and production-ready repository boundaries

Environment variables:

- `STORAGE_BACKEND=memory|sql`
- `DATABASE_URL=sqlite:///./.workdir/multi_agent_platform.db`

## Execution backends

The platform supports two execution backends:

- `EXECUTION_BACKEND=deterministic`
- `EXECUTION_BACKEND=llm`

When `EXECUTION_BACKEND=llm`, the platform supports these providers:

- `LLM_PROVIDER_NAME=fake`
- `LLM_PROVIDER_NAME=openai`

Additional LLM settings:

- `LLM_MODEL_NAME=fake-model` for fake mode or an OpenAI-compatible model name for real provider mode
- `LLM_API_BASE_URL=https://api.openai.com/v1`
- `LLM_API_KEY=...` required when `LLM_PROVIDER_NAME=openai`

## API highlights

Key run workflow endpoints:

- `POST /runs`
- `POST /runs/{run_id}/plan`
- `POST /runs/{run_id}/turns/advance`
- `GET /runs/{run_id}/tool-calls`
- `GET /runs/{run_id}/llm-calls`
- `POST /runs/{run_id}/verify`
- `POST /runs/{run_id}/finalize`
- `GET /runs/{run_id}/outputs/latest`

## Local setup

Bootstrap:

    uv sync --group dev

Run checks:

    make check

Run API locally:

    uv run uvicorn multi_agent_platform.main:app --reload

## Smoke flows

Deterministic memory mode:

    make smoke-memory

Durable SQL mode:

    make smoke-sql

LLM fake-provider mode:

    make smoke-llm-fake

Full local release gate:

    make release-check

## Known limitations

Current implementation remains backend-first and intentionally lightweight.

Not included yet:

- Alembic migrations
- PostgreSQL deployment setup
- authentication and authorization
- async job processing
- streaming provider responses
- richer provider auth and rate-limit policies
- UI frontend
- observability stack
- distributed workers

## Next practical upgrades

- Alembic migrations and schema versioning
- PostgreSQL deployment profile
- richer agent execution policies
- more provider adapters
- LLM-backed planning
- authentication and RBAC
- structured logging and tracing
- frontend operator console
