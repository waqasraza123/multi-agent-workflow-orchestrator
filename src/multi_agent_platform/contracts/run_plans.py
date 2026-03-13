from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from multi_agent_platform.contracts.common import generate_identifier, utc_now
from multi_agent_platform.contracts.runs import TaskRecord, WorkflowType

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class PlannedTask(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: NonEmptyText
    title: NonEmptyText
    description: NonEmptyText
    assigned_agent: NonEmptyText
    dependency_ids: list[NonEmptyText] = Field(default_factory=list)
    acceptance_criteria: list[NonEmptyText] = Field(default_factory=list)

    def to_task_record(self) -> TaskRecord:
        return TaskRecord(
            task_id=self.task_id,
            title=self.title,
            description=self.description,
            assigned_agent=self.assigned_agent,
            dependency_ids=self.dependency_ids,
            acceptance_criteria=self.acceptance_criteria,
        )


class RunPlanReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str = Field(default_factory=lambda: generate_identifier("plan"))
    run_id: str
    workflow_type: WorkflowType
    created_at: datetime = Field(default_factory=utc_now)
    template_name: NonEmptyText
    summary: NonEmptyText
    tasks: list[PlannedTask]
