from pydantic import BaseModel, ConfigDict

from multi_agent_platform.contracts.run_events import RunEventRecord
from multi_agent_platform.contracts.run_queries import PageInfo


class RunEventListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RunEventRecord]
    page: PageInfo
