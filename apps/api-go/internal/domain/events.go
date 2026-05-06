package domain

import "time"

type RunEventType string

const (
	RunEventTypeRunCreated            RunEventType = "run_created"
	RunEventTypeTasksRegistered       RunEventType = "tasks_registered"
	RunEventTypeTaskStarted           RunEventType = "task_started"
	RunEventTypeTaskCompleted         RunEventType = "task_completed"
	RunEventTypeEvidenceRecorded      RunEventType = "evidence_recorded"
	RunEventTypeVerificationCompleted RunEventType = "verification_completed"
	RunEventTypeApprovalRequested     RunEventType = "approval_requested"
	RunEventTypeApprovalDecided       RunEventType = "approval_decided"
	RunEventTypePlanGenerated         RunEventType = "plan_generated"
	RunEventTypeTurnExecuted          RunEventType = "turn_executed"
	RunEventTypeToolExecuted          RunEventType = "tool_executed"
	RunEventTypeRunFinalized          RunEventType = "run_finalized"
)

type RunEventRecord struct {
	EventID    string         `json:"event_id"`
	RunID      string         `json:"run_id"`
	EventType  RunEventType   `json:"event_type"`
	OccurredAt time.Time      `json:"occurred_at"`
	Payload    map[string]any `json:"payload"`
}

func NewRunEvent(runID string, eventType RunEventType, payload map[string]any) (RunEventRecord, error) {
	eventID, err := NewID("event")
	if err != nil {
		return RunEventRecord{}, err
	}
	return RunEventRecord{
		EventID:    eventID,
		RunID:      runID,
		EventType:  eventType,
		OccurredAt: time.Now().UTC(),
		Payload:    payload,
	}, nil
}
