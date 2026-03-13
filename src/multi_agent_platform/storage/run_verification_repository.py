from typing import Protocol

from multi_agent_platform.contracts.run_verifications import RunVerificationReport


class RunVerificationNotFoundError(LookupError):
    pass


class RunVerificationRepository(Protocol):
    def save(self, report: RunVerificationReport) -> RunVerificationReport: ...

    def get_latest(self, run_id: str) -> RunVerificationReport: ...


class InMemoryRunVerificationRepository:
    def __init__(self) -> None:
        self._reports_by_run_id: dict[str, list[RunVerificationReport]] = {}

    def save(self, report: RunVerificationReport) -> RunVerificationReport:
        stored_report = report.model_copy(deep=True)
        existing = self._reports_by_run_id.setdefault(stored_report.run_id, [])
        existing.append(stored_report)
        return stored_report.model_copy(deep=True)

    def get_latest(self, run_id: str) -> RunVerificationReport:
        existing = self._reports_by_run_id.get(run_id, [])
        if not existing:
            raise RunVerificationNotFoundError(f"No verification report exists for run {run_id}")
        ordered = sorted(
            existing,
            key=lambda report: (report.created_at, report.verification_id),
            reverse=True,
        )
        return ordered[0].model_copy(deep=True)
