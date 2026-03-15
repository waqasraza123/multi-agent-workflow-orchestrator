
from multi_agent_platform.application.runs import RunService
from multi_agent_platform.config.settings import get_settings, reset_settings_cache
from multi_agent_platform.storage.db.session import ensure_database_schema, get_session_factory
from multi_agent_platform.storage.run_approval_repository import InMemoryRunApprovalRepository
from multi_agent_platform.storage.run_event_repository import InMemoryRunEventRepository
from multi_agent_platform.storage.run_output_repository import InMemoryRunOutputRepository
from multi_agent_platform.storage.run_plan_repository import InMemoryRunPlanRepository
from multi_agent_platform.storage.run_repository import InMemoryRunRepository
from multi_agent_platform.storage.run_tool_call_repository import (
    InMemoryRunToolCallRepository,
)
from multi_agent_platform.storage.run_turn_repository import InMemoryRunTurnRepository
from multi_agent_platform.storage.run_verification_repository import (
    InMemoryRunVerificationRepository,
)
from multi_agent_platform.storage.sql_repository import (
    SqlAlchemyRunApprovalRepository,
    SqlAlchemyRunEventRepository,
    SqlAlchemyRunOutputRepository,
    SqlAlchemyRunPlanRepository,
    SqlAlchemyRunRepository,
    SqlAlchemyRunToolCallRepository,
    SqlAlchemyRunTurnRepository,
    SqlAlchemyRunVerificationRepository,
)

_run_service: RunService | None = None


def build_memory_run_service() -> RunService:
    return RunService(
        run_repository=InMemoryRunRepository(),
        run_event_repository=InMemoryRunEventRepository(),
        run_verification_repository=InMemoryRunVerificationRepository(),
        run_approval_repository=InMemoryRunApprovalRepository(),
        run_plan_repository=InMemoryRunPlanRepository(),
        run_turn_repository=InMemoryRunTurnRepository(),
        run_tool_call_repository=InMemoryRunToolCallRepository(),
        run_output_repository=InMemoryRunOutputRepository(),
    )


def build_sql_run_service(database_url: str) -> RunService:
    ensure_database_schema(database_url)
    session_factory = get_session_factory(database_url)

    return RunService(
        run_repository=SqlAlchemyRunRepository(session_factory),
        run_event_repository=SqlAlchemyRunEventRepository(session_factory),
        run_verification_repository=SqlAlchemyRunVerificationRepository(session_factory),
        run_approval_repository=SqlAlchemyRunApprovalRepository(session_factory),
        run_plan_repository=SqlAlchemyRunPlanRepository(session_factory),
        run_turn_repository=SqlAlchemyRunTurnRepository(session_factory),
        run_tool_call_repository=SqlAlchemyRunToolCallRepository(session_factory),
        run_output_repository=SqlAlchemyRunOutputRepository(session_factory),
    )


def get_run_service() -> RunService:
    global _run_service
    if _run_service is None:
        settings = get_settings()
        if settings.storage_backend == "sql":
            _run_service = build_sql_run_service(settings.database_url)
        else:
            _run_service = build_memory_run_service()
    return _run_service


def reset_api_state() -> None:
    global _run_service
    _run_service = None
    reset_settings_cache()
