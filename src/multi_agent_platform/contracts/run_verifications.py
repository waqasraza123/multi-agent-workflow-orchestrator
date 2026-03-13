from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from multi_agent_platform.contracts.common import generate_identifier, utc_now


class VerificationVerdict(StrEnum):
    PASS = "pass"
    FAIL = "fail"


class VerificationCheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    passed: bool
    message: str


class RunVerificationReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verification_id: str = Field(default_factory=lambda: generate_identifier("verification"))
    run_id: str
    verdict: VerificationVerdict
    created_at: datetime = Field(default_factory=utc_now)
    checks: list[VerificationCheck]
