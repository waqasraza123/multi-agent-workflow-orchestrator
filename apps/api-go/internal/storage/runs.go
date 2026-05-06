package storage

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"time"

	"github.com/jackc/pgx/v5"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/domain"
)

var ErrRunNotFound = errors.New("run not found")

type RunListQuery struct {
	Limit        int
	Offset       int
	Status       *domain.RunStatus
	WorkflowType *domain.WorkflowType
}

func (store *Store) CreateRunState(
	ctx context.Context,
	snapshot domain.RunStateSnapshot,
) (domain.RunStateSnapshot, error) {
	payload, err := json.Marshal(snapshot)
	if err != nil {
		return domain.RunStateSnapshot{}, err
	}
	eventID, err := domain.NewID("event")
	if err != nil {
		return domain.RunStateSnapshot{}, err
	}
	occurredAt := time.Now().UTC()
	eventPayload, err := json.Marshal(map[string]any{
		"event_id":    eventID,
		"run_id":      snapshot.RunID,
		"event_type":  "run_created",
		"occurred_at": occurredAt,
		"payload": map[string]string{
			"workflow_type": string(snapshot.WorkflowType),
			"status":        string(snapshot.Status),
		},
	})
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
			workflow_type,
			status,
			created_at,
			updated_at,
			payload
		) values ($1, $2, $3, $4, $5, $6)`,
		snapshot.RunID,
		string(snapshot.WorkflowType),
		string(snapshot.Status),
		snapshot.CreatedAt,
		snapshot.UpdatedAt,
		string(payload),
	)
	if err != nil {
		return domain.RunStateSnapshot{}, err
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
		eventID,
		snapshot.RunID,
		"run_created",
		occurredAt,
		string(eventPayload),
	)
	if err != nil {
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
	err := store.pool.QueryRow(
		ctx,
		`select payload from run_states where run_id = $1`,
		runID,
	).Scan(&payload)
	if errors.Is(err, pgx.ErrNoRows) {
		return domain.RunStateSnapshot{}, ErrRunNotFound
	}
	if err != nil {
		return domain.RunStateSnapshot{}, err
	}
	return decodeRunState(payload)
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

	var totalCount int
	if err := store.pool.QueryRow(
		ctx,
		`select count(*)
		from run_states
		where ($1::text is null or status = $1)
			and ($2::text is null or workflow_type = $2)`,
		status,
		workflowType,
	).Scan(&totalCount); err != nil {
		return nil, domain.PageInfo{}, err
	}

	rows, err := store.pool.Query(
		ctx,
		`select payload
		from run_states
		where ($3::text is null or status = $3)
			and ($4::text is null or workflow_type = $4)
		order by created_at desc, run_id desc
		limit $1 offset $2`,
		query.Limit,
		query.Offset,
		status,
		workflowType,
	)
	if err != nil {
		return nil, domain.PageInfo{}, err
	}
	defer rows.Close()

	items := make([]domain.RunStateSnapshot, 0)
	for rows.Next() {
		var payload string
		if err := rows.Scan(&payload); err != nil {
			return nil, domain.PageInfo{}, err
		}
		item, err := decodeRunState(payload)
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
