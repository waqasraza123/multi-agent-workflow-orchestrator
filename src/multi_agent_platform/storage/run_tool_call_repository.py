from typing import Protocol

from multi_agent_platform.contracts.run_queries import PageInfo
from multi_agent_platform.contracts.run_tool_calls import (
    RunToolCallListQuery,
    RunToolCallPage,
    RunToolCallRecord,
)


class RunToolCallRepository(Protocol):
    def save(self, record: RunToolCallRecord) -> RunToolCallRecord: ...

    def list(self, run_id: str, query: RunToolCallListQuery) -> RunToolCallPage: ...


class InMemoryRunToolCallRepository:
    def __init__(self) -> None:
        self._tool_calls_by_run_id: dict[str, list[RunToolCallRecord]] = {}

    def save(self, record: RunToolCallRecord) -> RunToolCallRecord:
        stored_record = record.model_copy(deep=True)
        existing = self._tool_calls_by_run_id.setdefault(stored_record.run_id, [])
        existing.append(stored_record)
        return stored_record.model_copy(deep=True)

    def list(self, run_id: str, query: RunToolCallListQuery) -> RunToolCallPage:
        existing = self._tool_calls_by_run_id.get(run_id, [])
        ordered = sorted(
            existing,
            key=lambda record: (record.created_at, record.tool_call_id),
            reverse=True,
        )
        start_index = query.offset
        end_index = start_index + query.limit
        paged = ordered[start_index:end_index]
        return RunToolCallPage(
            items=[record.model_copy(deep=True) for record in paged],
            page=PageInfo(
                limit=query.limit,
                offset=query.offset,
                total_count=len(ordered),
                has_more=end_index < len(ordered),
            ),
        )
