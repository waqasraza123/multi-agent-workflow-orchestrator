from pydantic import BaseModel, ConfigDict, Field

from multi_agent_platform.contracts.runs import RunStateSnapshot, TaskRecord
from multi_agent_platform.tools.registry import PlannedToolCall


class TurnExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    planned_tool_calls: list[PlannedToolCall] = Field(default_factory=list)


def execute_deterministic_turn(
    run_state: RunStateSnapshot,
    task: TaskRecord,
) -> TurnExecutionResult:
    summary = build_turn_summary(task.assigned_agent, task.title)
    planned_tool_call = build_planned_tool_call(
        agent_name=task.assigned_agent,
        user_goal=run_state.user_goal,
        task_title=task.title,
    )
    return TurnExecutionResult(
        summary=summary,
        planned_tool_calls=[planned_tool_call],
    )


def build_planned_tool_call(
    agent_name: str,
    user_goal: str,
    task_title: str,
) -> PlannedToolCall:
    if agent_name == "planner":
        tool_name = "goal_analyzer"
    elif agent_name == "researcher":
        tool_name = "evidence_lookup"
    elif agent_name == "writer":
        tool_name = "summary_writer"
    elif agent_name == "executor":
        tool_name = "execution_checker"
    else:
        tool_name = "generic_tool"

    return PlannedToolCall(
        tool_name=tool_name,
        tool_input={
            "user_goal": user_goal,
            "task_title": task_title,
            "agent_name": agent_name,
        },
    )


def build_turn_summary(agent_name: str, task_title: str) -> str:
    if agent_name == "planner":
        return (
            f"Planner reviewed the task scope for {task_title} "
            "and prepared the next execution step."
        )
    if agent_name == "researcher":
        return f"Researcher collected and synthesized evidence for {task_title}."
    if agent_name == "writer":
        return f"Writer drafted the structured output for {task_title}."
    if agent_name == "executor":
        return f"Executor prepared the execution outcome for {task_title}."
    return f"Agent completed a deterministic turn for {task_title}."
