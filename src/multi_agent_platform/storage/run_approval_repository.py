from typing import Protocol

from multi_agent_platform.contracts.run_approvals import (
    ApprovalListQuery,
    ApprovalPage,
    ApprovalRecord,
)
from multi_agent_platform.contracts.run_queries import PageInfo


class RunApprovalNotFoundError(LookupError):
    pass


class RunApprovalRepository(Protocol):
    def create(self, approval_record: ApprovalRecord) -> ApprovalRecord: ...

    def update(self, approval_record: ApprovalRecord) -> ApprovalRecord: ...

    def get(self, run_id: str, approval_id: str) -> ApprovalRecord: ...

    def list(self, run_id: str, query: ApprovalListQuery) -> ApprovalPage: ...


class InMemoryRunApprovalRepository:
    def __init__(self) -> None:
        self._records_by_run_id: dict[str, dict[str, ApprovalRecord]] = {}

    def create(self, approval_record: ApprovalRecord) -> ApprovalRecord:
        run_records = self._records_by_run_id.setdefault(approval_record.run_id, {})
        stored_record = approval_record.model_copy(deep=True)
        run_records[stored_record.approval_id] = stored_record
        return stored_record.model_copy(deep=True)

    def update(self, approval_record: ApprovalRecord) -> ApprovalRecord:
        run_records = self._records_by_run_id.get(approval_record.run_id, {})
        if approval_record.approval_id not in run_records:
            raise RunApprovalNotFoundError(
                "Approval "
                f"{approval_record.approval_id} does not exist for run "
                f"{approval_record.run_id}"
            )
        stored_record = approval_record.model_copy(deep=True)
        run_records[stored_record.approval_id] = stored_record
        return stored_record.model_copy(deep=True)

    def get(self, run_id: str, approval_id: str) -> ApprovalRecord:
        run_records = self._records_by_run_id.get(run_id, {})
        record = run_records.get(approval_id)
        if record is None:
            raise RunApprovalNotFoundError(
                f"Approval {approval_id} does not exist for run {run_id}"
            )
        return record.model_copy(deep=True)

    def list(self, run_id: str, query: ApprovalListQuery) -> ApprovalPage:
        run_records = list(self._records_by_run_id.get(run_id, {}).values())
        if query.status is not None:
            run_records = [record for record in run_records if record.status is query.status]
        ordered = sorted(
            run_records,
            key=lambda record: (record.requested_at, record.approval_id),
            reverse=True,
        )
        start_index = query.offset
        end_index = start_index + query.limit
        paged = ordered[start_index:end_index]
        return ApprovalPage(
            items=[record.model_copy(deep=True) for record in paged],
            page=PageInfo(
                limit=query.limit,
                offset=query.offset,
                total_count=len(ordered),
                has_more=end_index < len(ordered),
            ),
        )
