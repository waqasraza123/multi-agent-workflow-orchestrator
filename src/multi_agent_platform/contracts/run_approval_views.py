from pydantic import BaseModel, ConfigDict

from multi_agent_platform.contracts.run_approvals import ApprovalRecord
from multi_agent_platform.contracts.run_queries import PageInfo


class RunApprovalResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: ApprovalRecord


class RunApprovalListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ApprovalRecord]
    page: PageInfo
