from typing import Protocol

from multi_agent_platform.contracts.turn_execution import (
    LlmTurnRequest,
    LlmTurnResponse,
)


class LlmProvider(Protocol):
    provider_name: str

    def generate_turn(self, request: LlmTurnRequest) -> LlmTurnResponse: ...
