from typing import Protocol

from multi_agent_platform.contracts.run_plans import RunPlanReport


class RunPlanNotFoundError(LookupError):
    pass


class RunPlanRepository(Protocol):
    def save(self, report: RunPlanReport) -> RunPlanReport: ...

    def get_latest(self, run_id: str) -> RunPlanReport: ...


class InMemoryRunPlanRepository:
    def __init__(self) -> None:
        self._reports_by_run_id: dict[str, list[RunPlanReport]] = {}

    def save(self, report: RunPlanReport) -> RunPlanReport:
        stored_report = report.model_copy(deep=True)
        existing = self._reports_by_run_id.setdefault(stored_report.run_id, [])
        existing.append(stored_report)
        return stored_report.model_copy(deep=True)

    def get_latest(self, run_id: str) -> RunPlanReport:
        existing = self._reports_by_run_id.get(run_id, [])
        if not existing:
            raise RunPlanNotFoundError(f"No plan exists for run {run_id}")
        ordered = sorted(
            existing,
            key=lambda report: (report.created_at, report.plan_id),
            reverse=True,
        )
        return ordered[0].model_copy(deep=True)
