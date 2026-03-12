import pytest

from multi_agent_platform.contracts.runs import RunCreateRequest
from multi_agent_platform.orchestration.state import create_run_state
from multi_agent_platform.storage.run_repository import InMemoryRunRepository, RunNotFoundError


def test_repository_returns_saved_run() -> None:
    repository = InMemoryRunRepository()
    run_state = create_run_state(RunCreateRequest(user_goal="Inspect repository health"))

    stored_run_state = repository.save(run_state)
    fetched_run_state = repository.get(stored_run_state.run_id)

    assert fetched_run_state.run_id == stored_run_state.run_id
    assert fetched_run_state.user_goal == "Inspect repository health"


def test_repository_lists_newest_runs_first() -> None:
    repository = InMemoryRunRepository()

    older_run = repository.save(create_run_state(RunCreateRequest(user_goal="Older run")))
    newer_run = repository.save(create_run_state(RunCreateRequest(user_goal="Newer run")))

    run_states = repository.list()

    assert [run_state.run_id for run_state in run_states] == [
        newer_run.run_id,
        older_run.run_id,
    ]


def test_repository_raises_for_missing_run() -> None:
    repository = InMemoryRunRepository()

    with pytest.raises(RunNotFoundError):
        repository.get("run_missing")
