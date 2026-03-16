# Multi-Agent Platform

Production-grade multi-agent research and execution platform with deterministic planning, provider-backed turn execution, tool calls, approvals, verification, final outputs, and switchable storage backends.

## Current status

Implemented and working:

- run creation and listing
- deterministic plan generation
- task registration and lifecycle
- deterministic and provider-backed turn advancement
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

- `src/multi_agent_platform/api` for API app, routes, and dependency wiring
- `src/multi_agent_platform/application` for service orchestration and response builders
- `src/multi_agent_platform/contracts` for request, response, and domain contracts
- `src/multi_agent_platform/orchestration` for run state transitions
- `src/multi_agent_platform/planning` for deterministic plan generation
- `src/multi_agent_platform/agents` for deterministic and provider-backed execution
- `src/multi_agent_platform/tools` for deterministic tool execution
- `src/multi_agent_platform/storage` for in-memory and SQL persistence
- `src/multi_agent_platform/config` for runtime settings
- `tests/unit` for unit coverage
- `tests/integration` for integration coverage

## Storage backends

Supported storage modes:

- `STORAGE_BACKEND=memory`
- `STORAGE_BACKEND=sql`

Main SQL setting:

- `DATABASE_URL=sqlite:///./.workdir/multi_agent_platform.db`

## Execution backends

Supported execution modes:

- `EXECUTION_BACKEND=deterministic`
- `EXECUTION_BACKEND=llm`

When `EXECUTION_BACKEND=llm`, supported providers are:

- `LLM_PROVIDER_NAME=fake`
- `LLM_PROVIDER_NAME=openai`

Additional LLM settings:

- `LLM_MODEL_NAME=fake-model`
- `LLM_API_BASE_URL=https://api.openai.com/v1`
- `LLM_API_KEY=...` required for the OpenAI compatible provider

## API highlights

Key workflow endpoints:

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

Run the main quality gate:

    make check

Run the full local release gate:

    make release-check

Run the API locally:

    uv run uvicorn multi_agent_platform.main:app --reload

## Smoke flows

Deterministic memory mode:

    make smoke-memory

Durable SQL mode:

    make smoke-sql

LLM fake-provider mode:

    make smoke-llm-fake

## Production-readiness notes

This repository now has:

- strict lint, typecheck, and test gates
- durable SQL storage support
- release-check smoke validation
- provider-backed LLM execution with persisted call records
- repository metadata and community health files

Still intentionally out of scope:

- Alembic migrations
- PostgreSQL deployment profile
- authentication and authorization
- async job processing
- streaming provider responses
- advanced provider auth and rate-limit policy
- observability stack
- distributed workers
- frontend operator console

## Community files

- `LICENSE`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- `SECURITY.md`

## Next practical upgrades

- Alembic migrations and schema versioning
- PostgreSQL deployment profile
- richer agent execution policies
- more provider adapters
- LLM-backed planning
- authentication and RBAC
- structured logging and tracing
- frontend operator console
