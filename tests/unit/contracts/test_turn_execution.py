import pytest
from pydantic import ValidationError

from multi_agent_platform.contracts.runs import TaskRecord
from multi_agent_platform.contracts.turn_execution import (
    AgentExecutionProfile,
    ExecutionBackend,
    LlmTurnRequest,
    LlmTurnResponse,
    LlmUsage,
    StructuredTurnOutput,
)
from multi_agent_platform.tools.registry import PlannedToolCall


def build_task() -> TaskRecord:
    return TaskRecord(
        task_id="task_1",
        title="Review logs",
        description="Review service logs",
        assigned_agent="planner",
        acceptance_criteria=["Logs reviewed"],
    )


def test_agent_execution_profile_defaults_to_deterministic() -> None:
    profile = AgentExecutionProfile(agent_name="planner")

    assert profile.backend is ExecutionBackend.DETERMINISTIC
    assert profile.llm_provider_name is None


def test_agent_execution_profile_rejects_llm_settings_for_deterministic() -> None:
    with pytest.raises(ValidationError):
        AgentExecutionProfile(
            agent_name="planner",
            llm_provider_name="fake",
        )


def test_agent_execution_profile_requires_provider_for_llm() -> None:
    with pytest.raises(ValidationError):
        AgentExecutionProfile(
            agent_name="planner",
            backend=ExecutionBackend.LLM,
        )


def test_llm_usage_rejects_total_tokens_below_component_sum() -> None:
    with pytest.raises(ValidationError):
        LlmUsage(
            input_tokens=8,
            output_tokens=5,
            total_tokens=10,
        )


def test_llm_turn_response_preserves_structured_output() -> None:
    request = LlmTurnRequest(
        run_id="run_1",
        user_goal="Investigate deployment issue",
        task=build_task(),
        execution_profile=AgentExecutionProfile(
            agent_name="planner",
            backend=ExecutionBackend.LLM,
            llm_provider_name="fake",
            model_name="fake-model",
            max_output_tokens=256,
            timeout_seconds=30.0,
        ),
        available_tool_names=["goal_analyzer"],
    )
    response = LlmTurnResponse(
        provider_name="fake",
        model_name="fake-model",
        output=StructuredTurnOutput(
            summary="Planner prepared the structured next step.",
            planned_tool_calls=[
                PlannedToolCall(
                    tool_name="goal_analyzer",
                    tool_input={"task_title": request.task.title},
                )
            ],
        ),
        usage=LlmUsage(
            input_tokens=12,
            output_tokens=8,
            total_tokens=20,
        ),
        finish_reason="stop",
        latency_ms=45,
        raw_response_text="structured output",
    )

    assert response.output.summary == "Planner prepared the structured next step."
    assert response.output.planned_tool_calls[0].tool_name == "goal_analyzer"
    assert response.usage.total_tokens == 20
