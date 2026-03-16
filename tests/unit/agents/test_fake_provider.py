import pytest

from multi_agent_platform.agents.fake_provider import FakeLlmProvider
from multi_agent_platform.contracts.runs import TaskRecord
from multi_agent_platform.contracts.turn_execution import (
    AgentExecutionProfile,
    ExecutionBackend,
    LlmTurnRequest,
)


def build_request(provider_name: str = "fake") -> LlmTurnRequest:
    return LlmTurnRequest(
        run_id="run_1",
        user_goal="Create a technical delivery plan",
        task=TaskRecord(
            task_id="task_1",
            title="Break work into phases",
            description="Create the task breakdown",
            assigned_agent="planner",
            acceptance_criteria=["Phases are clear"],
        ),
        execution_profile=AgentExecutionProfile(
            agent_name="planner",
            backend=ExecutionBackend.LLM,
            llm_provider_name=provider_name,
            model_name="fake-model",
        ),
        available_tool_names=["goal_analyzer"],
    )


def test_fake_provider_generates_structured_turn_response() -> None:
    provider = FakeLlmProvider()

    response = provider.generate_turn(build_request())

    assert response.provider_name == "fake"
    assert response.model_name == "fake-model"
    assert response.output.planned_tool_calls[0].tool_name == "goal_analyzer"
    assert response.usage.total_tokens > 0
    assert response.raw_response_text is not None


def test_fake_provider_rejects_mismatched_provider_name() -> None:
    provider = FakeLlmProvider()

    with pytest.raises(ValueError):
        provider.generate_turn(build_request(provider_name="other"))
