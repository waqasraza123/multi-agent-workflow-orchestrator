from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from multi_agent_platform.contracts.common import generate_identifier, utc_now
from multi_agent_platform.contracts.run_queries import PageInfo


class RunEventType(StrEnum):
    RUN_CREATED = "run_created"
    TASKS_REGISTERED = "tasks_registered"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    EVIDENCE_RECORDED = "evidence_recorded"
    VERIFICATION_COMPLETED = "verification_completed"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_DECIDED = "approval_decided"
    PLAN_GENERATED = "plan_generated"
    TURN_EXECUTED = "turn_executed"
    TOOL_EXECUTED = "tool_executed"


class RunEventRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(default_factory=lambda: generate_identifier("event"))
    run_id: str
    event_type: RunEventType
    occurred_at: datetime = Field(default_factory=utc_now)
    payload: dict[str, Any] = Field(default_factory=dict)


class RunEventListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class RunEventPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RunEventRecord]
    page: PageInfo
