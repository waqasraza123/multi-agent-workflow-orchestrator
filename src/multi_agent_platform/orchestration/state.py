from multi_agent_platform.contracts.common import generate_identifier, utc_now
from multi_agent_platform.contracts.runs import (
    EvidenceRecord,
    RunCreateRequest,
    RunStateSnapshot,
    RunStatus,
    TaskRecord,
    TaskStatus,
)


class StateTransitionError(ValueError):
    pass


def create_run_state(
    request: RunCreateRequest,
    run_id: str | None = None,
) -> RunStateSnapshot:
    resolved_run_id = run_id or generate_identifier("run")
    return RunStateSnapshot(
        run_id=resolved_run_id,
        workflow_type=request.workflow_type,
        status=RunStatus.PLANNING,
        user_goal=request.user_goal,
        constraints=request.constraints,
        approval_policy=request.approval_policy,
    )


def register_tasks(
    run_state: RunStateSnapshot,
    tasks: list[TaskRecord],
) -> RunStateSnapshot:
    if not tasks:
        raise StateTransitionError("At least one task is required")

    existing_task_ids = {task.task_id for task in run_state.tasks}
    new_task_ids = [task.task_id for task in tasks]

    if len(set(new_task_ids)) != len(new_task_ids):
        raise StateTransitionError("Task identifiers must be unique")

    duplicate_task_ids = existing_task_ids.intersection(new_task_ids)
    if duplicate_task_ids:
        duplicated = ", ".join(sorted(duplicate_task_ids))
        raise StateTransitionError(f"Tasks already exist: {duplicated}")

    all_known_task_ids = existing_task_ids.union(new_task_ids)
    for task in tasks:
        unknown_dependency_ids = [
            dependency_id
            for dependency_id in task.dependency_ids
            if dependency_id not in all_known_task_ids
        ]
        if unknown_dependency_ids:
            missing = ", ".join(sorted(unknown_dependency_ids))
            raise StateTransitionError(f"Task {task.task_id} has unknown dependencies: {missing}")

    completed_task_ids = _completed_task_ids(run_state.tasks)
    normalized_tasks = [_normalize_pending_task(task, completed_task_ids) for task in tasks]
    return _replace_state(
        run_state,
        tasks=[*run_state.tasks, *normalized_tasks],
        status=RunStatus.PLANNING,
    )


def start_task(
    run_state: RunStateSnapshot,
    task_id: str,
) -> RunStateSnapshot:
    if run_state.current_task_id is not None:
        raise StateTransitionError("Only one task can be in progress at a time")

    target_task = _find_task(run_state.tasks, task_id)
    if target_task.status is not TaskStatus.READY:
        raise StateTransitionError(f"Task {task_id} is not ready to start")

    updated_tasks = [
        task.model_copy(update={"status": TaskStatus.IN_PROGRESS})
        if task.task_id == task_id
        else task
        for task in run_state.tasks
    ]
    return _replace_state(
        run_state,
        tasks=updated_tasks,
        current_task_id=task_id,
        status=RunStatus.EXECUTING,
    )


def complete_task(
    run_state: RunStateSnapshot,
    task_id: str,
) -> RunStateSnapshot:
    if run_state.current_task_id != task_id:
        raise StateTransitionError(f"Task {task_id} is not the active task")

    target_task = _find_task(run_state.tasks, task_id)
    if target_task.status is not TaskStatus.IN_PROGRESS:
        raise StateTransitionError(f"Task {task_id} is not in progress")

    completed_task_ids = _completed_task_ids(run_state.tasks).union({task_id})
    updated_tasks: list[TaskRecord] = []

    for task in run_state.tasks:
        if task.task_id == task_id:
            updated_tasks.append(task.model_copy(update={"status": TaskStatus.COMPLETED}))
            continue

        should_be_ready = task.status is TaskStatus.PENDING and _dependencies_completed(
            task, completed_task_ids
        )
        if should_be_ready:
            updated_tasks.append(task.model_copy(update={"status": TaskStatus.READY}))
            continue

        updated_tasks.append(task)

    next_status = (
        RunStatus.VERIFYING
        if all(task.status is TaskStatus.COMPLETED for task in updated_tasks)
        else RunStatus.EXECUTING
    )
    return _replace_state(
        run_state,
        tasks=updated_tasks,
        current_task_id=None,
        status=next_status,
    )


def record_evidence(
    run_state: RunStateSnapshot,
    evidence_record: EvidenceRecord,
) -> RunStateSnapshot:
    existing_evidence_ids = {existing_record.evidence_id for existing_record in run_state.evidence}
    if evidence_record.evidence_id in existing_evidence_ids:
        raise StateTransitionError(f"Evidence {evidence_record.evidence_id} already exists")

    return _replace_state(
        run_state,
        evidence=[*run_state.evidence, evidence_record],
    )


def _replace_state(
    run_state: RunStateSnapshot,
    **updates: object,
) -> RunStateSnapshot:
    merged_updates = {"updated_at": utc_now(), **updates}
    return run_state.model_copy(update=merged_updates, deep=True)


def _normalize_pending_task(
    task: TaskRecord,
    completed_task_ids: set[str],
) -> TaskRecord:
    if task.status is not TaskStatus.PENDING:
        return task

    next_status = (
        TaskStatus.READY
        if _dependencies_completed(task, completed_task_ids)
        else TaskStatus.PENDING
    )
    return task.model_copy(update={"status": next_status})


def _dependencies_completed(
    task: TaskRecord,
    completed_task_ids: set[str],
) -> bool:
    return all(dependency_id in completed_task_ids for dependency_id in task.dependency_ids)


def _completed_task_ids(tasks: list[TaskRecord]) -> set[str]:
    return {task.task_id for task in tasks if task.status is TaskStatus.COMPLETED}


def _find_task(tasks: list[TaskRecord], task_id: str) -> TaskRecord:
    for task in tasks:
        if task.task_id == task_id:
            return task
    raise StateTransitionError(f"Task {task_id} does not exist")
