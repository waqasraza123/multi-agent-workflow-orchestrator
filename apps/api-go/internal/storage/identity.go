package storage

import (
	"context"
	"time"

	"github.com/waqasraza123/agent-runway/apps/api-go/internal/domain"
)

func (store *Store) EnsureAuthIdentity(ctx context.Context, identity domain.AuthIdentity) error {
	now := time.Now().UTC()
	tenantName := identity.TenantID
	if tenantName == "" {
		tenantName = "Default Tenant"
	}
	tenantName = truncateForColumn(tenantName, 128)
	displayName := identity.DisplayName
	if displayName == "" {
		displayName = identity.UserID
	}
	displayName = truncateForColumn(displayName, 128)

	tx, err := store.pool.Begin(ctx)
	if err != nil {
		return err
	}
	defer func() {
		_ = tx.Rollback(ctx)
	}()

	_, err = tx.Exec(
		ctx,
		`insert into tenants (
			tenant_id,
			display_name,
			created_at,
			updated_at
		) values ($1, $2, $3, $4)
		on conflict (tenant_id) do update
		set display_name = excluded.display_name,
			updated_at = excluded.updated_at`,
		identity.TenantID,
		tenantName,
		now,
		now,
	)
	if err != nil {
		return err
	}

	_, err = tx.Exec(
		ctx,
		`insert into users (
			user_id,
			subject,
			display_name,
			token_fingerprint,
			created_at,
			updated_at
		) values ($1, $2, $3, $4, $5, $6)
		on conflict (user_id) do update
		set subject = excluded.subject,
			display_name = excluded.display_name,
			token_fingerprint = excluded.token_fingerprint,
			updated_at = excluded.updated_at`,
		identity.UserID,
		identity.Subject,
		displayName,
		identity.TokenFingerprint,
		now,
		now,
	)
	if err != nil {
		return err
	}

	_, err = tx.Exec(
		ctx,
		`insert into tenant_memberships (
			tenant_id,
			user_id,
			role,
			created_at,
			updated_at
		) values ($1, $2, $3, $4, $5)
		on conflict (tenant_id, user_id) do update
		set role = excluded.role,
			updated_at = excluded.updated_at`,
		identity.TenantID,
		identity.UserID,
		identity.Role,
		now,
		now,
	)
	if err != nil {
		return err
	}

	return tx.Commit(ctx)
}

func truncateForColumn(value string, limit int) string {
	if len(value) <= limit {
		return value
	}
	return value[:limit]
}
