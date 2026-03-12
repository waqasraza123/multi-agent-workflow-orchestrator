import pytest
from pydantic import ValidationError

from multi_agent_platform.contracts.runs import RunCreateRequest, WorkflowType


def test_run_create_request_rejects_blank_user_goal() -> None:
    with pytest.raises(ValidationError):
        RunCreateRequest(user_goal="   ")


def test_run_create_request_uses_expected_defaults() -> None:
    request = RunCreateRequest(user_goal="Investigate failed workflow execution")

    assert request.user_goal == "Investigate failed workflow execution"
    assert request.workflow_type is WorkflowType.TECHNICAL_PLAN
    assert request.constraints.allow_write_tools is False
    assert request.approval_policy.minimum_verification_confidence == 0.8
