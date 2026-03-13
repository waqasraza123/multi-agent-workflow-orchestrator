from datetime import datetime, timezone

from multi_agent_platform.contracts.run_queries import RunListQuery
from multi_agent_platform.contracts.runs import (
    RunCreateRequest,
    RunStateSnapshot,
    RunStatus,
    WorkflowType,
)
from multi_agent_platform.orchestration.state import create_run_state
from multi_agent_platform.storage.run_repository import InMemoryRunRepository, RunNotFoundError


def build_run_state(
    run_id: str,
    user_goal: str,
    *,
    workflow_type: WorkflowType = WorkflowType.TECHNICAL_PLAN,
    status: RunStatus = RunStatus.PLANNING,
    created_at: datetime,
) -> RunStateSnapshot:
    run_state = create_run_state(
        RunCreateRequest(user_goal=user_goal, workflow_type=workflow_type),
        run_id=run_id,
    )
    return run_state.model_copy(
        update={"status": status, "created_at": created_at, "updated_at": created_at}
    )


def test_repository_returns_saved_run() -> None:
    repository = InMemoryRunRepository()
    run_state = build_run_state(
        "run_1",
        "Inspect repository health",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    stored_run_state = repository.create(run_state)
    fetched_run_state = repository.get(stored_run_state.run_id)

    assert fetched_run_state.run_id == stored_run_state.run_id
    assert fetched_run_state.user_goal == "Inspect repository health"


def test_repository_lists_newest_runs_first_with_pagination() -> None:
    repository = InMemoryRunRepository()

    repository.create(
        build_run_state(
            "run_older",
            "Older run",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    )
    repository.create(
        build_run_state(
            "run_newer",
            "Newer run",
            created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
    )
    repository.create(
        build_run_state(
            "run_latest",
            "Latest run",
            created_at=datetime(2026, 1, 3, tzinfo=timezone.utc),
        )
    )

    page = repository.list(RunListQuery(limit=1, offset=1))

    assert [run_state.run_id for run_state in page.items] == ["run_newer"]
    assert page.page.limit == 1
    assert page.page.offset == 1
    assert page.page.total_count == 3
    assert page.page.has_more is True


def test_repository_filters_runs_by_status_and_workflow_type() -> None:
    repository = InMemoryRunRepository()

    repository.create(
        build_run_state(
            "run_1",
            "Planning run",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    )
    repository.create(
        build_run_state(
            "run_2",
            "Completed document analysis",
            workflow_type=WorkflowType.DOCUMENT_ANALYSIS,
            status=RunStatus.COMPLETED,
            created_at=datetime(2026, 1, 2, tzinfo=timezone.utc),
        )
    )

    page = repository.list(
        RunListQuery(
            limit=10,
            offset=0,
            status=RunStatus.COMPLETED,
            workflow_type=WorkflowType.DOCUMENT_ANALYSIS,
        )
    )

    assert [run_state.run_id for run_state in page.items] == ["run_2"]
    assert page.page.total_count == 1
    assert page.page.has_more is False


def test_repository_update_replaces_existing_run() -> None:
    repository = InMemoryRunRepository()
    created_run = repository.create(
        build_run_state(
            "run_1",
            "Updatable run",
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
    )

    updated_run = repository.update(created_run.model_copy(update={"status": RunStatus.COMPLETED}))

    assert updated_run.status is RunStatus.COMPLETED
    assert repository.get("run_1").status is RunStatus.COMPLETED


def test_repository_raises_for_missing_run() -> None:
    repository = InMemoryRunRepository()

    try:
        repository.get("run_missing")
    except RunNotFoundError:
        return

    raise AssertionError("Expected RunNotFoundError for a missing run")
