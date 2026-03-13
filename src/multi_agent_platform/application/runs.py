from multi_agent_platform.agents.runtime import execute_deterministic_turn
from multi_agent_platform.application.run_approvals import (
    build_run_approval_list_response,
    build_run_approval_response,
)
from multi_agent_platform.application.run_events import build_run_event_list_response
from multi_agent_platform.application.run_plans import build_run_plan_response
from multi_agent_platform.application.run_turns import (
    build_run_turn_advance_response,
    build_run_turn_list_response,
)
from multi_agent_platform.application.run_verifications import build_run_verification_report
from multi_agent_platform.application.run_views import (
    build_run_list_response,
    build_run_response,
    build_run_state_response,
)
from multi_agent_platform.contracts.run_approval_views import (
    RunApprovalListResponse,
    RunApprovalResponse,
)
from multi_agent_platform.contracts.run_approvals import (
    ApprovalDecision,
    ApprovalDecisionRequest,
    ApprovalListQuery,
    ApprovalRecord,
    ApprovalRequestCreate,
    ApprovalStatus,
)
from multi_agent_platform.contracts.run_commands import (
    EvidenceCreateRequest,
    TaskCompleteRequest,
    TaskRegistrationRequest,
    TaskStartRequest,
)
from multi_agent_platform.contracts.run_event_views import RunEventListResponse
from multi_agent_platform.contracts.run_events import (
    RunEventListQuery,
    RunEventRecord,
    RunEventType,
)
from multi_agent_platform.contracts.run_plan_views import RunPlanResponse
from multi_agent_platform.contracts.run_queries import RunListQuery
from multi_agent_platform.contracts.run_turn_views import (
    RunTurnAdvanceResponse,
    RunTurnListResponse,
)
from multi_agent_platform.contracts.run_turns import (
    RunTurnListQuery,
    RunTurnRecord,
)
from multi_agent_platform.contracts.run_verification_views import RunVerificationResponse
from multi_agent_platform.contracts.run_views import (
    RunListResponse,
    RunResponse,
    RunStateResponse,
)
from multi_agent_platform.contracts.runs import (
    RunCreateRequest,
    RunStateSnapshot,
    TaskRecord,
    TaskStatus,
)
from multi_agent_platform.orchestration.state import (
    StateTransitionError,
    complete_task,
    create_run_state,
    record_evidence,
    register_tasks,
    start_task,
)
from multi_agent_platform.planning.templates import build_run_plan
from multi_agent_platform.storage.run_approval_repository import RunApprovalRepository
from multi_agent_platform.storage.run_event_repository import RunEventRepository
from multi_agent_platform.storage.run_plan_repository import RunPlanRepository
from multi_agent_platform.storage.run_repository import RunRepository
from multi_agent_platform.storage.run_turn_repository import RunTurnRepository
from multi_agent_platform.storage.run_verification_repository import (
    RunVerificationRepository,
)


class ApprovalTransitionError(ValueError):
    pass


class PlanningTransitionError(ValueError):
    pass


class TurnAdvanceError(ValueError):
    pass


class RunService:
    def __init__(
        self,
        run_repository: RunRepository,
        run_event_repository: RunEventRepository,
        run_verification_repository: RunVerificationRepository,
        run_approval_repository: RunApprovalRepository,
        run_plan_repository: RunPlanRepository,
        run_turn_repository: RunTurnRepository,
    ) -> None:
        self._run_repository = run_repository
        self._run_event_repository = run_event_repository
        self._run_verification_repository = run_verification_repository
        self._run_approval_repository = run_approval_repository
        self._run_plan_repository = run_plan_repository
        self._run_turn_repository = run_turn_repository

    def create_run(self, request: RunCreateRequest) -> RunResponse:
        run_state = create_run_state(request)
        created_run_state = self._run_repository.create(run_state)
        self._record_event(
            run_id=created_run_state.run_id,
            event_type=RunEventType.RUN_CREATED,
            payload={
                "workflow_type": created_run_state.workflow_type.value,
                "status": created_run_state.status.value,
            },
        )
        return build_run_response(created_run_state)

    def get_run(self, run_id: str) -> RunResponse:
        run_state = self._run_repository.get(run_id)
        return build_run_response(run_state)

    def get_run_state(self, run_id: str) -> RunStateResponse:
        run_state = self._run_repository.get(run_id)
        return build_run_state_response(run_state)

    def list_runs(self, query: RunListQuery) -> RunListResponse:
        run_state_page = self._run_repository.list(query)
        return build_run_list_response(run_state_page)

    def generate_plan(self, run_id: str) -> RunPlanResponse:
        run_state = self._run_repository.get(run_id)
        if run_state.tasks:
            raise PlanningTransitionError(
                f"Run {run_id} already has registered tasks and cannot be planned again"
            )
        run_plan = build_run_plan(run_state)
        stored_plan = self._run_plan_repository.save(run_plan)
        updated_run_state = register_tasks(
            run_state,
            [planned_task.to_task_record() for planned_task in stored_plan.tasks],
        )
        self._run_repository.update(updated_run_state)
        self._record_event(
            run_id=run_id,
            event_type=RunEventType.PLAN_GENERATED,
            payload={
                "plan_id": stored_plan.plan_id,
                "template_name": stored_plan.template_name,
            },
        )
        self._record_event(
            run_id=run_id,
            event_type=RunEventType.TASKS_REGISTERED,
            payload={"task_ids": [task.task_id for task in stored_plan.tasks]},
        )
        return build_run_plan_response(stored_plan)

    def get_latest_plan(self, run_id: str) -> RunPlanResponse:
        self._run_repository.get(run_id)
        report = self._run_plan_repository.get_latest(run_id)
        return build_run_plan_response(report)

    def advance_turn(self, run_id: str) -> RunTurnAdvanceResponse:
        run_state = self._run_repository.get(run_id)
        if run_state.current_task_id is None:
            next_task = self._find_next_ready_task(run_state)
            if next_task is None:
                raise TurnAdvanceError(f"Run {run_id} has no ready task to advance")
            run_state = start_task(run_state, next_task.task_id)

        active_task = self._find_active_task(run_state)
        if active_task is None:
            raise TurnAdvanceError(f"Run {run_id} does not have an active task")

        turn_result = execute_deterministic_turn(run_state, active_task)
        evidence_ids: list[str] = []

        for evidence_record in turn_result.evidence_records:
            run_state = record_evidence(run_state, evidence_record)
            evidence_ids.append(evidence_record.evidence_id)

        run_state = complete_task(run_state, active_task.task_id)
        stored_run_state = self._run_repository.update(run_state)

        turn_record = self._run_turn_repository.save(
            RunTurnRecord(
                run_id=run_id,
                task_id=active_task.task_id,
                agent_name=active_task.assigned_agent,
                summary=turn_result.summary,
                evidence_ids=evidence_ids,
                resulting_run_status=stored_run_state.status,
            )
        )

        self._record_event(
            run_id=run_id,
            event_type=RunEventType.TURN_EXECUTED,
            payload={
                "turn_id": turn_record.turn_id,
                "task_id": turn_record.task_id,
                "agent_name": turn_record.agent_name,
            },
        )
        return build_run_turn_advance_response(turn_record, stored_run_state)

    def list_turns(
        self,
        run_id: str,
        query: RunTurnListQuery,
    ) -> RunTurnListResponse:
        self._run_repository.get(run_id)
        run_turn_page = self._run_turn_repository.list(run_id, query)
        return build_run_turn_list_response(run_turn_page)

    def list_run_events(
        self,
        run_id: str,
        query: RunEventListQuery,
    ) -> RunEventListResponse:
        self._run_repository.get(run_id)
        run_event_page = self._run_event_repository.list(run_id, query)
        return build_run_event_list_response(run_event_page)

    def request_approval(
        self,
        run_id: str,
        request: ApprovalRequestCreate,
    ) -> RunApprovalResponse:
        self._run_repository.get(run_id)
        approval_record = ApprovalRecord(
            run_id=run_id,
            requested_action=request.requested_action,
            reason=request.reason,
            risk_summary=request.risk_summary,
            proposed_next_step=request.proposed_next_step,
            supporting_evidence_refs=request.supporting_evidence_refs,
        )
        stored_record = self._run_approval_repository.create(approval_record)
        self._record_event(
            run_id=run_id,
            event_type=RunEventType.APPROVAL_REQUESTED,
            payload={
                "approval_id": stored_record.approval_id,
                "status": stored_record.status.value,
            },
        )
        return build_run_approval_response(stored_record)

    def decide_approval(
        self,
        run_id: str,
        approval_id: str,
        request: ApprovalDecisionRequest,
    ) -> RunApprovalResponse:
        self._run_repository.get(run_id)
        approval_record = self._run_approval_repository.get(run_id, approval_id)
        if approval_record.status is not ApprovalStatus.PENDING:
            raise ApprovalTransitionError(f"Approval {approval_id} is no longer pending")
        updated_record = approval_record.model_copy(
            update={
                "status": self._map_decision_to_status(request.decision),
                "reviewer_id": request.reviewer_id,
                "reviewer_note": request.reviewer_note,
                "decided_at": approval_record.requested_at.__class__.now(
                    approval_record.requested_at.tzinfo
                ),
            }
        )
        stored_record = self._run_approval_repository.update(updated_record)
        self._record_event(
            run_id=run_id,
            event_type=RunEventType.APPROVAL_DECIDED,
            payload={
                "approval_id": stored_record.approval_id,
                "decision": request.decision.value,
                "status": stored_record.status.value,
            },
        )
        return build_run_approval_response(stored_record)

    def list_approvals(
        self,
        run_id: str,
        query: ApprovalListQuery,
    ) -> RunApprovalListResponse:
        self._run_repository.get(run_id)
        approval_page = self._run_approval_repository.list(run_id, query)
        return build_run_approval_list_response(approval_page)

    def register_tasks(
        self,
        run_id: str,
        request: TaskRegistrationRequest,
    ) -> RunStateResponse:
        run_state = self._run_repository.get(run_id)
        task_records = request.to_task_records()
        updated_run_state = register_tasks(run_state, task_records)
        stored_run_state = self._run_repository.update(updated_run_state)
        self._record_event(
            run_id=run_id,
            event_type=RunEventType.TASKS_REGISTERED,
            payload={"task_ids": [task.task_id for task in task_records]},
        )
        return build_run_state_response(stored_run_state)

    def start_task(
        self,
        run_id: str,
        request: TaskStartRequest,
    ) -> RunStateResponse:
        run_state = self._run_repository.get(run_id)
        updated_run_state = start_task(run_state, request.task_id)
        stored_run_state = self._run_repository.update(updated_run_state)
        self._record_event(
            run_id=run_id,
            event_type=RunEventType.TASK_STARTED,
            payload={"task_id": request.task_id},
        )
        return build_run_state_response(stored_run_state)

    def complete_task(
        self,
        run_id: str,
        request: TaskCompleteRequest,
    ) -> RunStateResponse:
        run_state = self._run_repository.get(run_id)
        updated_run_state = complete_task(run_state, request.task_id)
        stored_run_state = self._run_repository.update(updated_run_state)
        self._record_event(
            run_id=run_id,
            event_type=RunEventType.TASK_COMPLETED,
            payload={"task_id": request.task_id},
        )
        return build_run_state_response(stored_run_state)

    def record_evidence(
        self,
        run_id: str,
        request: EvidenceCreateRequest,
    ) -> RunStateResponse:
        run_state = self._run_repository.get(run_id)
        updated_run_state = record_evidence(run_state, request.to_evidence_record())
        stored_run_state = self._run_repository.update(updated_run_state)
        self._record_event(
            run_id=run_id,
            event_type=RunEventType.EVIDENCE_RECORDED,
            payload={"evidence_id": request.evidence_id},
        )
        return build_run_state_response(stored_run_state)

    def verify_run(self, run_id: str) -> RunVerificationResponse:
        run_state = self._run_repository.get(run_id)
        report = build_run_verification_report(run_state)
        stored_report = self._run_verification_repository.save(report)
        self._record_event(
            run_id=run_id,
            event_type=RunEventType.VERIFICATION_COMPLETED,
            payload={"verdict": stored_report.verdict.value},
        )
        return RunVerificationResponse(item=stored_report)

    def get_latest_verification(self, run_id: str) -> RunVerificationResponse:
        self._run_repository.get(run_id)
        report = self._run_verification_repository.get_latest(run_id)
        return RunVerificationResponse(item=report)

    def _find_next_ready_task(
        self,
        run_state: RunStateSnapshot,
    ) -> TaskRecord | None:
        for task in run_state.tasks:
            if task.status is TaskStatus.READY:
                return task
        return None

    def _find_active_task(
        self,
        run_state: RunStateSnapshot,
    ) -> TaskRecord | None:
        current_task_id = run_state.current_task_id
        if current_task_id is None:
            return None
        for task in run_state.tasks:
            if task.task_id == current_task_id:
                return task
        return None

    def _record_event(
        self,
        run_id: str,
        event_type: RunEventType,
        payload: dict[str, object],
    ) -> None:
        self._run_event_repository.append(
            RunEventRecord(
                run_id=run_id,
                event_type=event_type,
                payload=payload,
            )
        )

    def _map_decision_to_status(self, decision: ApprovalDecision) -> ApprovalStatus:
        if decision is ApprovalDecision.APPROVE:
            return ApprovalStatus.APPROVED
        if decision is ApprovalDecision.REJECT:
            return ApprovalStatus.REJECTED
        return ApprovalStatus.REVISION_REQUESTED


__all__ = [
    "ApprovalTransitionError",
    "PlanningTransitionError",
    "RunService",
    "StateTransitionError",
    "TurnAdvanceError",
]
