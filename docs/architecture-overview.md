# Architecture overview

This repository is a production-grade multi-agent research and execution platform.

## Current source layout

The implementation uses a single root source package under `src/multi_agent_platform/`.

This keeps the codebase modular without introducing premature multi-package packaging complexity. Domain boundaries exist as internal subpackages and can be extracted later if the repository outgrows a single root package.

## Domain boundaries

- `multi_agent_platform.contracts` - Typed request, query, response, state, entity, command, event, verification, approval, planning, and turn models
- `multi_agent_platform.application` - Use-case orchestration across repositories and domain logic
- `multi_agent_platform.api` - HTTP routing, dependency wiring, and response shaping
- `multi_agent_platform.orchestration` - Deterministic workflow state transitions
- `multi_agent_platform.planning` - Deterministic workflow planning templates and task graph generation
- `multi_agent_platform.agents` - Deterministic agent turn execution
- `multi_agent_platform.storage` - Repository interfaces and implementations
- `multi_agent_platform.tools` - Tool interfaces and adapters
- `multi_agent_platform.verification` - Deterministic validation and verifier logic
- `multi_agent_platform.observability` - Logging, tracing, and metrics helpers

## Current implementation boundary

The repository includes a runnable FastAPI app with application services, in-memory repositories for runs, events, verifications, approvals, plans, and turns, deterministic workflow state transitions, explicit audit and review surfaces, deterministic plan generation, and deterministic turn-based execution.
