package storage

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/domain"
)

var ErrRunNotFound = errors.New("run not found")

type RunListQuery struct {
	Limit        int
	Offset       int
	Status       *domain.RunStatus
	WorkflowType *domain.WorkflowType
	TenantID     *string
}

func (store *Store) CreateRunState(
	ctx context.Context,
	snapshot domain.RunStateSnapshot,
) (domain.RunStateSnapshot, error) {
	payload, err := json.Marshal(snapshot)
	if err != nil {
		return domain.RunStateSnapshot{}, err
	}
	eventRecord, err := domain.NewRunEvent(
		snapshot.RunID,
		domain.RunEventTypeRunCreated,
		map[string]any{
			"workflow_type": string(snapshot.WorkflowType),
			"status":        string(snapshot.Status),
			"tenant_id":     snapshot.TenantID,
			"owner_user_id": snapshot.OwnerUserID,
		},
	)
	if err != nil {
		return domain.RunStateSnapshot{}, err
	}

	tx, err := store.pool.Begin(ctx)
	if err != nil {
		return domain.RunStateSnapshot{}, err
	}
	defer func() {
		_ = tx.Rollback(ctx)
	}()

	_, err = tx.Exec(
		ctx,
		`insert into run_states (
			run_id,
			tenant_id,
			owner_user_id,
			created_by_user_id,
			workflow_type,
			status,
			created_at,
			updated_at,
			payload
		) values ($1, $2, $3, $4, $5, $6, $7, $8, $9)`,
		snapshot.RunID,
		snapshot.TenantID,
		snapshot.OwnerUserID,
		snapshot.CreatedByUserID,
		string(snapshot.WorkflowType),
		string(snapshot.Status),
		snapshot.CreatedAt,
		snapshot.UpdatedAt,
		string(payload),
	)
	if err != nil {
		return domain.RunStateSnapshot{}, err
	}

	if err := appendEventInTx(ctx, tx, eventRecord); err != nil {
		return domain.RunStateSnapshot{}, err
	}

	if err := tx.Commit(ctx); err != nil {
		return domain.RunStateSnapshot{}, err
	}
	return snapshot, nil
}

func (store *Store) GetRunState(
	ctx context.Context,
	runID string,
) (domain.RunStateSnapshot, error) {
	var payload string
	var tenantID string
	var ownerUserID string
	var createdByUserID string
	err := store.pool.QueryRow(
		ctx,
		`select payload, tenant_id, owner_user_id, created_by_user_id
		from run_states
		where run_id = $1`,
		runID,
	).Scan(&payload, &tenantID, &ownerUserID, &createdByUserID)
	if errors.Is(err, pgx.ErrNoRows) {
		return domain.RunStateSnapshot{}, ErrRunNotFound
	}
	if err != nil {
		return domain.RunStateSnapshot{}, err
	}
	return decodeRunStateWithOwnership(payload, tenantID, ownerUserID, createdByUserID)
}

func (store *Store) ListRunStates(
	ctx context.Context,
	query RunListQuery,
) ([]domain.RunStateSnapshot, domain.PageInfo, error) {
	var status *string
	if query.Status != nil {
		value := string(*query.Status)
		status = &value
	}
	var workflowType *string
	if query.WorkflowType != nil {
		value := string(*query.WorkflowType)
		workflowType = &value
	}
	var tenantID *string
	if query.TenantID != nil {
		value := *query.TenantID
		tenantID = &value
	}

	var totalCount int
	if err := store.pool.QueryRow(
		ctx,
		`select count(*)
		from run_states
		where ($1::text is null or status = $1)
			and ($2::text is null or workflow_type = $2)
			and ($3::text is null or tenant_id = $3)`,
		status,
		workflowType,
		tenantID,
	).Scan(&totalCount); err != nil {
		return nil, domain.PageInfo{}, err
	}

	rows, err := store.pool.Query(
		ctx,
		`select payload, tenant_id, owner_user_id, created_by_user_id
		from run_states
		where ($3::text is null or status = $3)
			and ($4::text is null or workflow_type = $4)
			and ($5::text is null or tenant_id = $5)
		order by created_at desc, run_id desc
		limit $1 offset $2`,
		query.Limit,
		query.Offset,
		status,
		workflowType,
		tenantID,
	)
	if err != nil {
		return nil, domain.PageInfo{}, err
	}
	defer rows.Close()

	items := make([]domain.RunStateSnapshot, 0)
	for rows.Next() {
		var payload string
		var tenantID string
		var ownerUserID string
		var createdByUserID string
		if err := rows.Scan(&payload, &tenantID, &ownerUserID, &createdByUserID); err != nil {
			return nil, domain.PageInfo{}, err
		}
		item, err := decodeRunStateWithOwnership(payload, tenantID, ownerUserID, createdByUserID)
		if err != nil {
			return nil, domain.PageInfo{}, err
		}
		items = append(items, item)
	}
	if err := rows.Err(); err != nil {
		return nil, domain.PageInfo{}, err
	}

	page := domain.PageInfo{
		Limit:      query.Limit,
		Offset:     query.Offset,
		TotalCount: totalCount,
		HasMore:    query.Offset+query.Limit < totalCount,
	}
	return items, page, nil
}

func decodeRunState(payload string) (domain.RunStateSnapshot, error) {
	var snapshot domain.RunStateSnapshot
	if err := json.Unmarshal([]byte(payload), &snapshot); err != nil {
		return domain.RunStateSnapshot{}, fmt.Errorf("decode run state payload: %w", err)
	}
	return snapshot, nil
}

func decodeRunStateWithOwnership(
	payload string,
	tenantID string,
	ownerUserID string,
	createdByUserID string,
) (domain.RunStateSnapshot, error) {
	snapshot, err := decodeRunState(payload)
	if err != nil {
		return domain.RunStateSnapshot{}, err
	}
	snapshot.TenantID = tenantID
	snapshot.OwnerUserID = ownerUserID
	snapshot.CreatedByUserID = createdByUserID
	return snapshot, nil
}

func updateRunStateInTx(
	ctx context.Context,
	tx pgx.Tx,
	snapshot domain.RunStateSnapshot,
) error {
	payload, err := json.Marshal(snapshot)
	if err != nil {
		return err
	}
	_, err = tx.Exec(
		ctx,
		`update run_states
		set workflow_type = $2,
			status = $3,
			created_at = $4,
			updated_at = $5,
			payload = $6,
			tenant_id = $7,
			owner_user_id = $8,
			created_by_user_id = $9
		where run_id = $1`,
		snapshot.RunID,
		string(snapshot.WorkflowType),
		string(snapshot.Status),
		snapshot.CreatedAt,
		snapshot.UpdatedAt,
		string(payload),
		snapshot.TenantID,
		snapshot.OwnerUserID,
		snapshot.CreatedByUserID,
	)
	return err
}

func appendEventInTx(ctx context.Context, tx pgx.Tx, eventRecord domain.RunEventRecord) error {
	payload, err := json.Marshal(eventRecord)
	if err != nil {
		return err
	}
	_, err = tx.Exec(
		ctx,
		`insert into run_events (
			event_id,
			run_id,
			event_type,
			occurred_at,
			payload
		) values ($1, $2, $3, $4, $5)`,
		eventRecord.EventID,
		eventRecord.RunID,
		string(eventRecord.EventType),
		eventRecord.OccurredAt,
		string(payload),
	)
	return err
}
