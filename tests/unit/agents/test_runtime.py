from multi_agent_platform.agents.runtime import execute_deterministic_turn
from multi_agent_platform.contracts.runs import RunCreateRequest, TaskRecord
from multi_agent_platform.orchestration.state import create_run_state


def test_runtime_executes_deterministic_turn_and_plans_tool_call() -> None:
    run_state = create_run_state(
        RunCreateRequest(user_goal="Create a technical plan"),
        run_id="run_1",
    )
    task = TaskRecord(
        task_id="task_1",
        title="Review scope",
        description="Review the scope",
        assigned_agent="planner",
        acceptance_criteria=["Scope reviewed"],
    )

    result = execute_deterministic_turn(run_state, task)

    assert result.summary == (
        "Planner reviewed the task scope for Review scope and prepared the next execution step."
    )
    assert len(result.planned_tool_calls) == 1
    assert result.planned_tool_calls[0].tool_name == "goal_analyzer"
