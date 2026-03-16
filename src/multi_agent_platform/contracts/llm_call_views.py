from pydantic import BaseModel, ConfigDict

from multi_agent_platform.contracts.llm_calls import LlmCallRecord
from multi_agent_platform.contracts.run_queries import PageInfo


class LlmCallResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: LlmCallRecord


class LlmCallListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[LlmCallRecord]
    page: PageInfo
