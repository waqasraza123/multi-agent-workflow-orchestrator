from multi_agent_platform.contracts.run_events import (
    RunEventListQuery,
    RunEventRecord,
    RunEventType,
)
from multi_agent_platform.storage.run_event_repository import InMemoryRunEventRepository


def test_event_repository_appends_and_lists_events() -> None:
    repository = InMemoryRunEventRepository()

    repository.append(
        RunEventRecord(
            run_id="run_1",
            event_type=RunEventType.RUN_CREATED,
            payload={"status": "planning"},
        )
    )
    repository.append(
        RunEventRecord(
            run_id="run_1",
            event_type=RunEventType.TASK_STARTED,
            payload={"task_id": "task_1"},
        )
    )

    page = repository.list("run_1", RunEventListQuery(limit=10, offset=0))

    assert len(page.items) == 2
    assert page.page.total_count == 2
    assert page.page.has_more is False


def test_event_repository_paginates_events() -> None:
    repository = InMemoryRunEventRepository()

    for index in range(3):
        repository.append(
            RunEventRecord(
                run_id="run_1",
                event_type=RunEventType.RUN_CREATED,
                payload={"index": index},
            )
        )

    page = repository.list("run_1", RunEventListQuery(limit=1, offset=1))

    assert len(page.items) == 1
    assert page.page.limit == 1
    assert page.page.offset == 1
    assert page.page.total_count == 3
    assert page.page.has_more is True
