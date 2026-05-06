# Go Auth And RBAC

## Purpose

The Go control plane has an opt-in API-boundary authorization layer for production deployments. It protects workflow endpoints with static bearer/API-key tokens while keeping platform probe endpoints public.

This is intentionally simple and deployable before full user accounts, tenants, and audit identities are introduced.

## Configuration

Auth is disabled by default:

```bash
AUTH_MODE=disabled
```

Enable auth in deployed environments:

```bash
AUTH_MODE=bearer
```

or:

```bash
AUTH_MODE=api_key
```

Token lists are comma-separated:

```bash
AUTH_VIEWER_TOKENS=view-token-1,view-token-2
AUTH_OPERATOR_TOKENS=operator-token
AUTH_ADMIN_TOKENS=admin-token
```

When `AUTH_MODE` is not `disabled`, the Go API fails closed for workflow endpoints if no tokens are configured.

## Client Headers

Preferred header:

```text
Authorization: Bearer <token>
```

Compatibility header:

```text
X-API-Key: <token>
```

Tokens are compared using constant-time comparison. Tokens are never logged by the auth layer.

## Public Endpoints

These endpoints stay public for load balancers and platform health checks:

- `GET /health`
- `GET /ready`

## Roles

Role inheritance:

```text
admin > operator > viewer
```

Viewer permissions:

- `GET /runs`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/state`
- `GET /runs/{run_id}/plans/latest`
- `GET /runs/{run_id}/verifications/latest`
- `GET /runs/{run_id}/outputs/latest`
- `GET /runs/{run_id}/approvals`
- `GET /runs/{run_id}/events`
- `GET /runs/{run_id}/turns`
- `GET /runs/{run_id}/tool-calls`
- `GET /runs/{run_id}/llm-calls`

Operator permissions:

- all viewer permissions
- `POST /runs`
- `POST /runs/{run_id}/plan`
- `POST /runs/{run_id}/turns/advance`
- `POST /runs/{run_id}/verify`
- `POST /runs/{run_id}/finalize`
- `POST /runs/{run_id}/approvals`
- `POST /runs/{run_id}/approvals/{approval_id}/decide`

Admin permissions:

- all operator permissions

## Failure Modes

- Missing token: `401`
- Unknown token: `401`
- Known token without enough role access: `403`
- Auth enabled with no configured tokens: `503`

## Rotation Guidance

Use comma-separated token lists for zero-downtime rotation:

1. Add the new token beside the old token.
2. Deploy or reload environment variables.
3. Move clients to the new token.
4. Remove the old token.

## Next Auth Hardening

The next auth upgrade is replacing static tokens with durable user/tenant identity:

- signed JWT validation
- user and tenant tables
- ownership checks on run reads and mutations
- audit actor IDs on approvals, finalization, and future manual actions
