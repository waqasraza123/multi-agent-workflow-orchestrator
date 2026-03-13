from typing import Protocol

from multi_agent_platform.contracts.run_queries import PageInfo
from multi_agent_platform.contracts.run_turns import (
    RunTurnListQuery,
    RunTurnPage,
    RunTurnRecord,
)


class RunTurnRepository(Protocol):
    def save(self, record: RunTurnRecord) -> RunTurnRecord: ...

    def list(self, run_id: str, query: RunTurnListQuery) -> RunTurnPage: ...


class InMemoryRunTurnRepository:
    def __init__(self) -> None:
        self._turns_by_run_id: dict[str, list[RunTurnRecord]] = {}

    def save(self, record: RunTurnRecord) -> RunTurnRecord:
        stored_record = record.model_copy(deep=True)
        existing = self._turns_by_run_id.setdefault(stored_record.run_id, [])
        existing.append(stored_record)
        return stored_record.model_copy(deep=True)

    def list(self, run_id: str, query: RunTurnListQuery) -> RunTurnPage:
        existing = self._turns_by_run_id.get(run_id, [])
        ordered = sorted(
            existing,
            key=lambda record: (record.created_at, record.turn_id),
            reverse=True,
        )
        start_index = query.offset
        end_index = start_index + query.limit
        paged = ordered[start_index:end_index]
        return RunTurnPage(
            items=[record.model_copy(deep=True) for record in paged],
            page=PageInfo(
                limit=query.limit,
                offset=query.offset,
                total_count=len(ordered),
                has_more=end_index < len(ordered),
            ),
        )
