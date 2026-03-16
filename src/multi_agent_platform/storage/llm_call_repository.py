from typing import Protocol

from multi_agent_platform.contracts.llm_calls import (
    LlmCallListQuery,
    LlmCallPage,
    LlmCallRecord,
)
from multi_agent_platform.contracts.run_queries import PageInfo


class LlmCallNotFoundError(LookupError):
    pass


class LlmCallRepository(Protocol):
    def save(self, record: LlmCallRecord) -> LlmCallRecord: ...

    def get(self, run_id: str, llm_call_id: str) -> LlmCallRecord: ...

    def list(self, run_id: str, query: LlmCallListQuery) -> LlmCallPage: ...


class InMemoryLlmCallRepository:
    def __init__(self) -> None:
        self._records_by_run_id: dict[str, list[LlmCallRecord]] = {}

    def save(self, record: LlmCallRecord) -> LlmCallRecord:
        stored_record = record.model_copy(deep=True)
        existing = self._records_by_run_id.setdefault(stored_record.run_id, [])
        existing.append(stored_record)
        return stored_record.model_copy(deep=True)

    def get(self, run_id: str, llm_call_id: str) -> LlmCallRecord:
        existing = self._records_by_run_id.get(run_id, [])
        for record in existing:
            if record.llm_call_id == llm_call_id:
                return record.model_copy(deep=True)
        raise LlmCallNotFoundError(f"LLM call {llm_call_id} does not exist for run {run_id}")

    def list(self, run_id: str, query: LlmCallListQuery) -> LlmCallPage:
        existing = self._records_by_run_id.get(run_id, [])
        ordered = sorted(
            existing,
            key=lambda record: (record.created_at, record.llm_call_id),
            reverse=True,
        )
        start_index = query.offset
        end_index = start_index + query.limit
        paged = ordered[start_index:end_index]
        return LlmCallPage(
            items=[record.model_copy(deep=True) for record in paged],
            page=PageInfo(
                limit=query.limit,
                offset=query.offset,
                total_count=len(ordered),
                has_more=end_index < len(ordered),
            ),
        )
