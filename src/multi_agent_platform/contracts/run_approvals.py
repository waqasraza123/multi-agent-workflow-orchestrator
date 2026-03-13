from datetime import datetime
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from multi_agent_platform.contracts.common import generate_identifier, utc_now
from multi_agent_platform.contracts.run_queries import PageInfo

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class ApprovalDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_REVISION = "request_revision"


class ApprovalRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requested_action: NonEmptyText
    reason: NonEmptyText
    risk_summary: NonEmptyText
    proposed_next_step: NonEmptyText | None = None
    supporting_evidence_refs: list[NonEmptyText] = Field(default_factory=list)


class ApprovalDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    decision: ApprovalDecision
    reviewer_id: NonEmptyText
    reviewer_note: NonEmptyText | None = None


class ApprovalRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approval_id: str = Field(default_factory=lambda: generate_identifier("approval"))
    run_id: str
    requested_action: NonEmptyText
    reason: NonEmptyText
    risk_summary: NonEmptyText
    proposed_next_step: NonEmptyText | None = None
    supporting_evidence_refs: list[NonEmptyText] = Field(default_factory=list)
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime = Field(default_factory=utc_now)
    decided_at: datetime | None = None
    reviewer_id: NonEmptyText | None = None
    reviewer_note: NonEmptyText | None = None


class ApprovalListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    status: ApprovalStatus | None = None


class ApprovalPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ApprovalRecord]
    page: PageInfo
