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
from multi_agent_platform.contracts.run_queries import RunListQuery
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
from multi_agent_platform.storage.run_repository import RunRepository


class RunService:
    def __init__(self, run_repository: RunRepository) -> None:
        self._run_repository = run_repository

    def create_run(self, request: RunCreateRequest) -> RunResponse:
        run_state = create_run_state(request)
        created_run_state = self._run_repository.create(run_state)
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

    def register_tasks(
        self,
        run_id: str,
        request: TaskRegistrationRequest,
    ) -> RunStateResponse:
        run_state = self._run_repository.get(run_id)
        updated_run_state = register_tasks(run_state, request.to_task_records())
        stored_run_state = self._run_repository.update(updated_run_state)
        return build_run_state_response(stored_run_state)

    def start_task(
        self,
        run_id: str,
        request: TaskStartRequest,
    ) -> RunStateResponse:
        run_state = self._run_repository.get(run_id)
        updated_run_state = start_task(run_state, request.task_id)
        stored_run_state = self._run_repository.update(updated_run_state)
        return build_run_state_response(stored_run_state)

    def complete_task(
        self,
        run_id: str,
        request: TaskCompleteRequest,
    ) -> RunStateResponse:
        run_state = self._run_repository.get(run_id)
        updated_run_state = complete_task(run_state, request.task_id)
        stored_run_state = self._run_repository.update(updated_run_state)
        return build_run_state_response(stored_run_state)

    def record_evidence(
        self,
        run_id: str,
        request: EvidenceCreateRequest,
    ) -> RunStateResponse:
        run_state = self._run_repository.get(run_id)
        updated_run_state = record_evidence(run_state, request.to_evidence_record())
        stored_run_state = self._run_repository.update(updated_run_state)
        return build_run_state_response(stored_run_state)


__all__ = ["RunService", "StateTransitionError"]
