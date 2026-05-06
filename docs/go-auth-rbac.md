# Go Auth And RBAC

## Purpose

The Go control plane has an opt-in API-boundary authorization layer for production deployments. It protects workflow endpoints with static bearer/API-key tokens while keeping platform probe endpoints public.

Accepted tokens now resolve to durable user and tenant identities. See `docs/identity-ownership.md` for the ownership data model and backfill behavior.

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

or use externally signed JWTs:

```bash
AUTH_MODE=jwt
```

Token lists are comma-separated:

```bash
AUTH_VIEWER_TOKENS=view-token-1,view-token-2
AUTH_OPERATOR_TOKENS=operator-token
AUTH_ADMIN_TOKENS=admin-token
AUTH_DEFAULT_TENANT_ID=tenant_default
```

When `AUTH_MODE` is not `disabled`, the Go API fails closed for workflow endpoints if no tokens are configured.

For production deployments, add explicit principal mapping:

```bash
AUTH_TOKEN_PRINCIPALS_JSON='[
  {
    "token": "operator-token",
    "tenant_id": "tenant_acme",
    "user_id": "user_alice",
    "subject": "user:alice@example.com",
    "display_name": "Alice"
  }
]'
```

The token must still be present in one of the role token lists. The JSON mapping supplies durable tenant/user identity only.

## JWT Configuration

JWT mode validates `Authorization: Bearer <jwt>` at the API boundary and maps claims to the same durable identity and RBAC model as static tokens.

Shared-secret deployments can use HS256:

```bash
AUTH_MODE=jwt
AUTH_JWT_ALGORITHMS=HS256
AUTH_JWT_SIGNING_SECRET=<shared-secret>
AUTH_JWT_ISSUER=https://issuer.example.com
AUTH_JWT_AUDIENCE=agent-runway-api
```

Identity-provider deployments should use RS256 with either a PEM public key:

```bash
AUTH_MODE=jwt
AUTH_JWT_ALGORITHMS=RS256
AUTH_JWT_PUBLIC_KEY_PEM='-----BEGIN PUBLIC KEY-----...'
AUTH_JWT_ISSUER=https://issuer.example.com
AUTH_JWT_AUDIENCE=agent-runway-api
```

or a JWKS endpoint:

```bash
AUTH_MODE=jwt
AUTH_JWT_ALGORITHMS=RS256
AUTH_JWKS_URL=https://issuer.example.com/.well-known/jwks.json
AUTH_JWKS_CACHE_SECONDS=300
AUTH_JWT_ISSUER=https://issuer.example.com
AUTH_JWT_AUDIENCE=agent-runway-api
```

Claim mapping:

```bash
AUTH_JWT_SUBJECT_CLAIM=sub
AUTH_JWT_TENANT_CLAIM=tenant_id
AUTH_JWT_ROLE_CLAIM=role
AUTH_JWT_DISPLAY_NAME_CLAIM=name
AUTH_JWT_EMAIL_CLAIM=email
```

The role claim may be a string or an array. Supported role values are:

- `admin`
- `operator`
- `viewer`

The validator rejects unsigned tokens, algorithms outside `AUTH_JWT_ALGORITHMS`, expired tokens, future `nbf`, future `iat`, issuer mismatches, and audience mismatches.

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

Raw tokens are not stored in the database. The Go API stores a SHA-256 token fingerprint on the durable user record.

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

## Ownership Enforcement

When auth is enabled:

- `POST /runs` stamps the run with the caller's `tenant_id`, `owner_user_id`, and `created_by_user_id`.
- `GET /runs` only returns runs in the caller's tenant.
- Run reads and mutations return `404` when the run belongs to another tenant.
- Endpoint role checks still apply inside the tenant.

When auth is disabled, local requests use `tenant_default` and `user_local`.

## Failure Modes

- Missing token: `401`
- Unknown token: `401`
- Known token without enough role access: `403`
- Auth enabled with no configured verifier: `503`

## Rotation Guidance

Use comma-separated token lists for zero-downtime rotation:

1. Add the new token beside the old token.
2. Deploy or reload environment variables.
3. Move clients to the new token.
4. Remove the old token.

## Next Auth Hardening

The next auth upgrade is expanding identity operations around the JWT boundary:

- token revocation metadata
- audit actor IDs on approvals, finalization, and future manual actions
