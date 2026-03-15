# Decision log

## Foundation decisions

- Monorepo layout
- Python 3.12 baseline
- uv for environment and package management
- Ruff, mypy, pytest as quality gates

## Execution model decisions

- backend-first architecture
- deterministic planning before external intelligence
- deterministic turn runtime before provider-backed execution
- explicit contracts between API, application, orchestration, and storage
- repository boundaries before durable infrastructure

## Storage decisions

- keep repository interfaces stable
- support in-memory persistence for fast iteration
- add SQL-backed persistence behind the same service boundary
- use SQLAlchemy 2 style engine and session patterns
- use SQLite for local durability and integration tests
- keep schema compatible with a later PostgreSQL move

## Finalization decisions

- final output is a first-class persisted record
- a run must verify successfully before finalization
- pending approvals block finalization
- completed state must reference the final output identifier
