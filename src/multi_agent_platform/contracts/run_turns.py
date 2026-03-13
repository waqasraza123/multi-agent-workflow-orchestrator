from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from multi_agent_platform.contracts.common import generate_identifier, utc_now
from multi_agent_platform.contracts.run_queries import PageInfo
from multi_agent_platform.contracts.runs import RunStatus


class RunTurnRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn_id: str = Field(default_factory=lambda: generate_identifier("turn"))
    run_id: str
    task_id: str
    agent_name: str
    summary: str
    evidence_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    resulting_run_status: RunStatus


class RunTurnListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class RunTurnPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RunTurnRecord]
    page: PageInfo
