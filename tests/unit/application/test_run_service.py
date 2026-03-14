from multi_agent_platform.application.runs import (
    ApprovalTransitionError,
    PlanningTransitionError,
    RunService,
    StateTransitionError,
    TurnAdvanceError,
)
from multi_agent_platform.contracts.run_approvals import (
    ApprovalDecision,
    ApprovalDecisionRequest,
    ApprovalListQuery,
    ApprovalRequestCreate,
    ApprovalStatus,
)
from multi_agent_platform.contracts.run_commands import (
    EvidenceCreateRequest,
    TaskCompleteRequest,
    TaskRegistrationItem,
    TaskRegistrationRequest,
    TaskStartRequest,
)
from multi_agent_platform.contracts.run_events import RunEventListQuery, RunEventType
from multi_agent_platform.contracts.run_queries import RunListQuery
from multi_agent_platform.contracts.run_tool_calls import RunToolCallListQuery
from multi_agent_platform.contracts.run_turns import RunTurnListQuery
from multi_agent_platform.contracts.run_verifications import VerificationVerdict
from multi_agent_platform.contracts.runs import (
    RunCreateRequest,
    RunStatus,
    TaskStatus,
    WorkflowType,
)
from multi_agent_platform.storage.run_approval_repository import (
    InMemoryRunApprovalRepository,
)
from multi_agent_platform.storage.run_event_repository import InMemoryRunEventRepository
from multi_agent_platform.storage.run_plan_repository import InMemoryRunPlanRepository
from multi_agent_platform.storage.run_repository import (
    InMemoryRunRepository,
    RunNotFoundError,
)
from multi_agent_platform.storage.run_tool_call_repository import (
    InMemoryRunToolCallRepository,
)
from multi_agent_platform.storage.run_turn_repository import InMemoryRunTurnRepository
from multi_agent_platform.storage.run_verification_repository import (
    InMemoryRunVerificationRepository,
)


def build_run_service() -> RunService:
    return RunService(
        run_repository=InMemoryRunRepository(),
        run_event_repository=InMemoryRunEventRepository(),
        run_verification_repository=InMemoryRunVerificationRepository(),
        run_approval_repository=InMemoryRunApprovalRepository(),
        run_plan_repository=InMemoryRunPlanRepository(),
        run_turn_repository=InMemoryRunTurnRepository(),
        run_tool_call_repository=InMemoryRunToolCallRepository(),
    )


def build_single_task_request() -> TaskRegistrationRequest:
    return TaskRegistrationRequest(
        items=[
            TaskRegistrationItem(
                task_id="task_1",
                title="Review logs",
                description="Review service logs",
                assigned_agent="planner",
                acceptance_criteria=["Logs reviewed"],
            )
        ]
    )


def test_run_service_creates_and_returns_rich_run_detail() -> None:
    run_service = build_run_service()

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
    run_service = build_run_service()

    run_service.create_run(RunCreateRequest(user_goal="First run"))
    run_service.create_run(RunCreateRequest(user_goal="Second run"))

    run_list = run_service.list_runs(RunListQuery(limit=1, offset=0))

    assert len(run_list.items) == 1
    assert run_list.page.limit == 1
    assert run_list.page.offset == 0
    assert run_list.page.total_count == 2
    assert run_list.page.has_more is True


def test_run_service_generates_plan_and_registers_tasks() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(
        RunCreateRequest(
            user_goal="Create a delivery plan",
            workflow_type=WorkflowType.TECHNICAL_PLAN,
        )
    )
    run_id = created_run.item.run_id

    plan_response = run_service.generate_plan(run_id)
    latest_plan = run_service.get_latest_plan(run_id)
    run_state = run_service.get_run_state(run_id)
    event_response = run_service.list_run_events(
        run_id,
        RunEventListQuery(limit=10, offset=0),
    )

    assert plan_response.item.plan_id == latest_plan.item.plan_id
    assert len(plan_response.item.tasks) == 3
    assert len(run_state.item.tasks) == 3
    assert event_response.items[0].event_type is RunEventType.TASKS_REGISTERED
    assert event_response.items[1].event_type is RunEventType.PLAN_GENERATED


def test_run_service_advances_planned_run_through_turns() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(
        RunCreateRequest(
            user_goal="Create a technical delivery plan",
            workflow_type=WorkflowType.TECHNICAL_PLAN,
        )
    )
    run_id = created_run.item.run_id
    run_service.generate_plan(run_id)

    first_turn = run_service.advance_turn(run_id)
    second_turn = run_service.advance_turn(run_id)
    third_turn = run_service.advance_turn(run_id)
    turn_list = run_service.list_turns(run_id, RunTurnListQuery(limit=10, offset=0))
    tool_calls = run_service.list_tool_calls(
        run_id,
        RunToolCallListQuery(limit=10, offset=0),
    )

    assert first_turn.turn.agent_name == "planner"
    assert len(first_turn.turn.tool_call_ids) == 1
    assert second_turn.turn.agent_name == "researcher"
    assert third_turn.turn.agent_name == "writer"
    assert third_turn.run_state.status is RunStatus.VERIFYING
    assert len(third_turn.run_state.evidence) == 3
    assert len(turn_list.items) == 3
    assert tool_calls.page.total_count == 3


def test_run_service_rejects_turn_advance_without_ready_task() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(RunCreateRequest(user_goal="No tasks yet"))

    try:
        run_service.advance_turn(created_run.item.run_id)
    except TurnAdvanceError:
        return

    raise AssertionError("Expected TurnAdvanceError when no ready task exists")


def test_run_service_rejects_planning_when_tasks_already_exist() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(RunCreateRequest(user_goal="Manual planning"))
    run_id = created_run.item.run_id
    run_service.register_tasks(run_id, build_single_task_request())

    try:
        run_service.generate_plan(run_id)
    except PlanningTransitionError:
        return

    raise AssertionError("Expected PlanningTransitionError when planning a run with tasks")


def test_run_service_registers_and_progresses_tasks() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(RunCreateRequest(user_goal="Investigate issue"))
    run_id = created_run.item.run_id

    registration_response = run_service.register_tasks(run_id, build_single_task_request())

    assert [task.status for task in registration_response.item.tasks] == [TaskStatus.READY]

    started_response = run_service.start_task(run_id, TaskStartRequest(task_id="task_1"))
    assert started_response.item.current_task_id == "task_1"

    completed_response = run_service.complete_task(
        run_id,
        TaskCompleteRequest(task_id="task_1"),
    )
    assert [task.status for task in completed_response.item.tasks] == [TaskStatus.COMPLETED]


def test_run_service_records_evidence() -> None:
    run_service = build_run_service()
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


def test_run_service_lists_run_events() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(RunCreateRequest(user_goal="Track event history"))
    run_id = created_run.item.run_id
    run_service.register_tasks(run_id, build_single_task_request())

    response = run_service.list_run_events(run_id, RunEventListQuery(limit=10, offset=0))

    assert len(response.items) == 2
    assert response.items[0].event_type is RunEventType.TASKS_REGISTERED
    assert response.items[1].event_type is RunEventType.RUN_CREATED


def test_run_service_requests_and_decides_approval() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(RunCreateRequest(user_goal="Request approval"))
    run_id = created_run.item.run_id

    approval_response = run_service.request_approval(
        run_id,
        ApprovalRequestCreate(
            requested_action="Send deployment notice",
            reason="External communication is required",
            risk_summary="Incorrect message could confuse users",
            proposed_next_step="Wait for reviewer response",
        ),
    )
    decision_response = run_service.decide_approval(
        run_id,
        approval_response.item.approval_id,
        ApprovalDecisionRequest(
            decision=ApprovalDecision.APPROVE,
            reviewer_id="reviewer_1",
            reviewer_note="Approved for release",
        ),
    )
    approval_list = run_service.list_approvals(
        run_id,
        ApprovalListQuery(limit=10, offset=0, status=ApprovalStatus.APPROVED),
    )
    event_response = run_service.list_run_events(run_id, RunEventListQuery(limit=10, offset=0))

    assert approval_response.item.status is ApprovalStatus.PENDING
    assert decision_response.item.status is ApprovalStatus.APPROVED
    assert len(approval_list.items) == 1
    assert approval_list.items[0].approval_id == approval_response.item.approval_id
    assert event_response.items[0].event_type is RunEventType.APPROVAL_DECIDED


def test_run_service_verifies_completed_run() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(RunCreateRequest(user_goal="Verify readiness"))
    run_id = created_run.item.run_id
    run_service.register_tasks(run_id, build_single_task_request())
    run_service.start_task(run_id, TaskStartRequest(task_id="task_1"))
    run_service.complete_task(run_id, TaskCompleteRequest(task_id="task_1"))

    verification_response = run_service.verify_run(run_id)
    latest_response = run_service.get_latest_verification(run_id)
    event_response = run_service.list_run_events(run_id, RunEventListQuery(limit=10, offset=0))

    assert verification_response.item.verdict is VerificationVerdict.PASS
    assert latest_response.item.verification_id == verification_response.item.verification_id
    assert event_response.items[0].event_type is RunEventType.VERIFICATION_COMPLETED


def test_run_service_fails_verification_for_incomplete_run() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(RunCreateRequest(user_goal="Verify incomplete run"))
    run_id = created_run.item.run_id
    run_service.register_tasks(run_id, build_single_task_request())

    verification_response = run_service.verify_run(run_id)

    assert verification_response.item.verdict is VerificationVerdict.FAIL


def test_run_service_raises_for_missing_run() -> None:
    run_service = build_run_service()

    try:
        run_service.get_run("run_missing")
    except RunNotFoundError:
        return

    raise AssertionError("Expected RunNotFoundError for a missing run")


def test_run_service_raises_for_invalid_transition() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(RunCreateRequest(user_goal="Invalid transition check"))

    try:
        run_service.start_task(created_run.item.run_id, TaskStartRequest(task_id="missing_task"))
    except StateTransitionError:
        return

    raise AssertionError("Expected StateTransitionError for an invalid task start")


def test_run_service_rejects_deciding_non_pending_approval() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(RunCreateRequest(user_goal="Approval transition check"))
    run_id = created_run.item.run_id
    approval_response = run_service.request_approval(
        run_id,
        ApprovalRequestCreate(
            requested_action="Publish summary",
            reason="Public communication is required",
            risk_summary="Incorrect summary could mislead users",
        ),
    )
    run_service.decide_approval(
        run_id,
        approval_response.item.approval_id,
        ApprovalDecisionRequest(
            decision=ApprovalDecision.REJECT,
            reviewer_id="reviewer_1",
        ),
    )

    try:
        run_service.decide_approval(
            run_id,
            approval_response.item.approval_id,
            ApprovalDecisionRequest(
                decision=ApprovalDecision.APPROVE,
                reviewer_id="reviewer_2",
            ),
        )
    except ApprovalTransitionError:
        return

    raise AssertionError("Expected ApprovalTransitionError for a non-pending approval")
