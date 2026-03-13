from pydantic import BaseModel, ConfigDict

from multi_agent_platform.contracts.run_verifications import RunVerificationReport


class RunVerificationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    item: RunVerificationReport
