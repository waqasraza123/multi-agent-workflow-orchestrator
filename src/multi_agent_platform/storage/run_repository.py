from typing import Protocol

from multi_agent_platform.contracts.run_queries import PageInfo, RunListQuery, RunStatePage
from multi_agent_platform.contracts.runs import RunStateSnapshot


class RunAlreadyExistsError(LookupError):
    pass


class RunNotFoundError(LookupError):
    pass


class RunRepository(Protocol):
    def create(self, run_state: RunStateSnapshot) -> RunStateSnapshot: ...

    def update(self, run_state: RunStateSnapshot) -> RunStateSnapshot: ...

    def get(self, run_id: str) -> RunStateSnapshot: ...

    def list(self, query: RunListQuery) -> RunStatePage: ...


class InMemoryRunRepository:
    def __init__(self) -> None:
        self._run_states: dict[str, RunStateSnapshot] = {}

    def create(self, run_state: RunStateSnapshot) -> RunStateSnapshot:
        if run_state.run_id in self._run_states:
            raise RunAlreadyExistsError(f"Run {run_state.run_id} already exists")
        stored_run_state = run_state.model_copy(deep=True)
        self._run_states[stored_run_state.run_id] = stored_run_state
        return stored_run_state.model_copy(deep=True)

    def update(self, run_state: RunStateSnapshot) -> RunStateSnapshot:
        if run_state.run_id not in self._run_states:
            raise RunNotFoundError(f"Run {run_state.run_id} does not exist")
        stored_run_state = run_state.model_copy(deep=True)
        self._run_states[stored_run_state.run_id] = stored_run_state
        return stored_run_state.model_copy(deep=True)

    def get(self, run_id: str) -> RunStateSnapshot:
        run_state = self._run_states.get(run_id)
        if run_state is None:
            raise RunNotFoundError(f"Run {run_id} does not exist")
        return run_state.model_copy(deep=True)

    def list(self, query: RunListQuery) -> RunStatePage:
        filtered_states = self.filtered_states(query)
        total_count = len(filtered_states)
        start_index = query.offset
        end_index = start_index + query.limit
        paged_states = filtered_states[start_index:end_index]
        return RunStatePage(
            items=[run_state.model_copy(deep=True) for run_state in paged_states],
            page=PageInfo(
                limit=query.limit,
                offset=query.offset,
                total_count=total_count,
                has_more=end_index < total_count,
            ),
        )

    def filtered_states(self, query: RunListQuery) -> list[RunStateSnapshot]:
        run_states = sorted(
            self._run_states.values(),
            key=lambda run_state: (run_state.created_at, run_state.run_id),
            reverse=True,
        )
        if query.status is not None:
            run_states = [
                run_state for run_state in run_states if run_state.status is query.status
            ]
        if query.workflow_type is not None:
            run_states = [
                run_state
                for run_state in run_states
                if run_state.workflow_type is query.workflow_type
            ]
        return run_states
