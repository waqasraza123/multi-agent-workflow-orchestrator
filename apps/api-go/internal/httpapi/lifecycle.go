package httpapi

import (
	"errors"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/jackc/pgx/v5"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/domain"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/storage"
)

func (handler Handler) VerifyRun(response http.ResponseWriter, request *http.Request) {
	runState, ok := handler.getRunState(response, request)
	if !ok {
		return
	}

	report, err := domain.BuildRunVerificationReport(runState)
	if err != nil {
		handler.logError("build verification report failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to build verification report")
		return
	}
	eventRecord, err := domain.NewRunEvent(
		runState.RunID,
		domain.RunEventTypeVerificationCompleted,
		map[string]any{"verdict": string(report.Verdict)},
	)
	if err != nil {
		handler.logError("build verification event failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to build verification event")
		return
	}

	storedReport, err := handler.dependencies.Store.SaveVerificationReport(
		request.Context(),
		report,
		eventRecord,
	)
	if err != nil {
		handler.logError("save verification report failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to save verification report")
		return
	}

	writeJSON(response, http.StatusOK, domain.BuildRunVerificationResponse(storedReport))
}

func (handler Handler) GetLatestVerification(response http.ResponseWriter, request *http.Request) {
	runID := chi.URLParam(request, "run_id")
	if _, ok := handler.getRunState(response, request); !ok {
		return
	}

	report, err := handler.dependencies.Store.GetLatestRunVerification(request.Context(), runID)
	if errors.Is(err, pgx.ErrNoRows) {
		writeError(response, http.StatusNotFound, "Latest verification does not exist for run "+runID)
		return
	}
	if err != nil {
		handler.logError("get latest verification failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to get latest verification")
		return
	}

	writeJSON(response, http.StatusOK, domain.BuildRunVerificationResponse(report))
}

func (handler Handler) FinalizeRun(response http.ResponseWriter, request *http.Request) {
	runState, ok := handler.getRunState(response, request)
	if !ok {
		return
	}
	if runState.Status != domain.RunStatusVerifying {
		writeError(response, http.StatusConflict, "Run "+runState.RunID+" must be verifying before it can be finalized")
		return
	}

	verificationReport, err := handler.dependencies.Store.GetLatestRunVerification(
		request.Context(),
		runState.RunID,
	)
	if errors.Is(err, pgx.ErrNoRows) {
		writeError(response, http.StatusConflict, "Run "+runState.RunID+" requires a passing verification before finalization")
		return
	}
	if err != nil {
		handler.logError("get latest verification for finalization failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to get latest verification")
		return
	}
	if verificationReport.Verdict != domain.VerificationVerdictPass {
		writeError(response, http.StatusConflict, "Run "+runState.RunID+" requires a passing verification before finalization")
		return
	}

	pendingApprovals, err := handler.dependencies.Store.CountPendingApprovals(
		request.Context(),
		runState.RunID,
	)
	if err != nil {
		handler.logError("count pending approvals failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to check pending approvals")
		return
	}
	if pendingApprovals > 0 {
		writeError(response, http.StatusConflict, "Run "+runState.RunID+" has pending approvals and cannot be finalized")
		return
	}

	turns, _, err := handler.dependencies.Store.ListRunTurns(
		request.Context(),
		runState.RunID,
		storage.ArtifactListQuery{Limit: 100, Offset: 0},
	)
	if err != nil {
		handler.logError("list turns for finalization failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to list run turns")
		return
	}
	toolCalls, _, err := handler.dependencies.Store.ListRunToolCalls(
		request.Context(),
		runState.RunID,
		storage.ArtifactListQuery{Limit: 100, Offset: 0},
	)
	if err != nil {
		handler.logError("list tool calls for finalization failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to list run tool calls")
		return
	}

	output, err := domain.BuildFinalOutput(runState, turns, toolCalls)
	if err != nil {
		handler.logError("build final output failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to build final output")
		return
	}

	runState.Status = domain.RunStatusCompleted
	runState.FinalOutputRef = &output.OutputID
	runState.UpdatedAt = time.Now().UTC()

	eventRecord, err := domain.NewRunEvent(
		runState.RunID,
		domain.RunEventTypeRunFinalized,
		map[string]any{
			"output_id": output.OutputID,
			"status":    string(domain.RunStatusCompleted),
		},
	)
	if err != nil {
		handler.logError("build finalization event failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to build finalization event")
		return
	}

	storedOutput, _, err := handler.dependencies.Store.SaveFinalOutput(
		request.Context(),
		output,
		runState,
		eventRecord,
	)
	if err != nil {
		handler.logError("save final output failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to finalize run")
		return
	}

	writeJSON(response, http.StatusOK, domain.BuildRunOutputResponse(storedOutput))
}

func (handler Handler) GetLatestOutput(response http.ResponseWriter, request *http.Request) {
	runID := chi.URLParam(request, "run_id")
	if _, ok := handler.getRunState(response, request); !ok {
		return
	}

	output, err := handler.dependencies.Store.GetLatestRunOutput(request.Context(), runID)
	if errors.Is(err, pgx.ErrNoRows) {
		writeError(response, http.StatusNotFound, "Latest output does not exist for run "+runID)
		return
	}
	if err != nil {
		handler.logError("get latest output failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to get latest output")
		return
	}

	writeJSON(response, http.StatusOK, domain.BuildRunOutputResponse(output))
}
