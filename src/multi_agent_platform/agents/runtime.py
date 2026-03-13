from pydantic import BaseModel, ConfigDict, Field

from multi_agent_platform.contracts.common import generate_identifier
from multi_agent_platform.contracts.runs import EvidenceRecord, RunStateSnapshot, TaskRecord


class TurnExecutionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    evidence_records: list[EvidenceRecord] = Field(default_factory=list)


def execute_deterministic_turn(
    run_state: RunStateSnapshot,
    task: TaskRecord,
) -> TurnExecutionResult:
    summary = build_turn_summary(task.assigned_agent, task.title)
    evidence_record = EvidenceRecord(
        evidence_id=generate_identifier("evidence"),
        source_type="agent_turn",
        source_ref=f"{run_state.run_id}:{task.task_id}:{task.assigned_agent}",
        summary=f"{summary} Goal: {run_state.user_goal}",
        collected_by_agent=task.assigned_agent,
        confidence=0.84,
    )
    return TurnExecutionResult(summary=summary, evidence_records=[evidence_record])


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
