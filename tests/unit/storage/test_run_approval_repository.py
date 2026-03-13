from multi_agent_platform.contracts.run_approvals import (
    ApprovalListQuery,
    ApprovalRecord,
    ApprovalStatus,
)
from multi_agent_platform.storage.run_approval_repository import (
    InMemoryRunApprovalRepository,
    RunApprovalNotFoundError,
)


def test_approval_repository_creates_and_lists_records() -> None:
    repository = InMemoryRunApprovalRepository()

    repository.create(
        ApprovalRecord(
            run_id="run_1",
            requested_action="Send deployment notice",
            reason="External communication is required",
            risk_summary="Incorrect notice could confuse users",
        )
    )
    repository.create(
        ApprovalRecord(
            run_id="run_1",
            requested_action="Publish summary",
            reason="Public statement is required",
            risk_summary="Incorrect public statement could cause confusion",
            status=ApprovalStatus.APPROVED,
        )
    )

    page = repository.list(
        "run_1", ApprovalListQuery(limit=10, offset=0, status=ApprovalStatus.PENDING)
    )

    assert len(page.items) == 1
    assert page.items[0].status is ApprovalStatus.PENDING
    assert page.page.total_count == 1


def test_approval_repository_updates_record() -> None:
    repository = InMemoryRunApprovalRepository()
    created_record = repository.create(
        ApprovalRecord(
            run_id="run_1",
            requested_action="Notify customer",
            reason="Customer message is required",
            risk_summary="Incorrect customer message could escalate the issue",
        )
    )

    updated_record = repository.update(
        created_record.model_copy(update={"status": ApprovalStatus.REJECTED})
    )

    assert updated_record.status is ApprovalStatus.REJECTED
    assert repository.get("run_1", created_record.approval_id).status is ApprovalStatus.REJECTED


def test_approval_repository_raises_for_missing_record() -> None:
    repository = InMemoryRunApprovalRepository()

    try:
        repository.get("run_1", "approval_missing")
    except RunApprovalNotFoundError:
        return

    raise AssertionError("Expected RunApprovalNotFoundError for a missing approval")
