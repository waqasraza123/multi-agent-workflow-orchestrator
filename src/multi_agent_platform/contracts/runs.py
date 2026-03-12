from datetime import datetime
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from multi_agent_platform.contracts.common import utc_now

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class WorkflowType(StrEnum):
    RESEARCH_REPORT = "research_report"
    TECHNICAL_PLAN = "technical_plan"
    DOCUMENT_ANALYSIS = "document_analysis"
    ASSISTED_ACTION = "assisted_action"


class RunStatus(StrEnum):
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    VERIFYING = "verifying"
    FINALIZING = "finalizing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskStatus(StrEnum):
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    AWAITING_VERIFICATION = "awaiting_verification"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ApprovalMode(StrEnum):
    NEVER = "never"
    ON_HIGH_RISK = "on_high_risk"
    ALWAYS = "always"


class RunConstraints(BaseModel):
    model_config = ConfigDict(extra="forbid")

    max_turns: int | None = Field(default=None, ge=1)
    allow_write_tools: bool = False
    max_tool_calls_per_turn: int = Field(default=5, ge=1)


class ApprovalPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: ApprovalMode = ApprovalMode.ON_HIGH_RISK
    require_human_approval_for_high_risk_tools: bool = True
    minimum_verification_confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class TaskRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: NonEmptyText
    title: NonEmptyText
    description: NonEmptyText
    assigned_agent: NonEmptyText
    status: TaskStatus = TaskStatus.PENDING
    dependency_ids: list[NonEmptyText] = Field(default_factory=list)
    acceptance_criteria: list[NonEmptyText] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    attempt_count: int = Field(default=0, ge=0)


class EvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: NonEmptyText
    source_type: NonEmptyText
    source_ref: NonEmptyText
    summary: NonEmptyText
    collected_by_agent: NonEmptyText
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)


class RunCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_goal: NonEmptyText
    workflow_type: WorkflowType = WorkflowType.TECHNICAL_PLAN
    metadata: dict[str, Any] = Field(default_factory=dict)
    input_file_refs: list[NonEmptyText] = Field(default_factory=list)
    constraints: RunConstraints = Field(default_factory=RunConstraints)
    approval_policy: ApprovalPolicy = Field(default_factory=ApprovalPolicy)


class RunStateSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: NonEmptyText
    workflow_type: WorkflowType
    status: RunStatus
    user_goal: NonEmptyText
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    tasks: list[TaskRecord] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    constraints: RunConstraints = Field(default_factory=RunConstraints)
    approval_policy: ApprovalPolicy = Field(default_factory=ApprovalPolicy)
    current_task_id: NonEmptyText | None = None
    final_output_ref: NonEmptyText | None = None
    failure_summary: NonEmptyText | None = None
