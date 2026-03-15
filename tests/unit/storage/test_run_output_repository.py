from multi_agent_platform.contracts.run_outputs import RunOutputRecord
from multi_agent_platform.storage.run_output_repository import (
    InMemoryRunOutputRepository,
    RunOutputNotFoundError,
)


def test_output_repository_saves_and_returns_latest_output() -> None:
    repository = InMemoryRunOutputRepository()

    first_output = repository.save(
        RunOutputRecord(
            run_id="run_1",
            title="First output",
            summary="First summary",
        )
    )
    second_output = repository.save(
        RunOutputRecord(
            run_id="run_1",
            title="Second output",
            summary="Second summary",
        )
    )

    latest_output = repository.get_latest("run_1")

    assert first_output.run_id == "run_1"
    assert latest_output.output_id == second_output.output_id
    assert latest_output.title == "Second output"


def test_output_repository_raises_for_missing_output() -> None:
    repository = InMemoryRunOutputRepository()

    try:
        repository.get_latest("run_missing")
    except RunOutputNotFoundError:
        return

    raise AssertionError("Expected RunOutputNotFoundError for a missing output")
