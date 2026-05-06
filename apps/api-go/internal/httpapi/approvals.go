package httpapi

import (
	"encoding/json"
	"errors"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/domain"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/storage"
)

func (handler Handler) ListRunApprovals(response http.ResponseWriter, request *http.Request) {
	runID, query, ok := handler.parseApprovalListRequest(response, request)
	if !ok {
		return
	}

	items, page, err := handler.dependencies.Store.ListApprovals(request.Context(), runID, query)
	if err != nil {
		handler.logError("list run approvals failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to list run approvals")
		return
	}

	writeJSON(response, http.StatusOK, domain.BuildRunApprovalListResponse(items, page))
}

func (handler Handler) CreateRunApproval(response http.ResponseWriter, request *http.Request) {
	runState, ok := handler.getRunState(response, request)
	if !ok {
		return
	}

	var createRequest domain.ApprovalRequestCreate
	decoder := json.NewDecoder(request.Body)
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&createRequest); err != nil {
		writeError(response, http.StatusBadRequest, "Invalid approval create request")
		return
	}

	approval, err := domain.NewApprovalRecord(runState.RunID, createRequest)
	if err != nil {
		writeError(response, http.StatusBadRequest, err.Error())
		return
	}
	eventRecord, err := domain.NewRunEvent(
		runState.RunID,
		domain.RunEventTypeApprovalRequested,
		map[string]any{
			"approval_id": approval.ApprovalID,
			"status":      string(approval.Status),
		},
	)
	if err != nil {
		handler.logError("build approval requested event failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to build approval event")
		return
	}

	storedApproval, err := handler.dependencies.Store.CreateApproval(
		request.Context(),
		approval,
		eventRecord,
	)
	if err != nil {
		handler.logError("create approval failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to create approval")
		return
	}

	writeJSON(response, http.StatusOK, domain.BuildRunApprovalResponse(storedApproval))
}

func (handler Handler) DecideRunApproval(response http.ResponseWriter, request *http.Request) {
	runState, ok := handler.getRunState(response, request)
	if !ok {
		return
	}
	approvalID := chi.URLParam(request, "approval_id")
	if approvalID == "" {
		writeError(response, http.StatusBadRequest, "approval_id is required")
		return
	}

	approval, err := handler.dependencies.Store.GetApproval(
		request.Context(),
		runState.RunID,
		approvalID,
	)
	if errors.Is(err, storage.ErrApprovalNotFound) {
		writeError(response, http.StatusNotFound, "Approval "+approvalID+" does not exist for run "+runState.RunID)
		return
	}
	if err != nil {
		handler.logError("get approval failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to get approval")
		return
	}

	var decisionRequest domain.ApprovalDecisionRequest
	decoder := json.NewDecoder(request.Body)
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&decisionRequest); err != nil {
		writeError(response, http.StatusBadRequest, "Invalid approval decision request")
		return
	}
	decisionRequest.Normalize()
	if err := decisionRequest.Validate(); err != nil {
		writeError(response, http.StatusBadRequest, err.Error())
		return
	}

	decidedApproval, err := domain.DecideApproval(approval, decisionRequest)
	if err != nil {
		writeError(response, http.StatusConflict, err.Error())
		return
	}
	eventRecord, err := domain.NewRunEvent(
		runState.RunID,
		domain.RunEventTypeApprovalDecided,
		map[string]any{
			"approval_id": decidedApproval.ApprovalID,
			"decision":    string(decisionRequest.Decision),
			"status":      string(decidedApproval.Status),
		},
	)
	if err != nil {
		handler.logError("build approval decided event failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to build approval event")
		return
	}

	storedApproval, err := handler.dependencies.Store.UpdateApproval(
		request.Context(),
		decidedApproval,
		eventRecord,
	)
	if errors.Is(err, storage.ErrApprovalNotFound) {
		writeError(response, http.StatusNotFound, "Approval "+approvalID+" does not exist for run "+runState.RunID)
		return
	}
	if err != nil {
		handler.logError("update approval failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to decide approval")
		return
	}

	writeJSON(response, http.StatusOK, domain.BuildRunApprovalResponse(storedApproval))
}

func (handler Handler) parseApprovalListRequest(
	response http.ResponseWriter,
	request *http.Request,
) (string, domain.ApprovalListQuery, bool) {
	if _, ok := handler.getRunState(response, request); !ok {
		return "", domain.ApprovalListQuery{}, false
	}

	values := request.URL.Query()
	limit, ok := parseBoundedIntQuery(response, values.Get("limit"), 20, 1, 100, "limit")
	if !ok {
		return "", domain.ApprovalListQuery{}, false
	}
	offset, ok := parseBoundedIntQuery(response, values.Get("offset"), 0, 0, 0, "offset")
	if !ok {
		return "", domain.ApprovalListQuery{}, false
	}

	var status *domain.ApprovalStatus
	if value := values.Get("status"); value != "" {
		parsedStatus := domain.ApprovalStatus(value)
		if !parsedStatus.Valid() {
			writeError(response, http.StatusBadRequest, "status is not supported")
			return "", domain.ApprovalListQuery{}, false
		}
		status = &parsedStatus
	}

	return chi.URLParam(request, "run_id"), domain.ApprovalListQuery{
		Limit:  limit,
		Offset: offset,
		Status: status,
	}, true
}
