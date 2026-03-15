from collections.abc import Callable
from typing import TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from multi_agent_platform.contracts.run_approvals import (
    ApprovalListQuery,
    ApprovalPage,
    ApprovalRecord,
)
from multi_agent_platform.contracts.run_events import (
    RunEventListQuery,
    RunEventPage,
    RunEventRecord,
)
from multi_agent_platform.contracts.run_outputs import RunOutputRecord
from multi_agent_platform.contracts.run_plans import RunPlanReport
from multi_agent_platform.contracts.run_queries import PageInfo, RunListQuery, RunStatePage
from multi_agent_platform.contracts.run_tool_calls import (
    RunToolCallListQuery,
    RunToolCallPage,
    RunToolCallRecord,
)
from multi_agent_platform.contracts.run_turns import (
    RunTurnListQuery,
    RunTurnPage,
    RunTurnRecord,
)
from multi_agent_platform.contracts.run_verifications import RunVerificationReport
from multi_agent_platform.contracts.runs import RunStateSnapshot
from multi_agent_platform.storage.db.models import (
    RunApprovalRow,
    RunEventRow,
    RunOutputRow,
    RunPlanRow,
    RunStateRow,
    RunToolCallRow,
    RunTurnRow,
    RunVerificationRow,
)
from multi_agent_platform.storage.run_approval_repository import RunApprovalNotFoundError
from multi_agent_platform.storage.run_output_repository import RunOutputNotFoundError
from multi_agent_platform.storage.run_plan_repository import RunPlanNotFoundError
from multi_agent_platform.storage.run_repository import RunAlreadyExistsError, RunNotFoundError
from multi_agent_platform.storage.run_verification_repository import (
    RunVerificationNotFoundError,
)

ModelType = TypeVar("ModelType", bound=BaseModel)


def _serialize_model(model: BaseModel) -> str:
    return model.model_dump_json()


def _deserialize_model(model_type: type[ModelType], payload: str) -> ModelType:
    return model_type.model_validate_json(payload)


def _build_page_info(total_count: int, limit: int, offset: int) -> PageInfo:
    return PageInfo(
        limit=limit,
        offset=offset,
        total_count=total_count,
        has_more=offset + limit < total_count,
    )


class SqlAlchemyRunRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def create(self, run_state: RunStateSnapshot) -> RunStateSnapshot:
        with self._session_factory() as session:
            existing_row = session.get(RunStateRow, run_state.run_id)
            if existing_row is not None:
                raise RunAlreadyExistsError(f"Run {run_state.run_id} already exists")
            session.add(
                RunStateRow(
                    run_id=run_state.run_id,
                    workflow_type=run_state.workflow_type.value,
                    status=run_state.status.value,
                    created_at=run_state.created_at,
                    updated_at=run_state.updated_at,
                    payload=_serialize_model(run_state),
                )
            )
            session.commit()
        return run_state.model_copy(deep=True)

    def update(self, run_state: RunStateSnapshot) -> RunStateSnapshot:
        with self._session_factory() as session:
            row = session.get(RunStateRow, run_state.run_id)
            if row is None:
                raise RunNotFoundError(f"Run {run_state.run_id} does not exist")
            row.workflow_type = run_state.workflow_type.value
            row.status = run_state.status.value
            row.created_at = run_state.created_at
            row.updated_at = run_state.updated_at
            row.payload = _serialize_model(run_state)
            session.commit()
        return run_state.model_copy(deep=True)

    def get(self, run_id: str) -> RunStateSnapshot:
        with self._session_factory() as session:
            row = session.get(RunStateRow, run_id)
            if row is None:
                raise RunNotFoundError(f"Run {run_id} does not exist")
            return _deserialize_model(RunStateSnapshot, row.payload).model_copy(deep=True)

    def list(self, query: RunListQuery) -> RunStatePage:
        with self._session_factory() as session:
            filtered_stmt = select(RunStateRow)
            if query.status is not None:
                filtered_stmt = filtered_stmt.where(RunStateRow.status == query.status.value)
            if query.workflow_type is not None:
                filtered_stmt = filtered_stmt.where(
                    RunStateRow.workflow_type == query.workflow_type.value
                )
            total_count = int(
                session.scalar(select(func.count()).select_from(filtered_stmt.subquery())) or 0
            )
            ordered_stmt = filtered_stmt.order_by(
                RunStateRow.created_at.desc(),
                RunStateRow.run_id.desc(),
            )
            rows = session.scalars(
                ordered_stmt.offset(query.offset).limit(query.limit)
            ).all()
            return RunStatePage(
                items=[
                    _deserialize_model(RunStateSnapshot, row.payload).model_copy(deep=True)
                    for row in rows
                ],
                page=_build_page_info(total_count, query.limit, query.offset),
            )


class SqlAlchemyRunEventRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def append(self, event_record: RunEventRecord) -> RunEventRecord:
        with self._session_factory() as session:
            session.add(
                RunEventRow(
                    event_id=event_record.event_id,
                    run_id=event_record.run_id,
                    event_type=event_record.event_type.value,
                    occurred_at=event_record.occurred_at,
                    payload=_serialize_model(event_record),
                )
            )
            session.commit()
        return event_record.model_copy(deep=True)

    def list(self, run_id: str, query: RunEventListQuery) -> RunEventPage:
        with self._session_factory() as session:
            filtered_stmt = select(RunEventRow).where(RunEventRow.run_id == run_id)
            total_count = int(
                session.scalar(select(func.count()).select_from(filtered_stmt.subquery())) or 0
            )
            ordered_stmt = filtered_stmt.order_by(
                RunEventRow.occurred_at.desc(),
                RunEventRow.event_id.desc(),
            )
            rows = session.scalars(
                ordered_stmt.offset(query.offset).limit(query.limit)
            ).all()
            return RunEventPage(
                items=[
                    _deserialize_model(RunEventRecord, row.payload).model_copy(deep=True)
                    for row in rows
                ],
                page=_build_page_info(total_count, query.limit, query.offset),
            )


class SqlAlchemyRunApprovalRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def create(self, approval_record: ApprovalRecord) -> ApprovalRecord:
        with self._session_factory() as session:
            session.add(
                RunApprovalRow(
                    approval_id=approval_record.approval_id,
                    run_id=approval_record.run_id,
                    status=approval_record.status.value,
                    requested_at=approval_record.requested_at,
                    payload=_serialize_model(approval_record),
                )
            )
            session.commit()
        return approval_record.model_copy(deep=True)

    def update(self, approval_record: ApprovalRecord) -> ApprovalRecord:
        with self._session_factory() as session:
            row = session.get(RunApprovalRow, approval_record.approval_id)
            if row is None:
                raise RunApprovalNotFoundError(
                    f"Approval {approval_record.approval_id} does not exist for run {approval_record.run_id}"
                )
            row.status = approval_record.status.value
            row.requested_at = approval_record.requested_at
            row.payload = _serialize_model(approval_record)
            session.commit()
        return approval_record.model_copy(deep=True)

    def get(self, run_id: str, approval_id: str) -> ApprovalRecord:
        with self._session_factory() as session:
            row = session.get(RunApprovalRow, approval_id)
            if row is None or row.run_id != run_id:
                raise RunApprovalNotFoundError(
                    f"Approval {approval_id} does not exist for run {run_id}"
                )
            return _deserialize_model(ApprovalRecord, row.payload).model_copy(deep=True)

    def list(self, run_id: str, query: ApprovalListQuery) -> ApprovalPage:
        with self._session_factory() as session:
            filtered_stmt = select(RunApprovalRow).where(RunApprovalRow.run_id == run_id)
            if query.status is not None:
                filtered_stmt = filtered_stmt.where(RunApprovalRow.status == query.status.value)
            total_count = int(
                session.scalar(select(func.count()).select_from(filtered_stmt.subquery())) or 0
            )
            ordered_stmt = filtered_stmt.order_by(
                RunApprovalRow.requested_at.desc(),
                RunApprovalRow.approval_id.desc(),
            )
            rows = session.scalars(
                ordered_stmt.offset(query.offset).limit(query.limit)
            ).all()
            return ApprovalPage(
                items=[
                    _deserialize_model(ApprovalRecord, row.payload).model_copy(deep=True)
                    for row in rows
                ],
                page=_build_page_info(total_count, query.limit, query.offset),
            )


class SqlAlchemyRunVerificationRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def save(self, report: RunVerificationReport) -> RunVerificationReport:
        with self._session_factory() as session:
            session.add(
                RunVerificationRow(
                    verification_id=report.verification_id,
                    run_id=report.run_id,
                    verdict=report.verdict.value,
                    created_at=report.created_at,
                    payload=_serialize_model(report),
                )
            )
            session.commit()
        return report.model_copy(deep=True)

    def get_latest(self, run_id: str) -> RunVerificationReport:
        with self._session_factory() as session:
            stmt = (
                select(RunVerificationRow)
                .where(RunVerificationRow.run_id == run_id)
                .order_by(RunVerificationRow.created_at.desc(), RunVerificationRow.verification_id.desc())
                .limit(1)
            )
            row = session.scalar(stmt)
            if row is None:
                raise RunVerificationNotFoundError(f"No verification exists for run {run_id}")
            return _deserialize_model(RunVerificationReport, row.payload).model_copy(deep=True)


class SqlAlchemyRunPlanRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def save(self, report: RunPlanReport) -> RunPlanReport:
        with self._session_factory() as session:
            session.add(
                RunPlanRow(
                    plan_id=report.plan_id,
                    run_id=report.run_id,
                    created_at=report.created_at,
                    payload=_serialize_model(report),
                )
            )
            session.commit()
        return report.model_copy(deep=True)

    def get_latest(self, run_id: str) -> RunPlanReport:
        with self._session_factory() as session:
            stmt = (
                select(RunPlanRow)
                .where(RunPlanRow.run_id == run_id)
                .order_by(RunPlanRow.created_at.desc(), RunPlanRow.plan_id.desc())
                .limit(1)
            )
            row = session.scalar(stmt)
            if row is None:
                raise RunPlanNotFoundError(f"No plan exists for run {run_id}")
            return _deserialize_model(RunPlanReport, row.payload).model_copy(deep=True)


class SqlAlchemyRunTurnRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def save(self, record: RunTurnRecord) -> RunTurnRecord:
        with self._session_factory() as session:
            session.add(
                RunTurnRow(
                    turn_id=record.turn_id,
                    run_id=record.run_id,
                    task_id=record.task_id,
                    created_at=record.created_at,
                    payload=_serialize_model(record),
                )
            )
            session.commit()
        return record.model_copy(deep=True)

    def list(self, run_id: str, query: RunTurnListQuery) -> RunTurnPage:
        with self._session_factory() as session:
            filtered_stmt = select(RunTurnRow).where(RunTurnRow.run_id == run_id)
            total_count = int(
                session.scalar(select(func.count()).select_from(filtered_stmt.subquery())) or 0
            )
            ordered_stmt = filtered_stmt.order_by(
                RunTurnRow.created_at.desc(),
                RunTurnRow.turn_id.desc(),
            )
            rows = session.scalars(
                ordered_stmt.offset(query.offset).limit(query.limit)
            ).all()
            return RunTurnPage(
                items=[
                    _deserialize_model(RunTurnRecord, row.payload).model_copy(deep=True)
                    for row in rows
                ],
                page=_build_page_info(total_count, query.limit, query.offset),
            )


class SqlAlchemyRunToolCallRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def save(self, record: RunToolCallRecord) -> RunToolCallRecord:
        with self._session_factory() as session:
            session.add(
                RunToolCallRow(
                    tool_call_id=record.tool_call_id,
                    run_id=record.run_id,
                    turn_id=record.turn_id,
                    task_id=record.task_id,
                    created_at=record.created_at,
                    payload=_serialize_model(record),
                )
            )
            session.commit()
        return record.model_copy(deep=True)

    def list(self, run_id: str, query: RunToolCallListQuery) -> RunToolCallPage:
        with self._session_factory() as session:
            filtered_stmt = select(RunToolCallRow).where(RunToolCallRow.run_id == run_id)
            total_count = int(
                session.scalar(select(func.count()).select_from(filtered_stmt.subquery())) or 0
            )
            ordered_stmt = filtered_stmt.order_by(
                RunToolCallRow.created_at.desc(),
                RunToolCallRow.tool_call_id.desc(),
            )
            rows = session.scalars(
                ordered_stmt.offset(query.offset).limit(query.limit)
            ).all()
            return RunToolCallPage(
                items=[
                    _deserialize_model(RunToolCallRecord, row.payload).model_copy(deep=True)
                    for row in rows
                ],
                page=_build_page_info(total_count, query.limit, query.offset),
            )


class SqlAlchemyRunOutputRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self._session_factory = session_factory

    def save(self, record: RunOutputRecord) -> RunOutputRecord:
        with self._session_factory() as session:
            session.add(
                RunOutputRow(
                    output_id=record.output_id,
                    run_id=record.run_id,
                    created_at=record.created_at,
                    payload=_serialize_model(record),
                )
            )
            session.commit()
        return record.model_copy(deep=True)

    def get_latest(self, run_id: str) -> RunOutputRecord:
        with self._session_factory() as session:
            stmt = (
                select(RunOutputRow)
                .where(RunOutputRow.run_id == run_id)
                .order_by(RunOutputRow.created_at.desc(), RunOutputRow.output_id.desc())
                .limit(1)
            )
            row = session.scalar(stmt)
            if row is None:
                raise RunOutputNotFoundError(f"No output exists for run {run_id}")
            return _deserialize_model(RunOutputRecord, row.payload).model_copy(deep=True)
