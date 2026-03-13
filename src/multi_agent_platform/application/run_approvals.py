from multi_agent_platform.contracts.run_approval_views import (
    RunApprovalListResponse,
    RunApprovalResponse,
)
from multi_agent_platform.contracts.run_approvals import ApprovalPage, ApprovalRecord


def build_run_approval_response(approval_record: ApprovalRecord) -> RunApprovalResponse:
    return RunApprovalResponse(item=approval_record)


def build_run_approval_list_response(approval_page: ApprovalPage) -> RunApprovalListResponse:
    return RunApprovalListResponse(items=approval_page.items, page=approval_page.page)
