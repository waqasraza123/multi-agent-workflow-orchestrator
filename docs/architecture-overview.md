# Architecture overview

This repository is a production-grade multi-agent research and execution platform.

## Current source layout

The implementation starts with a single root source package under `src/multi_form/`.

This is intentional. It keeps the codebase modular without introducing premature multi-package packaging complexity. Domain boundaries still exist as internal subpackages and can be extracted later if the repository outgrows a single root package.

## Domain boundaries

- `multi_agent_platform.contracts` — Typed request, state, and entity models
- `multi_agent_platform.orchestration` — Deterministic workflow state transitions
- `multi_agent_platform.agents` — Agent role logic
- `multi_agent_platform.tools` — Tool interfaces and adapters
- `multi_agent_platform.verification` — Deterministic validation and verifier logic
- `multi_agent_platform.storage` — Persistence and repository abstractions
- `multi_agent_platform.observability` — Logging, tracing, and metrics helpers

## Reserved top-level paths

- `apps/` — External interfaces such as operator or user-facing applications
- `services/` — Long-running backend processes and worker entry points
- `packages/` — Future extraction ntly versioned modules
- `tests/` — Unit, integration, and evaluation coverage
- `infra/` — Environment and deployment assets
- `docs/` — Specifications, decisions, and runbooks

## Current implementation boundary

Only the contracts and orchestration state scaffold are implemented in this step. There is still no API layer, worker process, database integration, queueing layer, or external tool execution.
