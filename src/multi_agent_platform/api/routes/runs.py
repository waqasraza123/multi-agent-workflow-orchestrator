from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict

from multi_agent_platform.api.dependencies import get_run_service
from multi_agent_platform.application.runs import RunService
from multi_agent_platform.contracts.runs import (
    RunCreateRequest,
    RunStateSnapshot,
    RunStatus,
    WorkflowType,
)
from multi_agent_platform.storage.run_repository import RunNotFoundError

router = APIRouter(prefix="/runs", tags=["runs"])
RunServiceDependency = Annotated[RunService, Depends(get_run_service)]


class RunSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    workflow_type: WorkflowType
    status: RunStatus
    user_goal: str
    created_at: datetime
    updated_at: datetime
    current_task_id: str | None


class RunListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[RunSummary]


def build_run_summary(run_state: RunStateSnapshot) -> RunSummary:
    return RunSummary(
        run_id=run_state.run_id,
        workflow_type=run_state.workflow_type,
        status=run_state.status,
        user_goal=run_state.user_goal,
        created_at=run_state.created_at,
        updated_at=run_state.updated_at,
        current_task_id=run_state.current_task_id,
    )


@router.post("", response_model=RunStateSnapshot, status_code=status.HTTP_201_CREATED)
def create_run(
    request: RunCreateRequest,
    run_service: RunServiceDependency,
) -> RunStateSnapshot:
    return run_service.create_run(request)


@router.get("", response_model=RunListResponse)
def list_runs(
    run_service: RunServiceDependency,
) -> RunListResponse:
    return RunListResponse(
        items=[build_run_summary(run_state) for run_state in run_service.list_runs()]
    )


@router.get("/{run_id}", response_model=RunStateSnapshot)
def get_run(
    run_id: str,
    run_service: RunServiceDependency,
) -> RunStateSnapshot:
    try:
        return run_service.get_run(run_id)
    except RunNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error


@router.get("/{run_id}/state", response_model=RunStateSnapshot)
def get_run_state(
    run_id: str,
    run_service: RunServiceDependency,
) -> RunStateSnapshot:
    try:
        return run_service.get_run_state(run_id)
    except RunNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
