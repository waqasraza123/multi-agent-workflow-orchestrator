from multi_agent_platform.contracts.run_event_views import RunEventListResponse
from multi_agent_platform.contracts.run_events import RunEventPage


def build_run_event_list_response(run_event_page: RunEventPage) -> RunEventListResponse:
    return RunEventListResponse(items=run_event_page.items, page=run_event_page.page)
