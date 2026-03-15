from typing import Protocol

from multi_agent_platform.agents.runtime import TurnExecutionResult, execute_deterministic_turn
from multi_agent_platform.contracts.runs import RunStateSnapshot, TaskRecord
from multi_agent_platform.contracts.turn_execution import (
    AgentExecutionProfile,
    ExecutionBackend,
)


class TurnExecutor(Protocol):
    def execute_turn(
        self,
        run_state: RunStateSnapshot,
        task: TaskRecord,
        execution_profile: AgentExecutionProfile | None = None,
    ) -> TurnExecutionResult: ...


class DeterministicTurnExecutor:
    def execute_turn(
        self,
        run_state: RunStateSnapshot,
        task: TaskRecord,
        execution_profile: AgentExecutionProfile | None = None,
    ) -> TurnExecutionResult:
        self._validate_execution_profile(task, execution_profile)
        return execute_deterministic_turn(run_state, task)

    def _validate_execution_profile(
        self,
        task: TaskRecord,
        execution_profile: AgentExecutionProfile | None,
    ) -> None:
        if execution_profile is None:
            return
        if execution_profile.agent_name != task.assigned_agent:
            raise ValueError(
                "Execution profile agent "
                f"{execution_profile.agent_name} does not match "
                f"task agent {task.assigned_agent}"
            )
        if execution_profile.backend is not ExecutionBackend.DETERMINISTIC:
            raise ValueError("DeterministicTurnExecutor requires deterministic backend")
