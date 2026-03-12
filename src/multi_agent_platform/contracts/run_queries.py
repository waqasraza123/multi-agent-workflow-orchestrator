from pydantic import BaseModel, ConfigDict, Field

from multi_agent_platform.contracts.runs import RunStateSnapshot, RunStatus, WorkflowType


class RunListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    status: RunStatus | None = None
    workflow_type: WorkflowType | None = None


class PageInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
    total_count: int = Field(ge=0)
    has_more: bool


class RunStatePage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RunStateSnapshot]
    page: PageInfo
