from typing import Protocol

from multi_agent_platform.contracts.run_outputs import RunOutputRecord


class RunOutputNotFoundError(LookupError):
    pass


class RunOutputRepository(Protocol):
    def save(self, record: RunOutputRecord) -> RunOutputRecord: ...

    def get_latest(self, run_id: str) -> RunOutputRecord: ...


class InMemoryRunOutputRepository:
    def __init__(self) -> None:
        self._outputs_by_run_id: dict[str, list[RunOutputRecord]] = {}

    def save(self, record: RunOutputRecord) -> RunOutputRecord:
        stored_record = record.model_copy(deep=True)
        existing = self._outputs_by_run_id.setdefault(stored_record.run_id, [])
        existing.append(stored_record)
        return stored_record.model_copy(deep=True)

    def get_latest(self, run_id: str) -> RunOutputRecord:
        existing = self._outputs_by_run_id.get(run_id, [])
        if not existing:
            raise RunOutputNotFoundError(f"No output exists for run {run_id}")
        ordered = sorted(
            existing,
            key=lambda record: (record.created_at, record.output_id),
            reverse=True,
        )
        return ordered[0].model_copy(deep=True)
