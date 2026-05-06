package domain

import (
	"fmt"
	"strings"
	"time"
)

type ApprovalStatus string

const (
	ApprovalStatusPending           ApprovalStatus = "pending"
	ApprovalStatusApproved          ApprovalStatus = "approved"
	ApprovalStatusRejected          ApprovalStatus = "rejected"
	ApprovalStatusRevisionRequested ApprovalStatus = "revision_requested"
)

type ApprovalDecision string

const (
	ApprovalDecisionApprove         ApprovalDecision = "approve"
	ApprovalDecisionReject          ApprovalDecision = "reject"
	ApprovalDecisionRequestRevision ApprovalDecision = "request_revision"
)

type ApprovalRequestCreate struct {
	RequestedAction       string   `json:"requested_action"`
	Reason                string   `json:"reason"`
	RiskSummary           string   `json:"risk_summary"`
	ProposedNextStep      *string  `json:"proposed_next_step"`
	SupportingEvidenceRefs []string `json:"supporting_evidence_refs"`
}

type ApprovalDecisionRequest struct {
	Decision     ApprovalDecision `json:"decision"`
	ReviewerID   string           `json:"reviewer_id"`
	ReviewerNote *string          `json:"reviewer_note"`
}

type ApprovalRecord struct {
	ApprovalID             string         `json:"approval_id"`
	RunID                  string         `json:"run_id"`
	RequestedAction        string         `json:"requested_action"`
	Reason                 string         `json:"reason"`
	RiskSummary            string         `json:"risk_summary"`
	ProposedNextStep       *string        `json:"proposed_next_step"`
	SupportingEvidenceRefs []string       `json:"supporting_evidence_refs"`
	Status                 ApprovalStatus `json:"status"`
	RequestedAt            time.Time      `json:"requested_at"`
	DecidedAt              *time.Time     `json:"decided_at"`
	ReviewerID             *string        `json:"reviewer_id"`
	ReviewerNote           *string        `json:"reviewer_note"`
}

type ApprovalListQuery struct {
	Limit  int
	Offset int
	Status *ApprovalStatus
}

type RunApprovalResponse struct {
	Item ApprovalRecord `json:"item"`
}

type RunApprovalListResponse struct {
	Items []ApprovalRecord `json:"items"`
	Page  PageInfo         `json:"page"`
}

func NewApprovalRecord(runID string, request ApprovalRequestCreate) (ApprovalRecord, error) {
	request.Normalize()
	if err := request.Validate(); err != nil {
		return ApprovalRecord{}, err
	}
	approvalID, err := NewID("approval")
	if err != nil {
		return ApprovalRecord{}, err
	}
	return ApprovalRecord{
		ApprovalID:             approvalID,
		RunID:                  runID,
		RequestedAction:        request.RequestedAction,
		Reason:                 request.Reason,
		RiskSummary:            request.RiskSummary,
		ProposedNextStep:       request.ProposedNextStep,
		SupportingEvidenceRefs: request.SupportingEvidenceRefs,
		Status:                 ApprovalStatusPending,
		RequestedAt:            time.Now().UTC(),
	}, nil
}

func DecideApproval(record ApprovalRecord, request ApprovalDecisionRequest) (ApprovalRecord, error) {
	request.Normalize()
	if record.Status != ApprovalStatusPending {
		return ApprovalRecord{}, fmt.Errorf("approval %s is no longer pending", record.ApprovalID)
	}
	if err := request.Validate(); err != nil {
		return ApprovalRecord{}, err
	}
	now := time.Now().UTC()
	record.Status = request.Decision.ToStatus()
	record.ReviewerID = &request.ReviewerID
	record.ReviewerNote = request.ReviewerNote
	record.DecidedAt = &now
	return record, nil
}

func (request *ApprovalRequestCreate) Normalize() {
	request.RequestedAction = strings.TrimSpace(request.RequestedAction)
	request.Reason = strings.TrimSpace(request.Reason)
	request.RiskSummary = strings.TrimSpace(request.RiskSummary)
	if request.ProposedNextStep != nil {
		value := strings.TrimSpace(*request.ProposedNextStep)
		request.ProposedNextStep = &value
	}
	for index, value := range request.SupportingEvidenceRefs {
		request.SupportingEvidenceRefs[index] = strings.TrimSpace(value)
	}
	if request.SupportingEvidenceRefs == nil {
		request.SupportingEvidenceRefs = []string{}
	}
}

func (request ApprovalRequestCreate) Validate() error {
	if request.RequestedAction == "" {
		return fmt.Errorf("requested_action must not be blank")
	}
	if request.Reason == "" {
		return fmt.Errorf("reason must not be blank")
	}
	if request.RiskSummary == "" {
		return fmt.Errorf("risk_summary must not be blank")
	}
	if request.ProposedNextStep != nil && *request.ProposedNextStep == "" {
		return fmt.Errorf("proposed_next_step must not be blank when provided")
	}
	for _, value := range request.SupportingEvidenceRefs {
		if value == "" {
			return fmt.Errorf("supporting_evidence_refs must not contain blank values")
		}
	}
	return nil
}

func (request *ApprovalDecisionRequest) Normalize() {
	request.ReviewerID = strings.TrimSpace(request.ReviewerID)
	if request.ReviewerNote != nil {
		value := strings.TrimSpace(*request.ReviewerNote)
		request.ReviewerNote = &value
	}
}

func (request ApprovalDecisionRequest) Validate() error {
	if !request.Decision.Valid() {
		return fmt.Errorf("decision is not supported")
	}
	if request.ReviewerID == "" {
		return fmt.Errorf("reviewer_id must not be blank")
	}
	if request.ReviewerNote != nil && *request.ReviewerNote == "" {
		return fmt.Errorf("reviewer_note must not be blank when provided")
	}
	return nil
}

func (status ApprovalStatus) Valid() bool {
	switch status {
	case ApprovalStatusPending,
		ApprovalStatusApproved,
		ApprovalStatusRejected,
		ApprovalStatusRevisionRequested:
		return true
	default:
		return false
	}
}

func (decision ApprovalDecision) Valid() bool {
	switch decision {
	case ApprovalDecisionApprove,
		ApprovalDecisionReject,
		ApprovalDecisionRequestRevision:
		return true
	default:
		return false
	}
}

func (decision ApprovalDecision) ToStatus() ApprovalStatus {
	switch decision {
	case ApprovalDecisionApprove:
		return ApprovalStatusApproved
	case ApprovalDecisionReject:
		return ApprovalStatusRejected
	default:
		return ApprovalStatusRevisionRequested
	}
}

func BuildRunApprovalResponse(record ApprovalRecord) RunApprovalResponse {
	return RunApprovalResponse{Item: record}
}

func BuildRunApprovalListResponse(items []ApprovalRecord, page PageInfo) RunApprovalListResponse {
	return RunApprovalListResponse{Items: items, Page: page}
}
