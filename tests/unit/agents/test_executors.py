import pytest

from multi_agent_platform.agents.executors import DeterministicTurnExecutor
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


def test_deterministic_turn_executor_executes_existing_runtime() -> None:
    executor = DeterministicTurnExecutor()

    result = executor.execute_turn(build_run_state(), build_task())

    assert result.planned_tool_calls[0].tool_name == "goal_analyzer"
    assert "Planner reviewed the task scope" in result.summary


def test_deterministic_turn_executor_rejects_llm_profile() -> None:
    executor = DeterministicTurnExecutor()

    with pytest.raises(ValueError):
        executor.execute_turn(
            build_run_state(),
            build_task(),
            AgentExecutionProfile(
                agent_name="planner",
                backend=ExecutionBackend.LLM,
                llm_provider_name="fake",
            ),
        )


def test_deterministic_turn_executor_rejects_profile_for_different_agent() -> None:
    executor = DeterministicTurnExecutor()

    with pytest.raises(ValueError):
        executor.execute_turn(
            build_run_state(),
            build_task(),
            AgentExecutionProfile(agent_name="researcher"),
        )
