from multi_agent_platform.contracts.runs import (
    EvidenceRecord,
    RunCreateRequest,
    RunStatus,
    TaskRecord,
    TaskStatus,
)
from multi_agent_platform.orchestration.state import (
    complete_task,
    create_run_state,
    record_evidence,
    register_tasks,
    start_task,
)


def build_task(
    task_id: str,
    dependency_ids: list[str] | None = None,
) -> TaskRecord:
    return TaskRecord(
        task_id=task_id,
        title=f"Task {task_id}",
        description=f"Complete {task_id}",
        assigned_agent="planner",
        dependency_ids=dependency_ids or [],
        acceptance_criteria=[f"{task_id} is complete"],
    )


def test_register_tasks_marks_dependency_free_tasks_ready() -> None:
    run_state = create_run_state(RunCreateRequest(user_goal="Create a technical plan for rollout"))

    updated_state = register_tasks(
        run_state,
        [
            build_task("task_1"),
            build_task("task_2", dependency_ids=["task_1"]),
        ],
    )

    assert updated_state.status is RunStatus.PLANNING
    assert [task.status for task in updated_state.tasks] == [
        TaskStatus.READY,
        TaskStatus.PENDING,
    ]


def test_task_lifecycle_unlocks_dependent_tasks_and_ends_in_verifying() -> None:
    run_state = create_run_state(RunCreateRequest(user_goal="Investigate a production regression"))
    run_state = register_tasks(
        run_state,
        [
            build_task("task_1"),
            build_task("task_2", dependency_ids=["task_1"]),
        ],
    )

    run_state = start_task(run_state, "task_1")
    assert run_state.current_task_id == "task_1"
    assert run_state.status is RunStatus.EXECUTING

    run_state = complete_task(run_state, "task_1")
    assert run_state.current_task_id is None
    assert [task.status for task in run_state.tasks] == [
        TaskStatus.COMPLETED,
        TaskStatus.READY,
    ]

    run_state = start_task(run_state, "task_2")
    run_state = complete_task(run_state, "task_2")

    assert run_state.status is RunStatus.VERIFYING
    assert all(task.status is TaskStatus.COMPLETED for task in run_state.tasks)


def test_record_evidence_appends_validated_evidence() -> None:
    run_state = create_run_state(RunCreateRequest(user_goal="Analyze incident notes for evidence"))

    updated_state = record_evidence(
        run_state,
        EvidenceRecord(
            evidence_id="evidence_1",
            source_type="document",
            source_ref="incident-notes.md",
            summary="Incident notes confirm the failure started after deployment.",
            collected_by_agent="researcher",
            confidence=0.91,
        ),
    )

    assert len(updated_state.evidence) == 1
    assert updated_state.evidence[0].evidence_id == "evidence_1"
