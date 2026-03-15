from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from multi_agent_platform.contracts.common import generate_identifier, utc_now


class RunOutputRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    output_id: str = Field(default_factory=lambda: generate_identifier("output"))
    run_id: str
    title: str
    summary: str
    key_findings: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)
    tool_call_refs: list[str] = Field(default_factory=list)
    turn_refs: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
