from datetime import datetime

from pydantic import BaseModel, ConfigDict

from multi_agent_platform.contracts.run_queries import PageInfo
from multi_agent_platform.contracts.runs import (
    ApprovalPolicy,
    RunConstraints,
    RunStateSnapshot,
    RunStatus,
    WorkflowType,
)


class RunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    workflow_type: WorkflowType
    status: RunStatus
    user_goal: str
    created_at: datetime
    updated_at: datetime
    current_task_id: str | None
    task_count: int
    completed_task_count: int
    evidence_count: int


class RunDetail(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    workflow_type: WorkflowType
    status: RunStatus
    user_goal: str
    created_at: datetime
    updated_at: datetime
    current_task_id: str | None
    final_output_ref: str | None
    failure_summary: str | None
    task_count: int
    completed_task_count: int
    evidence_count: int
    constraints: RunConstraints
    approval_policy: ApprovalPolicy


class RunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: RunDetail


class RunStateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: RunStateSnapshot


class RunListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RunSummary]
    page: PageInfo
