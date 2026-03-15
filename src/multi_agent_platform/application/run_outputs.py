from multi_agent_platform.contracts.run_output_views import RunOutputResponse
from multi_agent_platform.contracts.run_outputs import RunOutputRecord


def build_run_output_response(run_output_record: RunOutputRecord) -> RunOutputResponse:
    return RunOutputResponse(item=run_output_record)
