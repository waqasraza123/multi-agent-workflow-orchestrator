package httpapi

import (
	"context"

	"github.com/waqasraza123/agent-runway/apps/api-go/internal/contracts"
	"github.com/waqasraza123/agent-runway/apps/api-go/internal/domain"
)

var availableToolNames = []string{
	"goal_analyzer",
	"evidence_lookup",
	"summary_writer",
	"execution_checker",
	"generic_tool",
}

type turnExecutionOutcome struct {
	Result  domain.TurnExecutionResult
	LLMCall *domain.LLMCallRecord
}

func (handler Handler) executeTurn(
	ctx context.Context,
	runState domain.RunStateSnapshot,
	task domain.TaskRecord,
	turnID string,
) (turnExecutionOutcome, error) {
	if handler.dependencies.Settings.ExecutionBackend != "llm" {
		return turnExecutionOutcome{
			Result: domain.ExecuteDeterministicTurn(runState, task),
		}, nil
	}

	workerRequest := contracts.LLMWorkerTurnRequest{
		RunID:    runState.RunID,
		UserGoal: runState.UserGoal,
		Task: contracts.TaskRecord{
			TaskID:             task.TaskID,
			Title:              task.Title,
			Description:        task.Description,
			AssignedAgent:      task.AssignedAgent,
			Status:             task.Status,
			DependencyIDs:      task.DependencyIDs,
			AcceptanceCriteria: task.AcceptanceCriteria,
			RiskLevel:          task.RiskLevel,
			AttemptCount:       task.AttemptCount,
		},
		ExecutionProfile: contracts.AgentExecutionProfile{
			AgentName:       task.AssignedAgent,
			Backend:         contracts.ExecutionBackendLLM,
			LLMProviderName: &handler.dependencies.Settings.LLMProviderName,
			ModelName:       &handler.dependencies.Settings.LLMModelName,
			Temperature:     handler.dependencies.Settings.LLMTemperature,
			MaxOutputTokens: handler.dependencies.Settings.LLMMaxOutputTokens,
			TimeoutSeconds:  handler.dependencies.Settings.LLMTimeoutSeconds,
			MaxRetries:      handler.dependencies.Settings.LLMMaxRetries,
		},
		AvailableToolNames: availableToolNames,
	}

	workerOutcome, err := handler.dependencies.WorkerClient.ExecuteTurn(ctx, workerRequest)
	if err != nil {
		return handler.buildWorkerFallbackOutcome(runState, task, turnID, err.Error())
	}

	turnResult := domain.TurnExecutionResult{
		Summary:          workerOutcome.Output.Summary,
		PlannedToolCalls: mapPlannedToolCalls(workerOutcome.Output.PlannedToolCalls),
	}

	providerName := handler.dependencies.Settings.LLMProviderName
	modelName := handler.dependencies.Settings.LLMModelName
	var finishReason *string
	var latencyMS *int
	var rawResponseText *string
	usage := domain.LLMUsage{}
	responsePayload := map[string]any{
		"fallback_used": workerOutcome.FallbackUsed,
		"attempt_count": workerOutcome.AttemptCount,
	}

	if workerOutcome.LLMResponse != nil {
		providerName = workerOutcome.LLMResponse.ProviderName
		modelName = workerOutcome.LLMResponse.ModelName
		finishReason = workerOutcome.LLMResponse.FinishReason
		latencyMS = workerOutcome.LLMResponse.LatencyMS
		rawResponseText = workerOutcome.LLMResponse.RawResponseText
		usage = domain.LLMUsage{
			InputTokens:      workerOutcome.LLMResponse.Usage.InputTokens,
			OutputTokens:     workerOutcome.LLMResponse.Usage.OutputTokens,
			TotalTokens:      workerOutcome.LLMResponse.Usage.TotalTokens,
			EstimatedCostUSD: workerOutcome.LLMResponse.Usage.EstimatedCostUSD,
		}
		responsePayload["provider_name"] = providerName
		responsePayload["model_name"] = modelName
	}

	llmCall, err := domain.NewLLMCallRecord(
		runState.RunID,
		turnID,
		task,
		providerName,
		modelName,
		domain.StructuredTurnOutput{
			Summary:          workerOutcome.Output.Summary,
			PlannedToolCalls: mapPlannedToolCalls(workerOutcome.Output.PlannedToolCalls),
		},
		usage,
		availableToolNames,
		map[string]any{
			"run_id":               workerRequest.RunID,
			"task_id":              workerRequest.Task.TaskID,
			"agent_name":           workerRequest.ExecutionProfile.AgentName,
			"llm_provider_name":    providerName,
			"model_name":           modelName,
			"available_tool_names": availableToolNames,
		},
		responsePayload,
		finishReason,
		latencyMS,
		workerOutcome.ErrorMessage,
		rawResponseText,
		workerOutcome.AttemptCount,
		workerOutcome.FallbackUsed,
	)
	if err != nil {
		return turnExecutionOutcome{}, err
	}

	return turnExecutionOutcome{
		Result:  turnResult,
		LLMCall: &llmCall,
	}, nil
}

func (handler Handler) buildWorkerFallbackOutcome(
	runState domain.RunStateSnapshot,
	task domain.TaskRecord,
	turnID string,
	errorMessage string,
) (turnExecutionOutcome, error) {
	turnResult := domain.ExecuteDeterministicTurn(runState, task)
	errorMessageRef := errorMessage
	llmCall, err := domain.NewLLMCallRecord(
		runState.RunID,
		turnID,
		task,
		handler.dependencies.Settings.LLMProviderName,
		handler.dependencies.Settings.LLMModelName,
		domain.StructuredTurnOutput{
			Summary:          turnResult.Summary,
			PlannedToolCalls: turnResult.PlannedToolCalls,
		},
		domain.LLMUsage{},
		availableToolNames,
		map[string]any{
			"run_id":               runState.RunID,
			"task_id":              task.TaskID,
			"agent_name":           task.AssignedAgent,
			"llm_provider_name":    handler.dependencies.Settings.LLMProviderName,
			"model_name":           handler.dependencies.Settings.LLMModelName,
			"available_tool_names": availableToolNames,
		},
		map[string]any{
			"fallback_used": true,
			"error_message":  errorMessage,
		},
		nil,
		nil,
		&errorMessageRef,
		nil,
		1,
		true,
	)
	if err != nil {
		return turnExecutionOutcome{}, err
	}
	return turnExecutionOutcome{
		Result:  turnResult,
		LLMCall: &llmCall,
	}, nil
}

func mapPlannedToolCalls(items []contracts.PlannedToolCall) []domain.PlannedToolCall {
	mapped := make([]domain.PlannedToolCall, 0, len(items))
	for _, item := range items {
		mapped = append(mapped, domain.PlannedToolCall{
			ToolName:  item.ToolName,
			ToolInput: item.ToolInput,
		})
	}
	return mapped
}
