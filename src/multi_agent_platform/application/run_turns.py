from multi_agent_platform.contracts.run_turn_views import (
    RunTurnAdvanceResponse,
    RunTurnListResponse,
    RunTurnResponse,
)
from multi_agent_platform.contracts.run_turns import RunTurnPage, RunTurnRecord
from multi_agent_platform.contracts.runs import RunStateSnapshot


def build_run_turn_response(run_turn_record: RunTurnRecord) -> RunTurnResponse:
    return RunTurnResponse(item=run_turn_record)


def build_run_turn_list_response(run_turn_page: RunTurnPage) -> RunTurnListResponse:
    return RunTurnListResponse(items=run_turn_page.items, page=run_turn_page.page)


def build_run_turn_advance_response(
    run_turn_record: RunTurnRecord,
    run_state: RunStateSnapshot,
) -> RunTurnAdvanceResponse:
    return RunTurnAdvanceResponse(turn=run_turn_record, run_state=run_state)
