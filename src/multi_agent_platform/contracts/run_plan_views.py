from pydantic import BaseModel, ConfigDict

from multi_agent_platform.contracts.run_plans import RunPlanReport


class RunPlanResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: RunPlanReport
