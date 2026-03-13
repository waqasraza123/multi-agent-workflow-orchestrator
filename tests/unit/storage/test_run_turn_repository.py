from multi_agent_platform.contracts.run_turns import (
    RunTurnListQuery,
    RunTurnRecord,
)
from multi_agent_platform.contracts.runs import RunStatus
from multi_agent_platform.storage.run_turn_repository import InMemoryRunTurnRepository


def test_turn_repository_saves_and_lists_turns() -> None:
    repository = InMemoryRunTurnRepository()

    repository.save(
        RunTurnRecord(
            run_id="run_1",
            task_id="task_1",
            agent_name="planner",
            summary="Planner completed the first turn",
            resulting_run_status=RunStatus.EXECUTING,
        )
    )
    repository.save(
        RunTurnRecord(
            run_id="run_1",
            task_id="task_2",
            agent_name="writer",
            summary="Writer completed the second turn",
            resulting_run_status=RunStatus.VERIFYING,
        )
    )

    page = repository.list("run_1", RunTurnListQuery(limit=10, offset=0))

    assert len(page.items) == 2
    assert page.page.total_count == 2
    assert page.page.has_more is False


def test_turn_repository_paginates_turns() -> None:
    repository = InMemoryRunTurnRepository()

    for index in range(3):
        repository.save(
            RunTurnRecord(
                run_id="run_1",
                task_id=f"task_{index}",
                agent_name="planner",
                summary=f"Turn {index}",
                resulting_run_status=RunStatus.EXECUTING,
            )
        )

    page = repository.list("run_1", RunTurnListQuery(limit=1, offset=1))

    assert len(page.items) == 1
    assert page.page.limit == 1
    assert page.page.offset == 1
    assert page.page.total_count == 3
    assert page.page.has_more is True
