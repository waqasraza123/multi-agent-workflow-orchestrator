# Agent Runway Go Control Plane

This is the first hybrid control-plane slice for Agent Runway.

Current responsibilities:

- expose Go service health/readiness endpoints
- enforce opt-in bearer-token RBAC for workflow endpoints
- own initial run creation and run reads
- own deterministic plan generation
- own deterministic and worker-backed LLM turn advancement
- own verification and finalization
- own approval request, listing, and decision flow
- persist turns, tool calls, LLM calls, evidence, and events
- persist approvals, verification reports, and final outputs
- expose persisted events, turns, tool calls, LLM calls, approvals, verifications, and outputs
- connect to PostgreSQL through `pgx`
- write run creation events
- call the private Python agent worker over HTTP
- hold Go structs for the worker-boundary contract
- provide sqlc query scaffolding for the existing run-state table

Run locally after installing Go:

```bash
go mod tidy
go run ./cmd/api
```

Environment:

```bash
HOST=0.0.0.0
PORT=8080
DATABASE_URL=postgres://user:password@localhost:5432/agent_runway?sslmode=disable
AGENT_WORKER_URL=http://127.0.0.1:8090
AGENT_WORKER_TOKEN=
EXECUTION_BACKEND=deterministic
LLM_PROVIDER_NAME=fake
LLM_MODEL_NAME=fake-model
LLM_MAX_RETRIES=0
LLM_TIMEOUT_SECONDS=
LLM_TEMPERATURE=
LLM_MAX_OUTPUT_TOKENS=
AUTH_MODE=disabled
AUTH_VIEWER_TOKENS=
AUTH_OPERATOR_TOKENS=
AUTH_ADMIN_TOKENS=
```

Set `EXECUTION_BACKEND=llm` to call the private Python worker during `POST /runs/{run_id}/turns/advance`. Go still owns the final run state transition and database writes.

If the Python worker is unavailable, the Go control plane falls back to deterministic execution and persists an LLM-call record with the failure details.

Auth is disabled by default for local development. Set `AUTH_MODE=bearer` or `AUTH_MODE=api_key` to protect all workflow endpoints. `GET /health` and `GET /ready` stay public for platform probes. Tokens are comma-separated by role:

```bash
AUTH_MODE=bearer
AUTH_VIEWER_TOKENS=view-token-1,view-token-2
AUTH_OPERATOR_TOKENS=operator-token
AUTH_ADMIN_TOKENS=admin-token
```

Clients send either:

```text
Authorization: Bearer <token>
X-API-Key: <token>
```

Role inheritance is `admin > operator > viewer`. Viewers can read runs and artifacts. Operators can mutate workflow state. Admins currently inherit every operator and viewer permission.

The current endpoints are:

- `GET /health`
- `GET /ready`
- `POST /runs`
- `GET /runs`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/state`
- `POST /runs/{run_id}/plan`
- `GET /runs/{run_id}/plans/latest`
- `POST /runs/{run_id}/turns/advance`
- `POST /runs/{run_id}/verify`
- `GET /runs/{run_id}/verifications/latest`
- `POST /runs/{run_id}/finalize`
- `GET /runs/{run_id}/outputs/latest`
- `GET /runs/{run_id}/approvals`
- `POST /runs/{run_id}/approvals`
- `POST /runs/{run_id}/approvals/{approval_id}/decide`
- `GET /runs/{run_id}/events`
- `GET /runs/{run_id}/turns`
- `GET /runs/{run_id}/tool-calls`
- `GET /runs/{run_id}/llm-calls`

Finalization requires a run in `verifying`, a latest verification verdict of `pass`, and zero pending approvals. The next implementation step is structured request logging, request IDs, and trace propagation between Go and Python.
