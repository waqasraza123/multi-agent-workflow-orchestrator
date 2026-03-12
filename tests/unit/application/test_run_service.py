from multi_agent_platform.application.runs import RunService, StateTransitionError
from multi_agent_platform.contracts.run_commands import (
    EvidenceCreateRequest,
    TaskCompleteRequest,
    TaskRegistrationRequest,
    TaskRegistrationItem,
    TaskStartRequest,
)
from multi_agent_platform.contracts.run_queries import RunListQuery
from multi_agent_platform.contracts.runs import RunCreateRequest, TaskStatus, WorkflowType
from multi_agent_platform.storage.run_repository import InMemoryRunRepository, RunNotFoundError


def test_run_service_creates_and_returns_rich_run_detail() -> None:
    run_service = RunService(InMemoryRunRepository())

    created_run = run_service.create_run(
        RunCreateRequest(
            user_goal="Review alert history",
            workflow_type=WorkflowType.DOCUMENT_ANALYSIS,
        )
    )
    fetched_run = run_service.get_run(created_run.item.run_id)

    assert created_run.item.run_id == fetched_run.item.run_id
    assert fetched_run.item.user_goal == "Review alert history"
    assert fetched_run.item.workflow_type is WorkflowType.DOCUMENT_ANALYSIS
    assert fetched_run.item.task_count == 0
    assert fetched_run.item.evidence_count == 0


def test_run_service_lists_paginated_runs() -> None:
    run_service = RunService(InMemoryRunRepository())

    run_service.create_run(RunCreateRequest(user_goal="First run"))
    run_service.create_run(RunCreateRequest(user_goal="Second run"))

    run_list = run_service.list_runs(RunListQuery(limit=1, offset=0))

    assert len(run_list.items) == 1
    assert run_list.page.limit == 1
    assert run_list.page.offset == 0
    assert run_list.page.total_count == 2
    assert run_list.page.has_more is True


def test_run_service_registers_and_progresses_tasks() -> None:
    run_service = RunService(InMemoryRunRepository())
    created_run = run_service.create_run(RunCreateRequest(user_goal="Investigate issue"))
    run_id = created_run.item.run_id

    registration_response = run_service.register_tasks(
        run_id,
        TaskRegistrationRequest(
            items=[
                TaskRegistrationItem(
                    task_id="task_1",
                    title="Review logs",
                    description="Review service logs",
                    assigned_agent="planner",
                    acceptance_criteria=["Logs reviewed"],
                ),
                TaskRegistrationItem(
                    task_id="task_2",
                    title="Summarize findings",
                    description="Summarize the investigation",
                    assigned_agent="writer",
                    dependency_ids=["task_1"],
                    acceptance_criteria=["Summary produced"],
                ),
            ]
        ),
    )

    assert [task.status for task in registration_response.item.tasks] == [
        TaskStatus.READY,
        TaskStatus.PENDING,
    ]

    started_response = run_service.start_task(run_id, TaskStartRequest(task_id="task_1"))
    assert started_response.item.current_task_id == "task_1"

    completed_response = run_service.complete_task(
        run_id,
        TaskCompleteRequest(task_id="task_1"),
    )
    assert [task.status for task in completed_response.item.tasks] == [
        TaskStatus.COMPLETED,
        TaskStatus.READY,
    ]


def test_run_service_records_evidence() -> None:
    run_service = RunService(InMemoryRunRepository())
    created_run = run_service.create_run(RunCreateRequest(user_goal="Collect evidence"))

    response = run_service.record_evidence(
        created_run.item.run_id,
        EvidenceCreateRequest(
            evidence_id="evidence_1",
            source_type="document",
            source_ref="incident-notes.md",
            summary="Notes confirm deployment timing",
            collected_by_agent="researcher",
            confidence=0.9,
        ),
    )

    assert len(response.item.evidence) == 1
    assert response.item.evidence[0].evidence_id == "evidence_1"


def test_run_service_raises_for_missing_run() -> None:
    run_service = RunService(InMemoryRunRepository())

    try:
        run_service.get_run("run_missing")
    except RunNotFoundError:
        return

    raise AssertionError("Expected RunNotFoundError for a missing run")


def test_run_service_raises_for_invalid_transition() -> None:
    run_service = RunService(InMemoryRunRepository())
    created_run = run_service.create_run(RunCreateRequest(user_goal="Invalid transition check"))

    try:
        run_service.start_task(created_run.item.run_id, TaskStartRequest(task_id="missing_task"))
    except StateTransitionError:
        return

    raise AssertionError("Expected StateTransitionError for an invalid task start")
