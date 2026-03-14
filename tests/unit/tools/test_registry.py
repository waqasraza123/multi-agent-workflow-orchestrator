from multi_agent_platform.tools.registry import (
    PlannedToolCall,
    execute_planned_tool_call,
)


def test_registry_executes_planned_tool_call() -> None:
    result = execute_planned_tool_call(
        PlannedToolCall(
            tool_name="goal_analyzer",
            tool_input={
                "user_goal": "Create a technical plan",
                "task_title": "Review request scope",
                "agent_name": "planner",
            },
        )
    )

    assert result.tool_name == "goal_analyzer"
    assert result.tool_output["goal_outline"] == "Analyzed goal for Review request scope"
