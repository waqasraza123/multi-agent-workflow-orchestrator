package httpapi

import (
	"encoding/json"
	"errors"
	"net/http"
	"strconv"

	"github.com/go-chi/chi/v5"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/domain"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/storage"
)

func (handler Handler) CreateRun(response http.ResponseWriter, request *http.Request) {
	if handler.dependencies.Store == nil {
		writeError(response, http.StatusServiceUnavailable, "database is not configured")
		return
	}

	var createRequest domain.RunCreateRequest
	decoder := json.NewDecoder(request.Body)
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&createRequest); err != nil {
		writeError(response, http.StatusBadRequest, "Invalid run create request")
		return
	}

	snapshot, err := domain.NewRunState(createRequest)
	if err != nil {
		writeError(response, http.StatusBadRequest, err.Error())
		return
	}
	identity := handler.identityForRequest(request)
	if err := identity.Validate(); err != nil {
		writeError(response, http.StatusServiceUnavailable, "run owner identity is not configured")
		return
	}
	if err := handler.dependencies.Store.EnsureAuthIdentity(request.Context(), identity); err != nil {
		handler.logError("persist run owner identity failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to persist run owner identity")
		return
	}
	snapshot.ApplyOwnership(identity)
	createdSnapshot, err := handler.dependencies.Store.CreateRunState(request.Context(), snapshot)
	if err != nil {
		handler.logError("create run failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to create run")
		return
	}

	writeJSON(response, http.StatusCreated, domain.BuildRunResponse(createdSnapshot))
}

func (handler Handler) ListRuns(response http.ResponseWriter, request *http.Request) {
	if handler.dependencies.Store == nil {
		writeError(response, http.StatusServiceUnavailable, "database is not configured")
		return
	}

	query, ok := parseRunListQuery(response, request)
	if !ok {
		return
	}
	if handler.dependencies.Settings.AuthEnabled() {
		identity, ok := currentAuthIdentity(request)
		if !ok {
			writeError(response, http.StatusUnauthorized, "authentication identity is required")
			return
		}
		query.TenantID = &identity.TenantID
	}
	items, page, err := handler.dependencies.Store.ListRunStates(request.Context(), query)
	if err != nil {
		handler.logError("list runs failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to list runs")
		return
	}

	writeJSON(response, http.StatusOK, domain.BuildRunListResponse(items, page))
}

func (handler Handler) GetRun(response http.ResponseWriter, request *http.Request) {
	snapshot, ok := handler.getRunState(response, request)
	if !ok {
		return
	}
	writeJSON(response, http.StatusOK, domain.BuildRunResponse(snapshot))
}

func (handler Handler) GetRunState(response http.ResponseWriter, request *http.Request) {
	snapshot, ok := handler.getRunState(response, request)
	if !ok {
		return
	}
	writeJSON(response, http.StatusOK, domain.BuildRunStateResponse(snapshot))
}

func (handler Handler) getRunState(
	response http.ResponseWriter,
	request *http.Request,
) (domain.RunStateSnapshot, bool) {
	if handler.dependencies.Store == nil {
		writeError(response, http.StatusServiceUnavailable, "database is not configured")
		return domain.RunStateSnapshot{}, false
	}

	runID := chi.URLParam(request, "run_id")
	if runID == "" {
		writeError(response, http.StatusBadRequest, "run_id is required")
		return domain.RunStateSnapshot{}, false
	}

	snapshot, err := handler.dependencies.Store.GetRunState(request.Context(), runID)
	if errors.Is(err, storage.ErrRunNotFound) {
		writeError(response, http.StatusNotFound, "Run "+runID+" does not exist")
		return domain.RunStateSnapshot{}, false
	}
	if err != nil {
		handler.logError("get run failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to get run")
		return domain.RunStateSnapshot{}, false
	}
	if !handler.canAccessRun(request, snapshot) {
		writeError(response, http.StatusNotFound, "Run "+runID+" does not exist")
		return domain.RunStateSnapshot{}, false
	}
	return snapshot, true
}

func (handler Handler) identityForRequest(request *http.Request) domain.AuthIdentity {
	if identity, ok := currentAuthIdentity(request); ok {
		return identity
	}
	return domain.LocalAuthIdentity(handler.dependencies.Settings.AuthDefaultTenantID)
}

func (handler Handler) canAccessRun(request *http.Request, snapshot domain.RunStateSnapshot) bool {
	if !handler.dependencies.Settings.AuthEnabled() {
		return true
	}
	identity, ok := currentAuthIdentity(request)
	if !ok {
		return false
	}
	if snapshot.TenantID == "" {
		return false
	}
	return snapshot.TenantID == identity.TenantID
}

func parseRunListQuery(
	response http.ResponseWriter,
	request *http.Request,
) (storage.RunListQuery, bool) {
	values := request.URL.Query()
	limit, ok := parseBoundedIntQuery(response, values.Get("limit"), 20, 1, 100, "limit")
	if !ok {
		return storage.RunListQuery{}, false
	}
	offset, ok := parseBoundedIntQuery(response, values.Get("offset"), 0, 0, 0, "offset")
	if !ok {
		return storage.RunListQuery{}, false
	}

	var status *domain.RunStatus
	if value := values.Get("status"); value != "" {
		parsedStatus := domain.RunStatus(value)
		if !parsedStatus.Valid() {
			writeError(response, http.StatusBadRequest, "status is not supported")
			return storage.RunListQuery{}, false
		}
		status = &parsedStatus
	}

	var workflowType *domain.WorkflowType
	if value := values.Get("workflow_type"); value != "" {
		parsedWorkflowType := domain.WorkflowType(value)
		if !parsedWorkflowType.Valid() {
			writeError(response, http.StatusBadRequest, "workflow_type is not supported")
			return storage.RunListQuery{}, false
		}
		workflowType = &parsedWorkflowType
	}

	return storage.RunListQuery{
		Limit:        limit,
		Offset:       offset,
		Status:       status,
		WorkflowType: workflowType,
	}, true
}

func parseBoundedIntQuery(
	response http.ResponseWriter,
	value string,
	fallback int,
	minimum int,
	maximum int,
	name string,
) (int, bool) {
	if value == "" {
		return fallback, true
	}
	parsed, err := strconv.Atoi(value)
	if err != nil {
		writeError(response, http.StatusBadRequest, name+" must be an integer")
		return 0, false
	}
	if parsed < minimum {
		writeError(response, http.StatusBadRequest, name+" is below the minimum")
		return 0, false
	}
	if maximum > 0 && parsed > maximum {
		writeError(response, http.StatusBadRequest, name+" is above the maximum")
		return 0, false
	}
	return parsed, true
}
