package storage

import (
	"context"
	"encoding/json"
	"errors"

	"github.com/jackc/pgx/v5"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/domain"
)

var ErrApprovalNotFound = errors.New("approval not found")

func (store *Store) CreateApproval(
	ctx context.Context,
	approval domain.ApprovalRecord,
	eventRecord domain.RunEventRecord,
) (domain.ApprovalRecord, error) {
	payload, err := json.Marshal(approval)
	if err != nil {
		return domain.ApprovalRecord{}, err
	}

	tx, err := store.pool.Begin(ctx)
	if err != nil {
		return domain.ApprovalRecord{}, err
	}
	defer func() {
		_ = tx.Rollback(ctx)
	}()

	_, err = tx.Exec(
		ctx,
		`insert into run_approvals (
			approval_id,
			run_id,
			status,
			requested_at,
			payload
		) values ($1, $2, $3, $4, $5)`,
		approval.ApprovalID,
		approval.RunID,
		string(approval.Status),
		approval.RequestedAt,
		string(payload),
	)
	if err != nil {
		return domain.ApprovalRecord{}, err
	}

	if err := appendEventInTx(ctx, tx, eventRecord); err != nil {
		return domain.ApprovalRecord{}, err
	}
	if err := tx.Commit(ctx); err != nil {
		return domain.ApprovalRecord{}, err
	}
	return approval, nil
}

func (store *Store) UpdateApproval(
	ctx context.Context,
	approval domain.ApprovalRecord,
	eventRecord domain.RunEventRecord,
) (domain.ApprovalRecord, error) {
	payload, err := json.Marshal(approval)
	if err != nil {
		return domain.ApprovalRecord{}, err
	}

	tx, err := store.pool.Begin(ctx)
	if err != nil {
		return domain.ApprovalRecord{}, err
	}
	defer func() {
		_ = tx.Rollback(ctx)
	}()

	commandTag, err := tx.Exec(
		ctx,
		`update run_approvals
		set status = $3,
			requested_at = $4,
			payload = $5
		where approval_id = $1
			and run_id = $2`,
		approval.ApprovalID,
		approval.RunID,
		string(approval.Status),
		approval.RequestedAt,
		string(payload),
	)
	if err != nil {
		return domain.ApprovalRecord{}, err
	}
	if commandTag.RowsAffected() == 0 {
		return domain.ApprovalRecord{}, ErrApprovalNotFound
	}

	if err := appendEventInTx(ctx, tx, eventRecord); err != nil {
		return domain.ApprovalRecord{}, err
	}
	if err := tx.Commit(ctx); err != nil {
		return domain.ApprovalRecord{}, err
	}
	return approval, nil
}

func (store *Store) GetApproval(
	ctx context.Context,
	runID string,
	approvalID string,
) (domain.ApprovalRecord, error) {
	var payload string
	err := store.pool.QueryRow(
		ctx,
		`select payload
		from run_approvals
		where run_id = $1
			and approval_id = $2`,
		runID,
		approvalID,
	).Scan(&payload)
	if errors.Is(err, pgx.ErrNoRows) {
		return domain.ApprovalRecord{}, ErrApprovalNotFound
	}
	if err != nil {
		return domain.ApprovalRecord{}, err
	}

	var approval domain.ApprovalRecord
	if err := json.Unmarshal([]byte(payload), &approval); err != nil {
		return domain.ApprovalRecord{}, err
	}
	return approval, nil
}

func (store *Store) ListApprovals(
	ctx context.Context,
	runID string,
	query domain.ApprovalListQuery,
) ([]domain.ApprovalRecord, domain.PageInfo, error) {
	var status *string
	if query.Status != nil {
		value := string(*query.Status)
		status = &value
	}

	var totalCount int
	if err := store.pool.QueryRow(
		ctx,
		`select count(*)
		from run_approvals
		where run_id = $1
			and ($2::text is null or status = $2)`,
		runID,
		status,
	).Scan(&totalCount); err != nil {
		return nil, domain.PageInfo{}, err
	}

	rows, err := store.pool.Query(
		ctx,
		`select payload
		from run_approvals
		where run_id = $1
			and ($4::text is null or status = $4)
		order by requested_at desc, approval_id desc
		limit $2 offset $3`,
		runID,
		query.Limit,
		query.Offset,
		status,
	)
	if err != nil {
		return nil, domain.PageInfo{}, err
	}
	defer rows.Close()

	items := make([]domain.ApprovalRecord, 0)
	for rows.Next() {
		var payload string
		if err := rows.Scan(&payload); err != nil {
			return nil, domain.PageInfo{}, err
		}
		var item domain.ApprovalRecord
		if err := json.Unmarshal([]byte(payload), &item); err != nil {
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
