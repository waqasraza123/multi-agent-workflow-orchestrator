from multi_agent_platform.contracts.runs import RunCreateRequest, RunStateSnapshot
from multi_agent_platform.orchestration.state import create_run_state
from multi_agent_platform.storage.run_repository import RunNotFoundError, RunRepository


class RunService:
    def __init__(self, run_repository: RunRepository) -> None:
        self._run_repository = run_repository

    def create_run(self, request: RunCreateRequest) -> RunStateSnapshot:
        run_state = create_run_state(request)
        return self._run_repository.save(run_state)

    def get_run(self, run_id: str) -> RunStateSnapshot:
        return self._run_repository.get(run_id)

    def get_run_state(self, run_id: str) -> RunStateSnapshot:
        return self._run_repository.get(run_id)

    def list_runs(self) -> list[RunStateSnapshot]:
        return self._run_repository.list()


__all__ = ["RunNotFoundError", "RunService"]
