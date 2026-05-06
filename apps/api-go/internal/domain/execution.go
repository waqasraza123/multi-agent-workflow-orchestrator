package domain

import "time"

type RunTurnRecord struct {
	TurnID            string    `json:"turn_id"`
	RunID             string    `json:"run_id"`
	TaskID            string    `json:"task_id"`
	AgentName         string    `json:"agent_name"`
	Summary           string    `json:"summary"`
	ToolCallIDs       []string  `json:"tool_call_ids"`
	EvidenceIDs       []string  `json:"evidence_ids"`
	CreatedAt         time.Time `json:"created_at"`
	ResultingRunStatus RunStatus `json:"resulting_run_status"`
}

type RunTurnAdvanceResponse struct {
	Turn     RunTurnRecord   `json:"turn"`
	RunState RunStateSnapshot `json:"run_state"`
}

type RunToolCallRecord struct {
	ToolCallID string            `json:"tool_call_id"`
	RunID      string            `json:"run_id"`
	TurnID     string            `json:"turn_id"`
	TaskID     string            `json:"task_id"`
	AgentName  string            `json:"agent_name"`
	ToolName   string            `json:"tool_name"`
	ToolInput  map[string]string `json:"tool_input"`
	ToolOutput map[string]string `json:"tool_output"`
	CreatedAt  time.Time         `json:"created_at"`
}

type LLMUsage struct {
	InputTokens      int      `json:"input_tokens"`
	OutputTokens     int      `json:"output_tokens"`
	TotalTokens      int      `json:"total_tokens"`
	EstimatedCostUSD *float64 `json:"estimated_cost_usd"`
}

type StructuredTurnOutput struct {
	Summary          string            `json:"summary"`
	PlannedToolCalls []PlannedToolCall `json:"planned_tool_calls"`
}

type LLMCallRecord struct {
	LLMCallID         string               `json:"llm_call_id"`
	RunID             string               `json:"run_id"`
	TurnID            string               `json:"turn_id"`
	TaskID            string               `json:"task_id"`
	AgentName         string               `json:"agent_name"`
	ProviderName      string               `json:"provider_name"`
	ModelName         string               `json:"model_name"`
	StructuredOutput  StructuredTurnOutput `json:"structured_output"`
	Usage             LLMUsage             `json:"usage"`
	AvailableToolNames []string            `json:"available_tool_names"`
	RequestPayload     map[string]any      `json:"request_payload"`
	ResponsePayload    map[string]any      `json:"response_payload"`
	FinishReason      *string              `json:"finish_reason"`
	LatencyMS         *int                 `json:"latency_ms"`
	ErrorMessage      *string              `json:"error_message"`
	RawResponseText   *string              `json:"raw_response_text"`
	AttemptCount      int                  `json:"attempt_count"`
	FallbackUsed      bool                 `json:"fallback_used"`
	CreatedAt         time.Time            `json:"created_at"`
}

type PlannedToolCall struct {
	ToolName  string            `json:"tool_name"`
	ToolInput map[string]string `json:"tool_input"`
}

type TurnExecutionResult struct {
	Summary          string            `json:"summary"`
	PlannedToolCalls []PlannedToolCall `json:"planned_tool_calls"`
}

func FindNextReadyTask(runState RunStateSnapshot) *TaskRecord {
	for index := range runState.Tasks {
		if runState.Tasks[index].Status == "ready" {
			return &runState.Tasks[index]
		}
	}
	return nil
}

func FindActiveTask(runState RunStateSnapshot) *TaskRecord {
	if runState.CurrentTaskID == nil {
		return nil
	}
	for index := range runState.Tasks {
		if runState.Tasks[index].TaskID == *runState.CurrentTaskID {
			return &runState.Tasks[index]
		}
	}
	return nil
}

func StartTask(runState RunStateSnapshot, taskID string) RunStateSnapshot {
	for index := range runState.Tasks {
		if runState.Tasks[index].TaskID == taskID {
			runState.Tasks[index].Status = "in_progress"
			break
		}
	}
	runState.CurrentTaskID = &taskID
	runState.Status = RunStatusExecuting
	runState.UpdatedAt = time.Now().UTC()
	return runState
}

func CompleteTask(runState RunStateSnapshot, taskID string) RunStateSnapshot {
	completed := completedTaskIDs(runState.Tasks)
	completed[taskID] = struct{}{}

	for index := range runState.Tasks {
		task := &runState.Tasks[index]
		if task.TaskID == taskID {
			task.Status = "completed"
			continue
		}
		if task.Status == "pending" && dependenciesCompleted(*task, completed) {
			task.Status = "ready"
		}
	}

	runState.CurrentTaskID = nil
	if allTasksCompleted(runState.Tasks) {
		runState.Status = RunStatusVerifying
	} else {
		runState.Status = RunStatusExecuting
	}
	runState.UpdatedAt = time.Now().UTC()
	return runState
}

func ExecuteDeterministicTurn(runState RunStateSnapshot, task TaskRecord) TurnExecutionResult {
	return TurnExecutionResult{
		Summary: buildTurnSummary(task.AssignedAgent, task.Title),
		PlannedToolCalls: []PlannedToolCall{
			BuildPlannedToolCall(task.AssignedAgent, runState.UserGoal, task.Title),
		},
	}
}

func BuildPlannedToolCall(agentName string, userGoal string, taskTitle string) PlannedToolCall {
	toolName := "generic_tool"
	switch agentName {
	case "planner":
		toolName = "goal_analyzer"
	case "researcher":
		toolName = "evidence_lookup"
	case "writer":
		toolName = "summary_writer"
	case "executor":
		toolName = "execution_checker"
	}
	return PlannedToolCall{
		ToolName: toolName,
		ToolInput: map[string]string{
			"user_goal":  userGoal,
			"task_title": taskTitle,
			"agent_name": agentName,
		},
	}
}

func ExecutePlannedToolCall(plannedToolCall PlannedToolCall) (map[string]string, map[string]string) {
	toolInput := plannedToolCall.ToolInput
	taskTitle := toolInput["task_title"]

	switch plannedToolCall.ToolName {
	case "goal_analyzer":
		return toolInput, map[string]string{
			"goal_outline":   "Analyzed goal for " + taskTitle,
			"execution_hint": "Proceed with structured planning",
		}
	case "evidence_lookup":
		return toolInput, map[string]string{
			"evidence_summary": "Collected evidence for " + taskTitle,
			"risk_note":        "Dependencies should be validated before delivery",
		}
	case "summary_writer":
		return toolInput, map[string]string{
			"draft_summary": "Prepared summary for " + taskTitle,
			"quality_check": "Draft is ready for review",
		}
	case "execution_checker":
		return toolInput, map[string]string{
			"execution_status": "Prepared execution notes for " + taskTitle,
			"next_step":        "Review execution outcome",
		}
	default:
		return toolInput, map[string]string{
			"result": "Completed deterministic tool execution for " + taskTitle,
		}
	}
}

func BuildEvidenceFromToolCall(toolCall RunToolCallRecord) (EvidenceRecord, error) {
	evidenceID, err := NewID("evidence")
	if err != nil {
		return EvidenceRecord{}, err
	}
	return EvidenceRecord{
		EvidenceID:       evidenceID,
		SourceType:       "tool_call",
		SourceRef:        toolCall.ToolCallID,
		Summary:          "Evidence recorded from " + toolCall.ToolName,
		CollectedByAgent: toolCall.AgentName,
		Confidence:       0.75,
	}, nil
}

func NewToolCallRecord(
	runID string,
	turnID string,
	task TaskRecord,
	plannedToolCall PlannedToolCall,
) (RunToolCallRecord, error) {
	toolCallID, err := NewID("tool")
	if err != nil {
		return RunToolCallRecord{}, err
	}
	toolInput, toolOutput := ExecutePlannedToolCall(plannedToolCall)
	return RunToolCallRecord{
		ToolCallID: toolCallID,
		RunID:      runID,
		TurnID:     turnID,
		TaskID:     task.TaskID,
		AgentName:  task.AssignedAgent,
		ToolName:   plannedToolCall.ToolName,
		ToolInput:  toolInput,
		ToolOutput: toolOutput,
		CreatedAt:  time.Now().UTC(),
	}, nil
}

func NewTurnRecord(
	turnID string,
	runID string,
	task TaskRecord,
	turnResult TurnExecutionResult,
	toolCallIDs []string,
	evidenceIDs []string,
	resultingRunStatus RunStatus,
) RunTurnRecord {
	return RunTurnRecord{
		TurnID:            turnID,
		RunID:             runID,
		TaskID:            task.TaskID,
		AgentName:         task.AssignedAgent,
		Summary:           turnResult.Summary,
		ToolCallIDs:       toolCallIDs,
		EvidenceIDs:       evidenceIDs,
		CreatedAt:         time.Now().UTC(),
		ResultingRunStatus: resultingRunStatus,
	}
}

func NewLLMCallRecord(
	runID string,
	turnID string,
	task TaskRecord,
	providerName string,
	modelName string,
	output StructuredTurnOutput,
	usage LLMUsage,
	availableToolNames []string,
	requestPayload map[string]any,
	responsePayload map[string]any,
	finishReason *string,
	latencyMS *int,
	errorMessage *string,
	rawResponseText *string,
	attemptCount int,
	fallbackUsed bool,
) (LLMCallRecord, error) {
	llmCallID, err := NewID("llm_call")
	if err != nil {
		return LLMCallRecord{}, err
	}
	return LLMCallRecord{
		LLMCallID:         llmCallID,
		RunID:             runID,
		TurnID:            turnID,
		TaskID:            task.TaskID,
		AgentName:         task.AssignedAgent,
		ProviderName:      providerName,
		ModelName:         modelName,
		StructuredOutput:  output,
		Usage:             usage,
		AvailableToolNames: availableToolNames,
		RequestPayload:     requestPayload,
		ResponsePayload:    responsePayload,
		FinishReason:      finishReason,
		LatencyMS:         latencyMS,
		ErrorMessage:      errorMessage,
		RawResponseText:   rawResponseText,
		AttemptCount:      attemptCount,
		FallbackUsed:      fallbackUsed,
		CreatedAt:         time.Now().UTC(),
	}, nil
}

func buildTurnSummary(agentName string, taskTitle string) string {
	switch agentName {
	case "planner":
		return "Planner reviewed the task scope for " + taskTitle + " and prepared the next execution step."
	case "researcher":
		return "Researcher collected and synthesized evidence for " + taskTitle + "."
	case "writer":
		return "Writer drafted the structured output for " + taskTitle + "."
	case "executor":
		return "Executor prepared the execution outcome for " + taskTitle + "."
	default:
		return "Agent completed a deterministic turn for " + taskTitle + "."
	}
}

func completedTaskIDs(tasks []TaskRecord) map[string]struct{} {
	completed := map[string]struct{}{}
	for _, task := range tasks {
		if task.Status == "completed" {
			completed[task.TaskID] = struct{}{}
		}
	}
	return completed
}

func dependenciesCompleted(task TaskRecord, completed map[string]struct{}) bool {
	for _, dependencyID := range task.DependencyIDs {
		if _, ok := completed[dependencyID]; !ok {
			return false
		}
	}
	return true
}

func allTasksCompleted(tasks []TaskRecord) bool {
	if len(tasks) == 0 {
		return false
	}
	for _, task := range tasks {
		if task.Status != "completed" {
			return false
		}
	}
	return true
}
