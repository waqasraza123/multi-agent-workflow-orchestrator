from pydantic import BaseModel, ConfigDict

from multi_agent_platform.contracts.run_outputs import RunOutputRecord


class RunOutputResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: RunOutputRecord
