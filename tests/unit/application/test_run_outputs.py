from multi_agent_platform.application.runs import FinalizationError, RunService
from multi_agent_platform.contracts.run_commands import (
    TaskCompleteRequest,
    TaskRegistrationItem,
    TaskRegistrationRequest,
    TaskStartRequest,
)
from multi_agent_platform.contracts.run_events import RunEventListQuery, RunEventType
from multi_agent_platform.contracts.runs import RunCreateRequest, RunStatus, WorkflowType
from multi_agent_platform.storage.run_approval_repository import (
    InMemoryRunApprovalRepository,
)
from multi_agent_platform.storage.run_event_repository import InMemoryRunEventRepository
from multi_agent_platform.storage.run_output_repository import InMemoryRunOutputRepository
from multi_agent_platform.storage.run_plan_repository import InMemoryRunPlanRepository
from multi_agent_platform.storage.run_repository import InMemoryRunRepository
from multi_agent_platform.storage.run_tool_call_repository import (
    InMemoryRunToolCallRepository,
)
from multi_agent_platform.storage.run_turn_repository import InMemoryRunTurnRepository
from multi_agent_platform.storage.run_verification_repository import (
    InMemoryRunVerificationRepository,
    RunVerificationNotFoundError,
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
        run_output_repository=InMemoryRunOutputRepository(),
    )


def test_run_service_finalizes_verified_run() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(
        RunCreateRequest(
            user_goal="Create a technical delivery plan",
            workflow_type=WorkflowType.TECHNICAL_PLAN,
        )
    )
    run_id = created_run.item.run_id

    run_service.generate_plan(run_id)
    run_service.advance_turn(run_id)
    run_service.advance_turn(run_id)
    run_service.advance_turn(run_id)
    run_service.verify_run(run_id)

    output_response = run_service.finalize_run(run_id)
    latest_output = run_service.get_latest_output(run_id)
    run_state = run_service.get_run_state(run_id)
    event_response = run_service.list_run_events(run_id, RunEventListQuery(limit=20, offset=0))

    assert output_response.item.output_id == latest_output.item.output_id
    assert run_state.item.status is RunStatus.COMPLETED
    assert run_state.item.final_output_ref == output_response.item.output_id
    assert len(output_response.item.turn_refs) == 3
    assert len(output_response.item.tool_call_refs) == 3
    assert event_response.items[0].event_type is RunEventType.RUN_FINALIZED


def test_run_service_requires_verification_before_finalize() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(
        RunCreateRequest(
            user_goal="Create a technical delivery plan",
            workflow_type=WorkflowType.TECHNICAL_PLAN,
        )
    )
    run_id = created_run.item.run_id

    run_service.generate_plan(run_id)
    run_service.advance_turn(run_id)
    run_service.advance_turn(run_id)
    run_service.advance_turn(run_id)

    try:
        run_service.finalize_run(run_id)
    except RunVerificationNotFoundError:
        return

    raise AssertionError("Expected RunVerificationNotFoundError before finalization")


def test_run_service_rejects_finalize_when_run_is_not_verifying() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(RunCreateRequest(user_goal="Finalize too early"))

    try:
        run_service.finalize_run(created_run.item.run_id)
    except FinalizationError:
        return

    raise AssertionError("Expected FinalizationError when finalizing too early")


def test_run_service_manual_task_flow_can_finalize_after_pass_verification() -> None:
    run_service = build_run_service()
    created_run = run_service.create_run(RunCreateRequest(user_goal="Manual finalize flow"))
    run_id = created_run.item.run_id

    state_response = run_service.register_tasks(
        run_id,
        TaskRegistrationRequest(
            items=[
                TaskRegistrationItem(
                    task_id="task_1",
                    title="Review logs",
                    description="Review service logs",
                    assigned_agent="planner",
                    acceptance_criteria=["Logs reviewed"],
                )
            ]
        ),
    )
    assert state_response.item.tasks[0].task_id == "task_1"

    run_service.start_task(run_id, TaskStartRequest(task_id="task_1"))
    run_service.complete_task(run_id, TaskCompleteRequest(task_id="task_1"))
    run_service.verify_run(run_id)

    output_response = run_service.finalize_run(run_id)

    assert output_response.item.run_id == run_id
