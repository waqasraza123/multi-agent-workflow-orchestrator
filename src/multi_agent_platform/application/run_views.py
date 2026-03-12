from multi_agent_platform.contracts.run_queries import RunStatePage
from multi_agent_platform.contracts.run_views import (
    RunDetail,
    RunListResponse,
    RunResponse,
    RunStateResponse,
    RunSummary,
)
from multi_agent_platform.contracts.runs import RunStateSnapshot, TaskStatus


def build_run_summary(run_state: RunStateSnapshot) -> RunSummary:
    return RunSummary(
        run_id=run_state.run_id,
        workflow_type=run_state.workflow_type,
        status=run_state.status,
        user_goal=run_state.user_goal,
        created_at=run_state.created_at,
        updated_at=run_state.updated_at,
        current_task_id=run_state.current_task_id,
        task_count=len(run_state.tasks),
        completed_task_count=completed_task_count(run_state),
        evidence_count=len(run_state.evidence),
    )


def build_run_detail(run_state: RunStateSnapshot) -> RunDetail:
    return RunDetail(
        run_id=run_state.run_id,
        workflow_type=run_state.workflow_type,
        status=run_state.status,
        user_goal=run_state.user_goal,
        created_at=run_state.created_at,
        updated_at=run_state.updated_at,
        current_task_id=run_state.current_task_id,
        final_output_ref=run_state.final_output_ref,
        failure_summary=run_state.failure_summary,
        task_count=len(run_state.tasks),
        completed_task_count=completed_task_count(run_state),
        evidence_count=len(run_state.evidence),
        constraints=run_state.constraints,
        approval_policy=run_state.approval_policy,
    )


def build_run_response(run_state: RunStateSnapshot) -> RunResponse:
    return RunResponse(item=build_run_detail(run_state))


def build_run_state_response(run_state: RunStateSnapshot) -> RunStateResponse:
    return RunStateResponse(item=run_state)


def build_run_list_response(run_state_page: RunStatePage) -> RunListResponse:
    return RunListResponse(
        items=[build_run_summary(run_state) for run_state in run_state_page.items],
        page=run_state_page.page,
    )


def completed_task_count(run_state: RunStateSnapshot) -> int:
    return sum(1 for task in run_state.tasks if task.status is TaskStatus.COMPLETED)
