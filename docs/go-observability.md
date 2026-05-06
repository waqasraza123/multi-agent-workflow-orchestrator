# Go Request Observability

## Purpose

The Go control plane now assigns request metadata at the API boundary, logs one structured record for every HTTP request, and propagates the same metadata to the private Python worker.

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

## Worker Propagation

The Go worker client forwards the same metadata on both worker calls:

- `GET /health`
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
4. Use `traceparent` when forwarding logs into a tracing backend that understands W3C trace context.

## Current Boundary

This slice is structured logging and header propagation. It does not yet export spans to an OpenTelemetry collector or persist request IDs on run events. Those are the next observability hardening steps.
