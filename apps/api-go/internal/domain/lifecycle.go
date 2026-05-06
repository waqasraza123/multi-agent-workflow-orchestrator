package domain

import (
	"fmt"
	"sort"
	"strings"
	"time"
)

type VerificationVerdict string

const (
	VerificationVerdictPass VerificationVerdict = "pass"
	VerificationVerdictFail VerificationVerdict = "fail"
)

type VerificationCheck struct {
	Code    string `json:"code"`
	Passed  bool   `json:"passed"`
	Message string `json:"message"`
}

type RunVerificationReport struct {
	VerificationID string              `json:"verification_id"`
	RunID          string              `json:"run_id"`
	Verdict        VerificationVerdict `json:"verdict"`
	CreatedAt      time.Time           `json:"created_at"`
	Checks         []VerificationCheck `json:"checks"`
}

type RunVerificationResponse struct {
	Item RunVerificationReport `json:"item"`
}

type RunOutputRecord struct {
	OutputID     string    `json:"output_id"`
	RunID        string    `json:"run_id"`
	Title        string    `json:"title"`
	Summary      string    `json:"summary"`
	KeyFindings  []string  `json:"key_findings"`
	EvidenceRefs []string  `json:"evidence_refs"`
	ToolCallRefs []string  `json:"tool_call_refs"`
	TurnRefs     []string  `json:"turn_refs"`
	CreatedAt    time.Time `json:"created_at"`
}

type RunOutputResponse struct {
	Item RunOutputRecord `json:"item"`
}

func BuildRunVerificationReport(runState RunStateSnapshot) (RunVerificationReport, error) {
	verificationID, err := NewID("verification")
	if err != nil {
		return RunVerificationReport{}, err
	}

	checks := []VerificationCheck{
		{
			Code:    "run_has_tasks",
			Passed:  len(runState.Tasks) > 0,
			Message: "Run must contain at least one task",
		},
		{
			Code:    "no_active_task",
			Passed:  runState.CurrentTaskID == nil,
			Message: "Run must not have an active task during verification",
		},
		{
			Code:    "all_tasks_completed",
			Passed:  allTasksCompleted(runState.Tasks),
			Message: "All tasks must be completed before verification passes",
		},
	}

	verdict := VerificationVerdictPass
	for _, check := range checks {
		if !check.Passed {
			verdict = VerificationVerdictFail
			break
		}
	}

	return RunVerificationReport{
		VerificationID: verificationID,
		RunID:          runState.RunID,
		Verdict:        verdict,
		CreatedAt:      time.Now().UTC(),
		Checks:         checks,
	}, nil
}

func BuildFinalOutput(
	runState RunStateSnapshot,
	turns []RunTurnRecord,
	toolCalls []RunToolCallRecord,
) (RunOutputRecord, error) {
	outputID, err := NewID("output")
	if err != nil {
		return RunOutputRecord{}, err
	}

	return RunOutputRecord{
		OutputID: outputID,
		RunID:    runState.RunID,
		Title:    "Final output for " + runState.UserGoal,
		Summary: fmt.Sprintf(
			"Completed run with %d tasks, %d evidence items, and %d tool calls.",
			len(runState.Tasks),
			len(runState.Evidence),
			len(toolCalls),
		),
		KeyFindings:  buildKeyFindings(runState, turns, toolCalls),
		EvidenceRefs: buildEvidenceRefs(runState.Evidence),
		ToolCallRefs: buildToolCallRefs(toolCalls),
		TurnRefs:     buildTurnRefs(turns),
		CreatedAt:    time.Now().UTC(),
	}, nil
}

func BuildRunVerificationResponse(report RunVerificationReport) RunVerificationResponse {
	return RunVerificationResponse{Item: report}
}

func BuildRunOutputResponse(output RunOutputRecord) RunOutputResponse {
	return RunOutputResponse{Item: output}
}

func buildKeyFindings(
	runState RunStateSnapshot,
	turns []RunTurnRecord,
	toolCalls []RunToolCallRecord,
) []string {
	findings := make([]string, 0, 6)
	for _, task := range runState.Tasks {
		if task.Status == "completed" {
			findings = append(findings, "Completed "+task.Title)
		}
	}
	for _, toolCall := range toolCalls {
		parts := make([]string, 0, len(toolCall.ToolOutput))
		keys := make([]string, 0, len(toolCall.ToolOutput))
		for key := range toolCall.ToolOutput {
			keys = append(keys, key)
		}
		sort.Strings(keys)
		for _, key := range keys {
			parts = append(parts, toolCall.ToolOutput[key])
		}
		if len(parts) > 0 {
			findings = append(findings, toolCall.ToolName+": "+strings.Join(parts, "; "))
		}
	}
	for _, turn := range turns {
		if turn.Summary != "" {
			findings = append(findings, turn.Summary)
		}
	}
	if len(findings) == 0 {
		findings = append(findings, "Run completed through deterministic execution.")
	}
	if len(findings) > 6 {
		return findings[:6]
	}
	return findings
}

func buildEvidenceRefs(evidence []EvidenceRecord) []string {
	refs := make([]string, 0, len(evidence))
	for _, item := range evidence {
		refs = append(refs, item.EvidenceID)
	}
	return refs
}

func buildToolCallRefs(toolCalls []RunToolCallRecord) []string {
	refs := make([]string, 0, len(toolCalls))
	for _, item := range toolCalls {
		refs = append(refs, item.ToolCallID)
	}
	return refs
}

func buildTurnRefs(turns []RunTurnRecord) []string {
	refs := make([]string, 0, len(turns))
	for _, item := range turns {
		refs = append(refs, item.TurnID)
	}
	return refs
}
