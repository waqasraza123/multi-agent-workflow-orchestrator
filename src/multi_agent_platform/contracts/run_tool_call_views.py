from pydantic import BaseModel, ConfigDict

from multi_agent_platform.contracts.run_queries import PageInfo
from multi_agent_platform.contracts.run_tool_calls import RunToolCallRecord


class RunToolCallResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: RunToolCallRecord


class RunToolCallListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RunToolCallRecord]
    page: PageInfo
