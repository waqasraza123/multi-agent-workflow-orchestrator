from collections.abc import Mapping, Sequence

from multi_agent_platform.agents.providers import LlmProvider
from multi_agent_platform.agents.runtime import TurnExecutionResult
from multi_agent_platform.contracts.runs import RunStateSnapshot, TaskRecord
from multi_agent_platform.contracts.turn_execution import (
    AgentExecutionProfile,
    ExecutionBackend,
    LlmTurnRequest,
    LlmTurnResponse,
)


class LlmTurnExecutor:
    def __init__(
        self,
        providers: Mapping[str, LlmProvider],
        available_tool_names: Sequence[str] | None = None,
    ) -> None:
        self._providers = dict(providers)
        self._available_tool_names = list(available_tool_names or [])

    def execute_turn(
        self,
        run_state: RunStateSnapshot,
        task: TaskRecord,
        execution_profile: AgentExecutionProfile | None = None,
    ) -> TurnExecutionResult:
        response = self.execute_structured_turn(
            run_state,
            task,
            execution_profile,
        )
        return TurnExecutionResult(
            summary=response.output.summary,
            planned_tool_calls=response.output.planned_tool_calls,
        )

    def execute_structured_turn(
        self,
        run_state: RunStateSnapshot,
        task: TaskRecord,
        execution_profile: AgentExecutionProfile | None = None,
    ) -> LlmTurnResponse:
        profile = self._validate_execution_profile(task, execution_profile)
        provider_name = profile.llm_provider_name
        if provider_name is None:
            raise ValueError("LlmTurnExecutor requires llm_provider_name")

        provider = self._providers.get(provider_name)
        if provider is None:
            raise ValueError(f"No LLM provider registered for {provider_name}")

        request = LlmTurnRequest(
            run_id=run_state.run_id,
            user_goal=run_state.user_goal,
            task=task,
            execution_profile=profile,
            available_tool_names=self._available_tool_names,
        )
        return provider.generate_turn(request)

    def _validate_execution_profile(
        self,
        task: TaskRecord,
        execution_profile: AgentExecutionProfile | None,
    ) -> AgentExecutionProfile:
        if execution_profile is None:
            raise ValueError("LlmTurnExecutor requires an execution profile")
        if execution_profile.agent_name != task.assigned_agent:
            raise ValueError(
                "Execution profile agent "
                f"{execution_profile.agent_name} does not match "
                f"task agent {task.assigned_agent}"
            )
        if execution_profile.backend is not ExecutionBackend.LLM:
            raise ValueError("LlmTurnExecutor requires llm backend")
        return execution_profile
