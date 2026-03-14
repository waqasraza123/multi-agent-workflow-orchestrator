from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from multi_agent_platform.contracts.common import generate_identifier, utc_now
from multi_agent_platform.contracts.run_queries import PageInfo


class RunToolCallRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tool_call_id: str = Field(default_factory=lambda: generate_identifier("tool"))
    run_id: str
    turn_id: str
    task_id: str
    agent_name: str
    tool_name: str
    tool_input: dict[str, str]
    tool_output: dict[str, str]
    created_at: datetime = Field(default_factory=utc_now)


class RunToolCallListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class RunToolCallPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RunToolCallRecord]
    page: PageInfo
