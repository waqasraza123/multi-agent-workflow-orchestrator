# Architecture overviewitory is a production-grade multi-agent research and execution platform.

## Current source layout

The implementation uses a single root source package under `src/multi_agent_platform/`.

This is intentional. It keeps the codebase modular without introducing premature multi-package packaging complexity. Domain boundaries still exist as internal subpackages and can be extracted later if the repository outgrows a single root package.

## Domain boundaries

- `multi_agent_platform.contracts` — Typed request, response, state, and entity models
- `multi_agent_platform.application` — Use-case orchestration across repositories and domain logic
- `multi_agent_platform.api` — HTTP routing, dependency wiring, and response shaping
- `multi_agent_platform.orchestration` — Deterministic workflow state transitions
- `multi_agent_platform.storage` — Repository interfaces and implementations
- `multi_agent_platform.agents` — Agent role logic
- `multi_ag.tools` — Tool interfaces and adapters
- `multi_agent_platform.verification` — Deterministic validation and verifier logic
- `multi_agent_platform.observability` — Logging, tracing, and metrics helpers

## Reserved top-level paths

- `apps/` — External interfaces such as operator or user-facing applications
- `services/` — Long-running backend processes and worker entry points
- `packages/` — Future extraction target for independently versioned modules
- `tests/` — Unit, integration, and evaluation coverage
- `infra/` — Environment and deployment assets
- `docs/` — Specifications, decisions, and runbooks

## Current implementation boundary

The repository now includes a runnable FastAPI app with a service layer and an in-memory repository. There is still no database integration, background worker, queueing layer, or external tool execution.
