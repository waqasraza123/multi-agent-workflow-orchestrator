from multi_agent_platform.application.runs import RunService
from multi_agent_platform.storage.run_repository import InMemoryRunRepository

_run_service: RunService | None = None


def get_run_service() -> RunService:
    global _run_service
    if _run_service is None:
        _run_service = RunService(InMemoryRunRepository())
    return _run_service


def reset_api_state() -> None:
    global _run_service
    _run_service = None
