package storage

import (
	"context"
	"encoding/json"

	"github.com/waqasraza123/agent-runway/apps/api-go/internal/domain"
)

func (store *Store) SaveVerificationReport(
	ctx context.Context,
	report domain.RunVerificationReport,
	eventRecord domain.RunEventRecord,
) (domain.RunVerificationReport, error) {
	payload, err := json.Marshal(report)
	if err != nil {
		return domain.RunVerificationReport{}, err
	}

	tx, err := store.pool.Begin(ctx)
	if err != nil {
		return domain.RunVerificationReport{}, err
	}
	defer func() {
		_ = tx.Rollback(ctx)
	}()

	_, err = tx.Exec(
		ctx,
		`insert into run_verifications (
			verification_id,
			run_id,
			verdict,
			created_at,
			payload
		) values ($1, $2, $3, $4, $5)`,
		report.VerificationID,
		report.RunID,
		string(report.Verdict),
		report.CreatedAt,
		string(payload),
	)
	if err != nil {
		return domain.RunVerificationReport{}, err
	}

	if err := appendEventInTx(ctx, tx, eventRecord); err != nil {
		return domain.RunVerificationReport{}, err
	}

	if err := tx.Commit(ctx); err != nil {
		return domain.RunVerificationReport{}, err
	}
	return report, nil
}

func (store *Store) GetLatestRunVerification(
	ctx context.Context,
	runID string,
) (domain.RunVerificationReport, error) {
	var payload string
	err := store.pool.QueryRow(
		ctx,
		`select payload
		from run_verifications
		where run_id = $1
		order by created_at desc, verification_id desc
		limit 1`,
		runID,
	).Scan(&payload)
	if err != nil {
		return domain.RunVerificationReport{}, err
	}

	var report domain.RunVerificationReport
	if err := json.Unmarshal([]byte(payload), &report); err != nil {
		return domain.RunVerificationReport{}, err
	}
	return report, nil
}

func (store *Store) CountPendingApprovals(ctx context.Context, runID string) (int, error) {
	var totalCount int
	err := store.pool.QueryRow(
		ctx,
		`select count(*)
		from run_approvals
		where run_id = $1
			and status = 'pending'`,
		runID,
	).Scan(&totalCount)
	return totalCount, err
}

func (store *Store) SaveFinalOutput(
	ctx context.Context,
	output domain.RunOutputRecord,
	runState domain.RunStateSnapshot,
	eventRecord domain.RunEventRecord,
) (domain.RunOutputRecord, domain.RunStateSnapshot, error) {
	payload, err := json.Marshal(output)
	if err != nil {
		return domain.RunOutputRecord{}, domain.RunStateSnapshot{}, err
	}

	tx, err := store.pool.Begin(ctx)
	if err != nil {
		return domain.RunOutputRecord{}, domain.RunStateSnapshot{}, err
	}
	defer func() {
		_ = tx.Rollback(ctx)
	}()

	_, err = tx.Exec(
		ctx,
		`insert into run_outputs (
			output_id,
			run_id,
			created_at,
			payload
		) values ($1, $2, $3, $4)`,
		output.OutputID,
		output.RunID,
		output.CreatedAt,
		string(payload),
	)
	if err != nil {
		return domain.RunOutputRecord{}, domain.RunStateSnapshot{}, err
	}

	if err := updateRunStateInTx(ctx, tx, runState); err != nil {
		return domain.RunOutputRecord{}, domain.RunStateSnapshot{}, err
	}
	if err := appendEventInTx(ctx, tx, eventRecord); err != nil {
		return domain.RunOutputRecord{}, domain.RunStateSnapshot{}, err
	}

	if err := tx.Commit(ctx); err != nil {
		return domain.RunOutputRecord{}, domain.RunStateSnapshot{}, err
	}
	return output, runState, nil
}

func (store *Store) GetLatestRunOutput(
	ctx context.Context,
	runID string,
) (domain.RunOutputRecord, error) {
	var payload string
	err := store.pool.QueryRow(
		ctx,
		`select payload
		from run_outputs
		where run_id = $1
		order by created_at desc, output_id desc
		limit 1`,
		runID,
	).Scan(&payload)
	if err != nil {
		return domain.RunOutputRecord{}, err
	}

	var output domain.RunOutputRecord
	if err := json.Unmarshal([]byte(payload), &output); err != nil {
		return domain.RunOutputRecord{}, err
	}
	return output, nil
}
