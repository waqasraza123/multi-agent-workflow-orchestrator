# Agent Runway Python Agent Worker

Private worker service for LLM/provider-backed planning and turn execution.

Run locally:

```bash
uv run uvicorn services.agent_worker.app:app --host 0.0.0.0 --port 8090 --reload
```

Endpoints:

- `GET /health`
- `POST /internal/agent/plan`
- `POST /internal/agent/turn`

Environment:

```bash
AGENT_WORKER_TOKEN=
LLM_API_KEY=
LLM_API_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4.1-mini
```

If `AGENT_WORKER_TOKEN` is set, requests to internal worker endpoints must include:

```text
Authorization: Bearer <token>
```

This service returns structured planning and turn execution outcomes. It does not mutate run state.

`POST /internal/agent/plan` returns structured planning output. The Go control plane validates and persists the plan; the worker does not write state.

The Go control plane forwards request correlation headers:

```text
X-Request-ID: <request-id>
traceparent: <w3c-traceparent>
```

The worker echoes both headers and logs `agent_worker_request` with request ID, traceparent, method, path, status, and duration.
