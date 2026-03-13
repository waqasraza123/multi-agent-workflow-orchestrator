from multi_agent_platform.contracts.run_verifications import (
    RunVerificationReport,
    VerificationCheck,
    VerificationVerdict,
)
from multi_agent_platform.contracts.runs import RunStateSnapshot, TaskStatus


def build_run_verification_report(run_state: RunStateSnapshot) -> RunVerificationReport:
    checks = [
        VerificationCheck(
            code="run_has_tasks",
            passed=len(run_state.tasks) > 0,
            message="Run must contain at least one task",
        ),
        VerificationCheck(
            code="no_active_task",
            passed=run_state.current_task_id is None,
            message="Run must not have an active task during verification",
        ),
        VerificationCheck(
            code="all_tasks_completed",
            passed=all(task.status is TaskStatus.COMPLETED for task in run_state.tasks),
            message="All tasks must be completed before verification passes",
        ),
    ]
    verdict = (
        VerificationVerdict.PASS
        if all(check.passed for check in checks)
        else VerificationVerdict.FAIL
    )
    return RunVerificationReport(
        run_id=run_state.run_id,
        verdict=verdict,
        checks=checks,
    )
