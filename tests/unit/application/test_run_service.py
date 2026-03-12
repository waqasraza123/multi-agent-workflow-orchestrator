import pytest

from multi_agent_platform.application.runs import RunService
from multi_agent_platform.contracts.runs import RunCreateRequest
from multi_agent_platform.storage.run_repository import InMemoryRunRepository, RunNotFoundError


def test_run_service_creates_and_returns_run() -> None:
    run_service = RunService(InMemoryRunRepository())

    created_run = run_service.create_run(RunCreateRequest(user_goal="Review alert history"))
    fetched_run = run_service.get_run(created_run.run_id)

    assert created_run.run_id == fetched_run.run_id
    assert fetched_run.user_goal == "Review alert history"


def test_run_service_raises_for_missing_run() -> None:
    run_service = RunService(InMemoryRunRepository())

    with pytest.raises(RunNotFoundError):
        run_service.get_run("run_missing")
