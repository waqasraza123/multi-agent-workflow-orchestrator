from pydantic import BaseModel, ConfigDict

from multi_agent_platform.contracts.run_queries import PageInfo
from multi_agent_platform.contracts.run_turns import RunTurnRecord
from multi_agent_platform.contracts.runs import RunStateSnapshot


class RunTurnResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: RunTurnRecord


class RunTurnListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RunTurnRecord]
    page: PageInfo


class RunTurnAdvanceResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    turn: RunTurnRecord
    run_state: RunStateSnapshot
