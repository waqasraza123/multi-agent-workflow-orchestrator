# Go Request Observability

## Purpose

The Go control plane assigns request metadata at the API boundary, logs one structured record for every HTTP request, propagates the same metadata to the private Python worker, persists request metadata on run events, and can export server spans to an OpenTelemetry collector.

This gives operators a stable correlation key across:

- external client request
- Go API route handling
- Go to Python worker call
- Python worker route handling

## Headers

The Go API accepts incoming request metadata:

```text
X-Request-ID: <request-id>
traceparent: <w3c-traceparent>
```

If either header is missing, Go generates it and echoes it on the response. The generated request ID uses this shape:

```text
req_<32-hex-chars>
```

The generated `traceparent` follows the W3C header shape:

```text
00-<32-hex-trace-id>-<16-hex-span-id>-01
```

When an incoming `traceparent` is valid, Go keeps the trace ID and creates a new server span ID. The response and worker calls use the server span context.

## Go Logs

Each request produces a structured `http_request` log record with:

- `request_id`
- `traceparent`
- `method`
- `path`
- `status`
- `bytes`
- `duration_ms`
- `remote_addr`
- `user_agent`

The Go logger writes JSON to stdout through `slog`, so platforms such as Render, Fly, ECS, Kubernetes, and log drains can index these fields directly.

## Durable Event Metadata

Every Go-created run event stores:

- `request_id`
- `traceparent`

The values are persisted in indexed `run_events` columns and copied into the run-event JSON payload. This makes lifecycle queries traceable without parsing log streams first.

Use `GET /runs/{run_id}/events` to retrieve the metadata with each event.

## OpenTelemetry Export

Set an OTLP endpoint to enable span export:

```bash
OTEL_SERVICE_NAME=agent-runway-api-go
OTEL_RESOURCE_ENVIRONMENT=production
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
```

or set the traces endpoint directly:

```bash
OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=http://otel-collector:4318/v1/traces
```

Optional settings:

```bash
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer token
OTEL_EXPORTER_OTLP_TIMEOUT_SECONDS=2
OTEL_EXPORTER_OTLP_QUEUE_SIZE=256
```

The exporter sends OTLP/HTTP JSON server spans asynchronously. If the queue is full, the API drops the span and logs `otel_span_dropped`; request handling is not blocked by collector backpressure.

## Worker Propagation

The Go worker client forwards the same metadata on both worker calls:

- `GET /health`
- `POST /internal/agent/plan`
- `POST /internal/agent/turn`

Forwarded headers:

```text
X-Request-ID: <same-request-id>
traceparent: <same-traceparent>
```

The Python worker echoes both headers on its response and writes an `agent_worker_request` log record with:

- `request_id`
- `traceparent`
- `method`
- `path`
- `status`
- `duration_ms`

## Operational Use

To investigate a single run advancement:

1. Capture the `X-Request-ID` from the client response.
2. Search Go API logs for `request_id`.
3. If the request used `EXECUTION_BACKEND=llm`, search worker logs for the same `request_id`.
4. Open `GET /runs/{run_id}/events` and confirm the event `request_id`.
5. Use the `traceparent` trace ID in an OpenTelemetry backend when span export is enabled.

## Current Boundary

This is intentionally a lightweight OTLP/HTTP exporter owned by the Go service so the current backend has production correlation without adding a larger tracing dependency tree. The next observability hardening step is adding worker-side spans and domain-specific spans around provider calls, database transactions, and workflow state transitions.
