from typing import Protocol

from multi_agent_platform.contracts.run_events import (
    RunEventListQuery,
    RunEventPage,
    RunEventRecord,
)
from multi_agent_platform.contracts.run_queries import PageInfo


class RunEventRepository(Protocol):
    def append(self, event_record: RunEventRecord) -> RunEventRecord: ...

    def list(self, run_id: str, query: RunEventListQuery) -> RunEventPage: ...


class InMemoryRunEventRepository:
    def __init__(self) -> None:
        self._events_by_run_id: dict[str, list[RunEventRecord]] = {}

    def append(self, event_record: RunEventRecord) -> RunEventRecord:
        stored_event_record = event_record.model_copy(deep=True)
        existing = self._events_by_run_id.setdefault(stored_event_record.run_id, [])
        existing.append(stored_event_record)
        return stored_event_record.model_copy(deep=True)

    def list(self, run_id: str, query: RunEventListQuery) -> RunEventPage:
        existing = self._events_by_run_id.get(run_id, [])
        ordered = sorted(
            existing,
            key=lambda event_record: (event_record.occurred_at, event_record.event_id),
            reverse=True,
        )
        start_index = query.offset
        end_index = start_index + query.limit
        paged = ordered[start_index:end_index]
        return RunEventPage(
            items=[event_record.model_copy(deep=True) for event_record in paged],
            page=PageInfo(
                limit=query.limit,
                offset=query.offset,
                total_count=len(ordered),
                has_more=end_index < len(ordered),
            ),
        )
