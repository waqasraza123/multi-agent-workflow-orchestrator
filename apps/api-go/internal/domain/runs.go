package domain

import (
	"fmt"
	"strings"
	"time"
)

type WorkflowType string

const (
	WorkflowTypeResearchReport   WorkflowType = "research_report"
	WorkflowTypeTechnicalPlan    WorkflowType = "technical_plan"
	WorkflowTypeDocumentAnalysis WorkflowType = "document_analysis"
	WorkflowTypeAssistedAction   WorkflowType = "assisted_action"
)

type RunStatus string

const (
	RunStatusPending            RunStatus = "pending"
	RunStatusPlanning           RunStatus = "planning"
	RunStatusExecuting          RunStatus = "executing"
	RunStatusWaitingForApproval RunStatus = "waiting_for_approval"
	RunStatusVerifying          RunStatus = "verifying"
	RunStatusFinalizing         RunStatus = "finalizing"
	RunStatusCompleted          RunStatus = "completed"
	RunStatusFailed             RunStatus = "failed"
	RunStatusCancelled          RunStatus = "cancelled"
)

type RunCreateRequest struct {
	UserGoal       string                 `json:"user_goal"`
	WorkflowType   WorkflowType           `json:"workflow_type"`
	Metadata       map[string]any         `json:"metadata"`
	InputFileRefs  []string               `json:"input_file_refs"`
	Constraints    RunConstraints         `json:"constraints"`
	ApprovalPolicy ApprovalPolicy         `json:"approval_policy"`
}

type RunConstraints struct {
	MaxTurns            *int `json:"max_turns"`
	AllowWriteTools     bool `json:"allow_write_tools"`
	MaxToolCallsPerTurn int  `json:"max_tool_calls_per_turn"`
}

type ApprovalPolicy struct {
	Mode                                 string  `json:"mode"`
	RequireHumanApprovalForHighRiskTools bool    `json:"require_human_approval_for_high_risk_tools"`
	MinimumVerificationConfidence        float64 `json:"minimum_verification_confidence"`
}

type TaskRecord struct {
	TaskID             string   `json:"task_id"`
	Title              string   `json:"title"`
	Description        string   `json:"description"`
	AssignedAgent      string   `json:"assigned_agent"`
	Status             string   `json:"status"`
	DependencyIDs      []string `json:"dependency_ids"`
	AcceptanceCriteria []string `json:"acceptance_criteria"`
	RiskLevel          string   `json:"risk_level"`
	AttemptCount       int      `json:"attempt_count"`
}

type EvidenceRecord struct {
	EvidenceID       string  `json:"evidence_id"`
	SourceType       string  `json:"source_type"`
	SourceRef        string  `json:"source_ref"`
	Summary          string  `json:"summary"`
	CollectedByAgent string  `json:"collected_by_agent"`
	Confidence       float64 `json:"confidence"`
}

type RunStateSnapshot struct {
	RunID           string           `json:"run_id"`
	TenantID        string           `json:"tenant_id"`
	OwnerUserID     string           `json:"owner_user_id"`
	CreatedByUserID string           `json:"created_by_user_id"`
	WorkflowType    WorkflowType     `json:"workflow_type"`
	Status          RunStatus        `json:"status"`
	UserGoal        string           `json:"user_goal"`
	CreatedAt       time.Time        `json:"created_at"`
	UpdatedAt       time.Time        `json:"updated_at"`
	Tasks           []TaskRecord     `json:"tasks"`
	Evidence        []EvidenceRecord `json:"evidence"`
	Constraints     RunConstraints   `json:"constraints"`
	ApprovalPolicy  ApprovalPolicy   `json:"approval_policy"`
	CurrentTaskID   *string          `json:"current_task_id"`
	FinalOutputRef  *string          `json:"final_output_ref"`
	FailureSummary  *string          `json:"failure_summary"`
}

type RunSummary struct {
	RunID              string       `json:"run_id"`
	TenantID           string       `json:"tenant_id"`
	OwnerUserID        string       `json:"owner_user_id"`
	WorkflowType       WorkflowType `json:"workflow_type"`
	Status             RunStatus    `json:"status"`
	UserGoal           string       `json:"user_goal"`
	CreatedAt          time.Time    `json:"created_at"`
	UpdatedAt          time.Time    `json:"updated_at"`
	CurrentTaskID      *string      `json:"current_task_id"`
	TaskCount          int          `json:"task_count"`
	CompletedTaskCount int          `json:"completed_task_count"`
	EvidenceCount      int          `json:"evidence_count"`
}

type RunDetail struct {
	RunID              string         `json:"run_id"`
	TenantID           string         `json:"tenant_id"`
	OwnerUserID        string         `json:"owner_user_id"`
	CreatedByUserID    string         `json:"created_by_user_id"`
	WorkflowType       WorkflowType   `json:"workflow_type"`
	Status             RunStatus      `json:"status"`
	UserGoal           string         `json:"user_goal"`
	CreatedAt          time.Time      `json:"created_at"`
	UpdatedAt          time.Time      `json:"updated_at"`
	CurrentTaskID      *string        `json:"current_task_id"`
	FinalOutputRef     *string        `json:"final_output_ref"`
	FailureSummary     *string        `json:"failure_summary"`
	TaskCount          int            `json:"task_count"`
	CompletedTaskCount int            `json:"completed_task_count"`
	EvidenceCount      int            `json:"evidence_count"`
	Constraints        RunConstraints `json:"constraints"`
	ApprovalPolicy     ApprovalPolicy `json:"approval_policy"`
}

type PageInfo struct {
	Limit      int  `json:"limit"`
	Offset     int  `json:"offset"`
	TotalCount int  `json:"total_count"`
	HasMore    bool `json:"has_more"`
}

type RunResponse struct {
	Item RunDetail `json:"item"`
}

type RunStateResponse struct {
	Item RunStateSnapshot `json:"item"`
}

type RunListResponse struct {
	Items []RunSummary `json:"items"`
	Page  PageInfo     `json:"page"`
}

func NewRunState(request RunCreateRequest) (RunStateSnapshot, error) {
	if err := request.NormalizeAndValidate(); err != nil {
		return RunStateSnapshot{}, err
	}
	runID, err := NewID("run")
	if err != nil {
		return RunStateSnapshot{}, err
	}
	now := time.Now().UTC()
	return RunStateSnapshot{
		RunID:          runID,
		WorkflowType:   request.WorkflowType,
		Status:         RunStatusPlanning,
		UserGoal:       strings.TrimSpace(request.UserGoal),
		CreatedAt:      now,
		UpdatedAt:      now,
		Tasks:          []TaskRecord{},
		Evidence:       []EvidenceRecord{},
		Constraints:    request.Constraints,
		ApprovalPolicy: request.ApprovalPolicy,
	}, nil
}

func (request *RunCreateRequest) NormalizeAndValidate() error {
	request.UserGoal = strings.TrimSpace(request.UserGoal)
	if request.UserGoal == "" {
		return fmt.Errorf("user_goal must not be blank")
	}
	if request.WorkflowType == "" {
		request.WorkflowType = WorkflowTypeTechnicalPlan
	}
	if !request.WorkflowType.Valid() {
		return fmt.Errorf("workflow_type is not supported")
	}
	request.Constraints.ApplyDefaults()
	if err := request.Constraints.Validate(); err != nil {
		return err
	}
	request.ApprovalPolicy.ApplyDefaults()
	if err := request.ApprovalPolicy.Validate(); err != nil {
		return err
	}
	if request.Metadata == nil {
		request.Metadata = map[string]any{}
	}
	if request.InputFileRefs == nil {
		request.InputFileRefs = []string{}
	}
	return nil
}

func (workflowType WorkflowType) Valid() bool {
	switch workflowType {
	case WorkflowTypeResearchReport,
		WorkflowTypeTechnicalPlan,
		WorkflowTypeDocumentAnalysis,
		WorkflowTypeAssistedAction:
		return true
	default:
		return false
	}
}

func (status RunStatus) Valid() bool {
	switch status {
	case RunStatusPending,
		RunStatusPlanning,
		RunStatusExecuting,
		RunStatusWaitingForApproval,
		RunStatusVerifying,
		RunStatusFinalizing,
		RunStatusCompleted,
		RunStatusFailed,
		RunStatusCancelled:
		return true
	default:
		return false
	}
}

func (constraints *RunConstraints) ApplyDefaults() {
	if constraints.MaxToolCallsPerTurn == 0 {
		constraints.MaxToolCallsPerTurn = 5
	}
}

func (constraints RunConstraints) Validate() error {
	if constraints.MaxTurns != nil && *constraints.MaxTurns < 1 {
		return fmt.Errorf("max_turns must be at least 1")
	}
	if constraints.MaxToolCallsPerTurn < 1 {
		return fmt.Errorf("max_tool_calls_per_turn must be at least 1")
	}
	return nil
}

func (policy *ApprovalPolicy) ApplyDefaults() {
	zeroPolicy := policy.Mode == "" &&
		policy.MinimumVerificationConfidence == 0 &&
		!policy.RequireHumanApprovalForHighRiskTools
	if policy.Mode == "" {
		policy.Mode = "on_high_risk"
	}
	if policy.MinimumVerificationConfidence == 0 {
		policy.MinimumVerificationConfidence = 0.8
	}
	if zeroPolicy {
		policy.RequireHumanApprovalForHighRiskTools = true
	}
}

func (policy ApprovalPolicy) Validate() error {
	if policy.Mode != "never" && policy.Mode != "on_high_risk" && policy.Mode != "always" {
		return fmt.Errorf("approval policy mode is not supported")
	}
	if policy.MinimumVerificationConfidence < 0 || policy.MinimumVerificationConfidence > 1 {
		return fmt.Errorf("minimum_verification_confidence must be between 0 and 1")
	}
	return nil
}

func BuildRunResponse(snapshot RunStateSnapshot) RunResponse {
	return RunResponse{Item: buildRunDetail(snapshot)}
}

func BuildRunStateResponse(snapshot RunStateSnapshot) RunStateResponse {
	return RunStateResponse{Item: snapshot}
}

func BuildRunListResponse(items []RunStateSnapshot, page PageInfo) RunListResponse {
	summaries := make([]RunSummary, 0, len(items))
	for _, item := range items {
		summaries = append(summaries, buildRunSummary(item))
	}
	return RunListResponse{Items: summaries, Page: page}
}

func buildRunSummary(snapshot RunStateSnapshot) RunSummary {
	return RunSummary{
		RunID:              snapshot.RunID,
		TenantID:           snapshot.TenantID,
		OwnerUserID:        snapshot.OwnerUserID,
		WorkflowType:       snapshot.WorkflowType,
		Status:             snapshot.Status,
		UserGoal:           snapshot.UserGoal,
		CreatedAt:          snapshot.CreatedAt,
		UpdatedAt:          snapshot.UpdatedAt,
		CurrentTaskID:      snapshot.CurrentTaskID,
		TaskCount:          len(snapshot.Tasks),
		CompletedTaskCount: countCompletedTasks(snapshot.Tasks),
		EvidenceCount:      len(snapshot.Evidence),
	}
}

func buildRunDetail(snapshot RunStateSnapshot) RunDetail {
	summary := buildRunSummary(snapshot)
	return RunDetail{
		RunID:              summary.RunID,
		TenantID:           summary.TenantID,
		OwnerUserID:        summary.OwnerUserID,
		CreatedByUserID:    snapshot.CreatedByUserID,
		WorkflowType:       summary.WorkflowType,
		Status:             summary.Status,
		UserGoal:           summary.UserGoal,
		CreatedAt:          summary.CreatedAt,
		UpdatedAt:          summary.UpdatedAt,
		CurrentTaskID:      summary.CurrentTaskID,
		FinalOutputRef:     snapshot.FinalOutputRef,
		FailureSummary:     snapshot.FailureSummary,
		TaskCount:          summary.TaskCount,
		CompletedTaskCount: summary.CompletedTaskCount,
		EvidenceCount:      summary.EvidenceCount,
		Constraints:        snapshot.Constraints,
		ApprovalPolicy:     snapshot.ApprovalPolicy,
	}
}

func countCompletedTasks(tasks []TaskRecord) int {
	count := 0
	for _, task := range tasks {
		if task.Status == "completed" {
			count++
		}
	}
	return count
}
