from typing import Protocol

from multi_agent_platform.contracts.runs import RunStateSnapshot


class RunNotFoundError(LookupError):
    pass


class RunRepository(Protocol):
    def save(self, run_state: RunStateSnapshot) -> RunStateSnapshot: ...
    def get(self, run_id: str) -> RunStateSnapshot: ...
    def list(self) -> list[RunStateSnapshot]: ...


class InMemoryRunRepository:
    def __init__(self) -> None:
        self._run_states: dict[str, RunStateSnapshot] = {}

    def save(self, run_state: RunStateSnapshot) -> RunStateSnapshot:
        stored_run_state = run_state.model_copy(deep=True)
        self._run_states[stored_run_state.run_id] = stored_run_state
        return stored_run_state.model_copy(deep=True)

    def get(self, run_id: str) -> RunStateSnapshot:
        run_state = self._run_states.get(run_id)
        if run_state is None:
            raise RunNotFoundError(f"Run {run_id} does not exist")
        return run_state.model_copy(deep=True)

    def list(self) -> list[RunStateSnapshot]:
        run_states = list(self._run_states.values())
        run_states.sort(key=lambda run_state: run_state.created_at, reverse=True)
        return [run_state.model_copy(deep=True) for run_state in run_states]
