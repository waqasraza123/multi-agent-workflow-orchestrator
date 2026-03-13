from multi_agent_platform.application.run_events import build_run_event_list_response
from multi_agent_platform.application.run_verifications import build_run_verification_report
from multi_agent_platform.application.run_views import (
    build_run_list_response,
    build_run_response,
    build_run_state_response,
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
from multi_agent_platform.contracts.run_queries import RunListQuery
from multi_agent_platform.contracts.run_verification_views import RunVerificationResponse
from multi_agent_platform.contracts.run_views import RunListResponse, RunResponse, RunStateResponse
from multi_agent_platform.contracts.runs import RunCreateRequest
from multi_agent_platform.orchestration.state import (
    StateTransitionError,
    complete_task,
    create_run_state,
    record_evidence,
    register_tasks,
    start_task,
)
from multi_agent_platform.storage.run_event_repository import RunEventRepository
from multi_agent_platform.storage.run_repository import RunRepository
from multi_agent_platform.storage.run_verification_repository import (
    RunVerificationRepository,
)


class RunService:
    def __init__(
        self,
        run_repository: RunRepository,
        run_event_repository: RunEventRepository,
        run_verification_repository: RunVerificationRepository,
    ) -> None:
        self._run_repository = run_repository
        self._run_event_repository = run_event_repository
        self._run_verification_repository = run_verification_repository

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

    def list_run_events(
        self,
        run_id: str,
        query: RunEventListQuery,
    ) -> RunEventListResponse:
        self._run_repository.get(run_id)
        run_event_page = self._run_event_repository.list(run_id, query)
        return build_run_event_list_response(run_event_page)

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


__all__ = ["RunService", "StateTransitionError"]
