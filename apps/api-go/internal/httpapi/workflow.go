package httpapi

import (
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/domain"
)

func (handler Handler) GeneratePlan(response http.ResponseWriter, request *http.Request) {
	runState, ok := handler.getRunState(response, request)
	if !ok {
		return
	}
	if len(runState.Tasks) > 0 {
		writeError(
			response,
			http.StatusConflict,
			"Run "+runState.RunID+" already has registered tasks and cannot be planned again",
		)
		return
	}

	plan, err := domain.BuildRunPlan(runState)
	if err != nil {
		handler.logError("build plan failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to build run plan")
		return
	}
	updatedRunState, err := domain.RegisterTasks(runState, plan.Tasks)
	if err != nil {
		writeError(response, http.StatusConflict, err.Error())
		return
	}

	taskIDs := make([]string, 0, len(plan.Tasks))
	for _, task := range plan.Tasks {
		taskIDs = append(taskIDs, task.TaskID)
	}
	planEvent, err := domain.NewRunEvent(
		runState.RunID,
		domain.RunEventTypePlanGenerated,
		map[string]any{
			"plan_id":       plan.PlanID,
			"template_name": plan.TemplateName,
		},
	)
	if err != nil {
		handler.logError("build plan event failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to build plan event")
		return
	}
	tasksEvent, err := domain.NewRunEvent(
		runState.RunID,
		domain.RunEventTypeTasksRegistered,
		map[string]any{"task_ids": taskIDs},
	)
	if err != nil {
		handler.logError("build tasks event failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to build tasks event")
		return
	}

	storedPlan, err := handler.dependencies.Store.SavePlanAndRunState(
		request.Context(),
		plan,
		updatedRunState,
		[]domain.RunEventRecord{planEvent, tasksEvent},
	)
	if err != nil {
		handler.logError("save plan failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to save run plan")
		return
	}

	writeJSON(response, http.StatusOK, domain.RunPlanResponse{Item: storedPlan})
}

func (handler Handler) GetLatestPlan(response http.ResponseWriter, request *http.Request) {
	runID := chi.URLParam(request, "run_id")
	if _, ok := handler.getRunState(response, request); !ok {
		return
	}

	plan, err := handler.dependencies.Store.GetLatestRunPlan(request.Context(), runID)
	if err != nil {
		handler.logError("get latest plan failed", err)
		writeError(response, http.StatusNotFound, "Latest plan does not exist for run "+runID)
		return
	}

	writeJSON(response, http.StatusOK, domain.RunPlanResponse{Item: plan})
}

func (handler Handler) AdvanceTurn(response http.ResponseWriter, request *http.Request) {
	runState, ok := handler.getRunState(response, request)
	if !ok {
		return
	}

	events := make([]domain.RunEventRecord, 0)
	if runState.CurrentTaskID == nil {
		nextTask := domain.FindNextReadyTask(runState)
		if nextTask == nil {
			writeError(response, http.StatusConflict, "Run "+runState.RunID+" has no ready task to advance")
			return
		}
		runState = domain.StartTask(runState, nextTask.TaskID)
		taskStartedEvent, err := domain.NewRunEvent(
			runState.RunID,
			domain.RunEventTypeTaskStarted,
			map[string]any{"task_id": nextTask.TaskID},
		)
		if err != nil {
			handler.logError("build task started event failed", err)
			writeError(response, http.StatusInternalServerError, "Failed to build task event")
			return
		}
		events = append(events, taskStartedEvent)
	}

	activeTask := domain.FindActiveTask(runState)
	if activeTask == nil {
		writeError(response, http.StatusConflict, "Run "+runState.RunID+" does not have an active task")
		return
	}

	turnID, err := domain.NewID("turn")
	if err != nil {
		handler.logError("build turn id failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to build turn")
		return
	}
	executionOutcome, err := handler.executeTurn(request.Context(), runState, *activeTask, turnID)
	if err != nil {
		handler.logError("execute turn failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to execute turn")
		return
	}
	turnResult := executionOutcome.Result
	toolCalls := make([]domain.RunToolCallRecord, 0, len(turnResult.PlannedToolCalls))
	llmCalls := make([]domain.LLMCallRecord, 0, 1)
	if executionOutcome.LLMCall != nil {
		llmCalls = append(llmCalls, *executionOutcome.LLMCall)
	}
	toolCallIDs := make([]string, 0, len(turnResult.PlannedToolCalls))
	evidenceIDs := make([]string, 0, len(turnResult.PlannedToolCalls))

	for _, plannedToolCall := range turnResult.PlannedToolCalls {
		toolCall, err := domain.NewToolCallRecord(
			runState.RunID,
			turnID,
			*activeTask,
			plannedToolCall,
		)
		if err != nil {
			handler.logError("build tool call failed", err)
			writeError(response, http.StatusInternalServerError, "Failed to build tool call")
			return
		}
		toolCalls = append(toolCalls, toolCall)
		toolCallIDs = append(toolCallIDs, toolCall.ToolCallID)

		toolEvent, err := domain.NewRunEvent(
			runState.RunID,
			domain.RunEventTypeToolExecuted,
			map[string]any{
				"tool_call_id": toolCall.ToolCallID,
				"tool_name":    toolCall.ToolName,
				"task_id":      activeTask.TaskID,
			},
		)
		if err != nil {
			handler.logError("build tool event failed", err)
			writeError(response, http.StatusInternalServerError, "Failed to build tool event")
			return
		}
		events = append(events, toolEvent)

		evidenceRecord, err := domain.BuildEvidenceFromToolCall(toolCall)
		if err != nil {
			handler.logError("build evidence failed", err)
			writeError(response, http.StatusInternalServerError, "Failed to build evidence")
			return
		}
		runState.Evidence = append(runState.Evidence, evidenceRecord)
		evidenceIDs = append(evidenceIDs, evidenceRecord.EvidenceID)

		evidenceEvent, err := domain.NewRunEvent(
			runState.RunID,
			domain.RunEventTypeEvidenceRecorded,
			map[string]any{"evidence_id": evidenceRecord.EvidenceID},
		)
		if err != nil {
			handler.logError("build evidence event failed", err)
			writeError(response, http.StatusInternalServerError, "Failed to build evidence event")
			return
		}
		events = append(events, evidenceEvent)
	}

	completedTaskID := activeTask.TaskID
	runState = domain.CompleteTask(runState, completedTaskID)
	taskCompletedEvent, err := domain.NewRunEvent(
		runState.RunID,
		domain.RunEventTypeTaskCompleted,
		map[string]any{"task_id": completedTaskID},
	)
	if err != nil {
		handler.logError("build task completed event failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to build task completed event")
		return
	}
	events = append(events, taskCompletedEvent)

	turn := domain.NewTurnRecord(
		turnID,
		runState.RunID,
		*activeTask,
		turnResult,
		toolCallIDs,
		evidenceIDs,
		runState.Status,
	)
	turnEvent, err := domain.NewRunEvent(
		runState.RunID,
		domain.RunEventTypeTurnExecuted,
		map[string]any{
			"turn_id":    turn.TurnID,
			"task_id":    turn.TaskID,
			"agent_name": turn.AgentName,
		},
	)
	if err != nil {
		handler.logError("build turn event failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to build turn event")
		return
	}
	events = append(events, turnEvent)

	storedTurn, storedRunState, err := handler.dependencies.Store.SaveTurnAdvance(
		request.Context(),
		runState,
		turn,
		toolCalls,
		llmCalls,
		events,
	)
	if err != nil {
		handler.logError("save turn advance failed", err)
		writeError(response, http.StatusInternalServerError, "Failed to advance turn")
		return
	}

	writeJSON(
		response,
		http.StatusOK,
		domain.RunTurnAdvanceResponse{Turn: storedTurn, RunState: storedRunState},
	)
}
