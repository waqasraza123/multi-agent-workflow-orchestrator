from multi_agent_platform.contracts.run_plan_views import RunPlanResponse
from multi_agent_platform.contracts.run_plans import RunPlanReport


def build_run_plan_response(run_plan_report: RunPlanReport) -> RunPlanResponse:
    return RunPlanResponse(item=run_plan_report)
