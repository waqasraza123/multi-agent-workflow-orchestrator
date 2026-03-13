from multi_agent_platform.contracts.run_verifications import (
    RunVerificationReport,
    VerificationCheck,
    VerificationVerdict,
)
from multi_agent_platform.storage.run_verification_repository import (
    InMemoryRunVerificationRepository,
    RunVerificationNotFoundError,
)


def test_verification_repository_saves_and_returns_latest_report() -> None:
    repository = InMemoryRunVerificationRepository()

    first_report = repository.save(
        RunVerificationReport(
            run_id="run_1",
            verdict=VerificationVerdict.FAIL,
            checks=[
                VerificationCheck(
                    code="all_tasks_completed",
                    passed=False,
                    message="Tasks are incomplete",
                )
            ],
        )
    )
    second_report = repository.save(
        RunVerificationReport(
            run_id="run_1",
            verdict=VerificationVerdict.PASS,
            checks=[
                VerificationCheck(
                    code="all_tasks_completed",
                    passed=True,
                    message="All tasks are complete",
                )
            ],
        )
    )

    latest_report = repository.get_latest("run_1")

    assert first_report.run_id == "run_1"
    assert latest_report.verification_id == second_report.verification_id
    assert latest_report.verdict is VerificationVerdict.PASS


def test_verification_repository_raises_for_missing_report() -> None:
    repository = InMemoryRunVerificationRepository()

    try:
        repository.get_latest("run_missing")
    except RunVerificationNotFoundError:
        return

    raise AssertionError("Expected RunVerificationNotFoundError for a missing report")
