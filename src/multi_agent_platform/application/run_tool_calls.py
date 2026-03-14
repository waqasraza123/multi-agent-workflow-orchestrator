from multi_agent_platform.contracts.run_tool_call_views import (
    RunToolCallListResponse,
    RunToolCallResponse,
)
from multi_agent_platform.contracts.run_tool_calls import (
    RunToolCallPage,
    RunToolCallRecord,
)


def build_run_tool_call_response(
    run_tool_call_record: RunToolCallRecord,
) -> RunToolCallResponse:
    return RunToolCallResponse(item=run_tool_call_record)


def build_run_tool_call_list_response(
    run_tool_call_page: RunToolCallPage,
) -> RunToolCallListResponse:
    return RunToolCallListResponse(
        items=run_tool_call_page.items,
        page=run_tool_call_page.page,
    )
