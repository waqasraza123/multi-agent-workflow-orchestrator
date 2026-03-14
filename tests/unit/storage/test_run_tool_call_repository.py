from multi_agent_platform.contracts.run_tool_calls import (
    RunToolCallListQuery,
    RunToolCallRecord,
)
from multi_agent_platform.storage.run_tool_call_repository import (
    InMemoryRunToolCallRepository,
)


def test_tool_call_repository_saves_and_lists_tool_calls() -> None:
    repository = InMemoryRunToolCallRepository()

    repository.save(
        RunToolCallRecord(
            run_id="run_1",
            turn_id="turn_1",
            task_id="task_1",
            agent_name="planner",
            tool_name="goal_analyzer",
            tool_input={"task_title": "Review scope"},
            tool_output={"goal_outline": "Analyzed scope"},
        )
    )
    repository.save(
        RunToolCallRecord(
            run_id="run_1",
            turn_id="turn_2",
            task_id="task_2",
            agent_name="writer",
            tool_name="summary_writer",
            tool_input={"task_title": "Write summary"},
            tool_output={"draft_summary": "Prepared summary"},
        )
    )

    page = repository.list("run_1", RunToolCallListQuery(limit=10, offset=0))

    assert len(page.items) == 2
    assert page.page.total_count == 2
    assert page.page.has_more is False
