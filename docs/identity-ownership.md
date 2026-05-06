# Identity And Ownership

## Purpose

Agent Runway now has a durable identity boundary for the Go control plane. Static bearer/API-key tokens and signed JWTs both resolve to a user, tenant, and role before workflow handlers run.

The goal is tenant isolation for runs without introducing a full external identity provider yet.

## Data Model

The ownership schema is introduced by:

- `migrations/versions/0002_identity_ownership.py`
- `apps/api-go/schema/0002_identity_ownership.sql`

Tables:

- `tenants`: durable tenant records.
- `users`: durable user records keyed by `user_id` with a stable auth `subject`.
- `tenant_memberships`: role for a user inside a tenant.

Run ownership columns on `run_states`:

- `tenant_id`
- `owner_user_id`
- `created_by_user_id`

The full run JSON payload also includes the same ownership fields so API responses and archived payloads remain self-describing. The indexed `run_states` columns are the source of truth; repository reads overlay those column values onto the JSON payload before returning a run.

## Static Token Principal Resolution

Existing token lists remain the role authority:

```bash
AUTH_VIEWER_TOKENS=view-token
AUTH_OPERATOR_TOKENS=operator-token
AUTH_ADMIN_TOKENS=admin-token
```

By default, tokens are mapped to deterministic users in `AUTH_DEFAULT_TENANT_ID`:

```bash
AUTH_DEFAULT_TENANT_ID=tenant_default
```

For production deployments, configure explicit token principals:

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

The token must still appear in one of the role token lists. `AUTH_TOKEN_PRINCIPALS_JSON` only supplies the durable tenant/user identity.

## JWT Principal Resolution

In `AUTH_MODE=jwt`, the JWT subject claim becomes the durable user subject. The durable `user_id` is a stable hash of that subject. The tenant and role are read from configurable claims:

```bash
AUTH_JWT_SUBJECT_CLAIM=sub
AUTH_JWT_TENANT_CLAIM=tenant_id
AUTH_JWT_ROLE_CLAIM=role
AUTH_JWT_DISPLAY_NAME_CLAIM=name
AUTH_JWT_EMAIL_CLAIM=email
```

The Go API stores a SHA-256 fingerprint of the accepted JWT, not the raw token.

## Request Behavior

When `AUTH_MODE` is enabled:

1. The token is authenticated and mapped to a role.
2. The token or JWT is resolved to a durable tenant/user principal.
3. The Go API upserts `tenants`, `users`, and `tenant_memberships`.
4. `POST /runs` stamps new runs with `tenant_id`, `owner_user_id`, and `created_by_user_id`.
5. `GET /runs` filters by the caller's tenant.
6. Run reads and mutations return `404` for runs outside the caller's tenant.

Health endpoints remain public.

When auth is disabled, local development uses:

```text
tenant_id=tenant_default
user_id=user_local
role=admin
```

## Backfill

The `0002_identity_ownership` migration backfills existing runs to:

```text
tenant_id=tenant_default
owner_user_id=user_legacy
created_by_user_id=user_legacy
```

That keeps old local data readable after migration while new authenticated production traffic receives explicit ownership.

## Security Notes

- Raw tokens are not stored in the identity tables.
- The Go API stores a SHA-256 token fingerprint for diagnostics and rotation tracking.
- Cross-tenant run access is masked as `404` to avoid confirming another tenant's run IDs.
- Roles continue to gate endpoint capability; tenant ownership gates data scope.
