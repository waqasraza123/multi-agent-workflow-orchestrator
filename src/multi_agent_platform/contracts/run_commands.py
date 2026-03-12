from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from multi_agent_platform.contracts.runs import EvidenceRecord, RiskLevel, TaskRecord

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class TaskRegistrationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: NonEmptyText
    title: NonEmptyText
    description: NonEmptyText
    assigned_agent: NonEmptyText
    dependency_ids: list[NonEmptyText] = Field(default_factory=list)
    acceptance_criteria: list[NonEmptyText] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.MEDIUM

    def to_task_record(self) -> TaskRecord:
        return TaskRecord(
            task_id=self.task_id,
            title=self.title,
            description=self.description,
            assigned_agent=self.assigned_agent,
            dependency_ids=self.dependency_ids,
            acceptance_criteria=self.acceptance_criteria,
            risk_level=self.risk_level,
        )


class TaskRegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[TaskRegistrationItem] = Field(min_length=1)

    def to_task_records(self) -> list[TaskRecord]:
        return [item.to_task_record() for item in self.items]


class TaskStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: NonEmptyText


class TaskCompleteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: NonEmptyText


class EvidenceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: NonEmptyText
    source_type: NonEmptyText
    source_ref: NonEmptyText
    summary: NonEmptyText
    collected_by_agent: NonEmptyText
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)

    def to_evidence_record(self) -> EvidenceRecord:
        return EvidenceRecord(
            evidence_id=self.evidence_id,
            source_type=self.source_type,
            source_ref=self.source_ref,
            summary=self.summary,
            collected_by_agent=self.collected_by_agent,
            confidence=self.confidence,
        )
