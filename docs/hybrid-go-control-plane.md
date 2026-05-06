# Hybrid Go Control Plane

## Purpose

The Go control plane is the production target for Agent Runway's public backend API. It owns durable workflow state, run state transitions, and database writes. The Python service remains the reference implementation during migration and the long-term private execution worker for LLM/provider-heavy work.

## Current Go-Owned Surface

The Go service in `apps/api-go` currently owns:

- `GET /health`
- `GET /ready`
- `POST /runs`
- `GET /runs`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/state`
- `POST /runs/{run_id}/plan`
- `GET /runs/{run_id}/plans/latest`
- `POST /runs/{run_id}/turns/advance`

The Python FastAPI app remains the reference for endpoints that are not listed above.

## State Ownership

Go owns run state mutation for the endpoints it serves. Python must not mutate run state when called as a worker. This keeps state transitions auditable and prevents split-brain behavior between services.

Current Go state transitions:

- Run creation starts a run in `planning`.
- Plan generation registers deterministic template tasks and leaves the run in `planning`.
- Turn advancement starts the next ready task, executes deterministic tool logic, records evidence, completes the task, and moves the run to `executing` or `verifying`.

## Persistence Model

Go writes to the existing Alembic-managed tables:

- `run_states`
- `run_events`
- `run_plans`
- `run_turns`
- `run_tool_calls`

The tables continue to store full JSON payloads in the same model shape used by Python. Go also maintains indexed columns such as `status`, `workflow_type`, `created_at`, `task_id`, and `turn_id`.

Plan generation is persisted transactionally:

1. insert `run_plans`
2. update `run_states`
3. append `plan_generated`
4. append `tasks_registered`

Turn advancement is persisted transactionally:

1. update `run_states`
2. insert `run_tool_calls`
3. insert `run_turns`
4. append `task_started`, `tool_executed`, `evidence_recorded`, `task_completed`, and `turn_executed`

## Deterministic Execution

The first Go execution path intentionally matches the existing Python deterministic behavior:

- planner uses `goal_analyzer`
- researcher uses `evidence_lookup`
- writer uses `summary_writer`
- executor uses `execution_checker`
- unknown agents use `generic_tool`

Tool outputs are deterministic strings derived from the active task title. Evidence is stored inside the run state payload and references the persisted tool call.

## Python Worker Boundary

The private Python worker lives in `services/agent_worker` and exposes:

- `GET /health`
- `POST /internal/agent/turn`

The worker returns structured turn outcomes and does not write to the database.

The next production step is to let Go choose between deterministic execution and worker-backed LLM execution. Go should still own the final run state update, event append, turn record, tool call records, and any fallback decision.

## Operational Notes

Use `make hybrid-up` for local multi-service wiring with Postgres, Alembic migrations, Python worker, and Go API.

Use `make api-go-dev` only after installing Go and running `go mod tidy` in `apps/api-go`.

No Go-native migration system is introduced yet. Alembic remains the migration authority until the schema and Go control-plane ownership are stable.

## Next Implementation Order

1. Wire Go turn advancement to the Python worker for LLM execution.
2. Port Go read/list endpoints for events, turns, tool calls, and plans.
3. Port verification and finalization.
4. Add auth/RBAC at the Go API boundary.
5. Add structured request logging, request IDs, and trace propagation between Go and Python.
