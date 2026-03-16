import pytest

from multi_agent_platform.agents.fake_provider import FakeLlmProvider
from multi_agent_platform.agents.llm_executor import LlmTurnExecutor
from multi_agent_platform.contracts.runs import (
    RunStateSnapshot,
    RunStatus,
    TaskRecord,
    WorkflowType,
)
from multi_agent_platform.contracts.turn_execution import (
    AgentExecutionProfile,
    ExecutionBackend,
)


def build_run_state() -> RunStateSnapshot:
    return RunStateSnapshot(
        run_id="run_1",
        workflow_type=WorkflowType.TECHNICAL_PLAN,
        status=RunStatus.EXECUTING,
        user_goal="Create a technical delivery plan",
    )


def build_task() -> TaskRecord:
    return TaskRecord(
        task_id="task_1",
        title="Break work into phases",
        description="Create the task breakdown",
        assigned_agent="planner",
        acceptance_criteria=["Phases are clear"],
    )


def build_profile(
    *,
    agent_name: str = "planner",
    backend: ExecutionBackend = ExecutionBackend.LLM,
    provider_name: str = "fake",
) -> AgentExecutionProfile:
    return AgentExecutionProfile(
        agent_name=agent_name,
        backend=backend,
        llm_provider_name=provider_name if backend is ExecutionBackend.LLM else None,
        model_name="fake-model" if backend is ExecutionBackend.LLM else None,
    )


def test_llm_turn_executor_returns_turn_execution_result() -> None:
    executor = LlmTurnExecutor(
        providers={"fake": FakeLlmProvider()},
        available_tool_names=["goal_analyzer"],
    )

    result = executor.execute_turn(
        build_run_state(),
        build_task(),
        build_profile(),
    )

    assert result.planned_tool_calls[0].tool_name == "goal_analyzer"
    assert "Planner reviewed the task scope" in result.summary


def test_llm_turn_executor_returns_structured_response() -> None:
    executor = LlmTurnExecutor(
        providers={"fake": FakeLlmProvider()},
        available_tool_names=["goal_analyzer"],
    )

    response = executor.execute_structured_turn(
        build_run_state(),
        build_task(),
        build_profile(),
    )

    assert response.provider_name == "fake"
    assert response.output.planned_tool_calls[0].tool_name == "goal_analyzer"


def test_llm_turn_executor_rejects_unknown_provider() -> None:
    executor = LlmTurnExecutor(providers={})

    with pytest.raises(ValueError):
        executor.execute_turn(
            build_run_state(),
            build_task(),
            build_profile(),
        )


def test_llm_turn_executor_rejects_deterministic_profile() -> None:
    executor = LlmTurnExecutor(providers={"fake": FakeLlmProvider()})

    with pytest.raises(ValueError):
        executor.execute_turn(
            build_run_state(),
            build_task(),
            AgentExecutionProfile(agent_name="planner"),
        )


def test_llm_turn_executor_rejects_profile_for_different_agent() -> None:
    executor = LlmTurnExecutor(providers={"fake": FakeLlmProvider()})

    with pytest.raises(ValueError):
        executor.execute_turn(
            build_run_state(),
            build_task(),
            build_profile(agent_name="researcher"),
        )
