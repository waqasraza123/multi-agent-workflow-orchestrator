# Agent Runway Go Control Plane

This is the first hybrid control-plane slice for Agent Runway.

Current responsibilities:

- expose Go service health/readiness endpoints
- own initial run creation and run reads
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
```

The current endpoints are:

- `GET /health`
- `GET /ready`
- `POST /runs`
- `GET /runs`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/state`

The next implementation step is to port planning and turn advancement into this service while keeping the Python app as the behavior reference.
