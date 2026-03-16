from multi_agent_platform.agents.openai_provider import OpenAiCompatibleProvider
from multi_agent_platform.contracts.runs import TaskRecord
from multi_agent_platform.contracts.turn_execution import (
    AgentExecutionProfile,
    ExecutionBackend,
    LlmTurnRequest,
)


def build_request() -> LlmTurnRequest:
    return LlmTurnRequest(
        run_id="run_1",
        user_goal="Create a technical delivery plan",
        task=TaskRecord(
            task_id="task_1",
            title="Break work into phases",
            description="Create the task breakdown",
            assigned_agent="planner",
            acceptance_criteria=["Phases are clear"],
        ),
        execution_profile=AgentExecutionProfile(
            agent_name="planner",
            backend=ExecutionBackend.LLM,
            llm_provider_name="openai",
            model_name="gpt-4.1-mini",
            max_output_tokens=256,
            temperature=0.2,
        ),
        available_tool_names=["goal_analyzer"],
    )


def test_openai_provider_generates_structured_turn_response() -> None:
    provider = OpenAiCompatibleProvider(
        api_key="test-key",
        transport=lambda url, headers, payload, timeout_seconds: {
            "model": "gpt-4.1-mini",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": (
                            '{"summary":"Planner prepared the structured next step.",'
                            '"planned_tool_calls":['
                            '{"tool_name":"goal_analyzer",'
                            '"tool_input":{"task_title":"Break work into phases"}}'
                            "]}"
                        )
                    },
                }
            ],
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 8,
                "total_tokens": 20,
            },
        },
    )

    response = provider.generate_turn(build_request())

    assert response.provider_name == "openai"
    assert response.model_name == "gpt-4.1-mini"
    assert response.output.summary == "Planner prepared the structured next step."
    assert response.output.planned_tool_calls[0].tool_name == "goal_analyzer"
    assert response.usage.total_tokens == 20
    assert response.finish_reason == "stop"


def test_openai_provider_rejects_unknown_tool_name() -> None:
    provider = OpenAiCompatibleProvider(
        api_key="test-key",
        transport=lambda url, headers, payload, timeout_seconds: {
            "model": "gpt-4.1-mini",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "content": (
                            '{"summary":"Planner prepared the structured next step.",'
                            '"planned_tool_calls":['
                            '{"tool_name":"unknown_tool",'
                            '"tool_input":{"task_title":"Break work into phases"}}'
                            "]}"
                        )
                    },
                }
            ],
            "usage": {
                "prompt_tokens": 12,
                "completion_tokens": 8,
                "total_tokens": 20,
            },
        },
    )

    try:
        provider.generate_turn(build_request())
    except ValueError as error:
        assert "Unsupported tool name" in str(error)
        return

    raise AssertionError("Expected ValueError for unsupported tool name")
