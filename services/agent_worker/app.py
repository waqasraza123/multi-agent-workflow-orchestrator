import os
import json
import logging
import time
from collections.abc import Awaitable, Callable, Mapping
from typing import cast
from urllib.error import HTTPError, URLError
from urllib.request import Request as UrlRequest
from urllib.request import urlopen

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi import status as http_status

from multi_agent_platform.agents.fake_provider import FakeLlmProvider
from multi_agent_platform.agents.openai_provider import OpenAiCompatibleProvider
from multi_agent_platform.agents.providers import LlmProvider
from multi_agent_platform.agents.runtime import build_planned_tool_call, build_turn_summary
from multi_agent_platform.contracts.runs import RunStateSnapshot, RunStatus, WorkflowType
from multi_agent_platform.contracts.turn_execution import (
    LlmPlanOutput,
    LlmPlanRequest,
    LlmPlanResponse,
    LlmPlanningOutcome,
    LlmExecutionOutcome,
    LlmTurnRequest,
    LlmUsage,
    StructuredTurnOutput,
)
from multi_agent_platform.planning.templates import build_run_plan


LOGGER = logging.getLogger("agent_worker")
REQUEST_ID_HEADER = "x-request-id"
TRACEPARENT_HEADER = "traceparent"


def create_app() -> FastAPI:
    application = FastAPI(title="Agent Runway Agent Worker", version="0.1.0")
    executor = AgentWorkerExecutor()

    @application.middleware("http")
    async def request_observability_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started_at = time.perf_counter()
        request_id = request.headers.get(REQUEST_ID_HEADER, "")
        traceparent = request.headers.get(TRACEPARENT_HEADER, "")
        response = await call_next(request)
        if request_id:
            response.headers[REQUEST_ID_HEADER] = request_id
        if traceparent:
            response.headers[TRACEPARENT_HEADER] = traceparent
        LOGGER.info(
            "agent_worker_request",
            extra={
                "request_id": request_id,
                "traceparent": traceparent,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.perf_counter() - started_at) * 1000),
            },
        )
        return response

    @application.get("/health")
    def get_health() -> dict[str, str]:
        return {"status": "ok"}

    @application.post("/internal/agent/turn", response_model=LlmExecutionOutcome)
    def execute_agent_turn(
        request: LlmTurnRequest,
        _: None = Depends(require_worker_token),
    ) -> LlmExecutionOutcome:
        return executor.execute_turn(request)

    @application.post("/internal/agent/plan", response_model=LlmPlanningOutcome)
    def generate_agent_plan(
        request: LlmPlanRequest,
        _: None = Depends(require_worker_token),
    ) -> LlmPlanningOutcome:
        return executor.generate_plan(request)

    return application


def require_worker_token(authorization: str | None = Header(default=None)) -> None:
    expected_token = os.getenv("AGENT_WORKER_TOKEN")
    if expected_token is None or expected_token.strip() == "":
        return

    expected_header = f"Bearer {expected_token.strip()}"
    if authorization != expected_header:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid worker token",
        )


class AgentWorkerExecutor:
    def generate_plan(self, request: LlmPlanRequest) -> LlmPlanningOutcome:
        profile = request.execution_profile
        provider_name = profile.llm_provider_name
        if provider_name == "fake":
            return self._fake_plan(request)
        if provider_name != "openai":
            return self._fallback_plan(
                request,
                f"No planning provider registered for {provider_name}",
            )
        if os.getenv("LLM_API_KEY") is None or os.getenv("LLM_API_KEY", "").strip() == "":
            return self._fallback_plan(request, "LLM_API_KEY must be set for openai planning")

        attempt_total = profile.max_retries + 1
        last_error_message: str | None = None
        for attempt_index in range(attempt_total):
            try:
                return self._openai_plan(request, attempt_count=attempt_index + 1)
            except Exception as error:
                last_error_message = str(error)
                if attempt_index == attempt_total - 1:
                    break
                continue
        return self._fallback_plan(
            request,
            last_error_message or "LLM planning failed",
            attempt_count=attempt_total,
        )

    def execute_turn(self, request: LlmTurnRequest) -> LlmExecutionOutcome:
        profile = request.execution_profile
        providers = self._build_providers()
        provider_name = profile.llm_provider_name
        provider = providers.get(provider_name or "")
        if provider is None:
            return self._fallback(request, f"No LLM provider registered for {provider_name}")

        attempt_total = profile.max_retries + 1
        last_error_message: str | None = None

        for attempt_index in range(attempt_total):
            try:
                response = provider.generate_turn(request)
            except Exception as error:
                last_error_message = str(error)
                if attempt_index == attempt_total - 1:
                    break
                continue
            return LlmExecutionOutcome(
                output=response.output,
                llm_response=response,
                attempt_count=attempt_index + 1,
            )

        return self._fallback(
            request,
            last_error_message or "LLM execution failed",
            attempt_count=attempt_total,
        )

    def _fake_plan(self, request: LlmPlanRequest) -> LlmPlanningOutcome:
        output = self._deterministic_plan_output(request)
        return LlmPlanningOutcome(
            output=output,
            llm_response=LlmPlanResponse(
                provider_name="fake",
                model_name=request.execution_profile.model_name or "fake-model",
                output=output,
                usage=LlmUsage(),
                finish_reason="stop",
            ),
            attempt_count=1,
        )

    def _openai_plan(
        self,
        request: LlmPlanRequest,
        *,
        attempt_count: int,
    ) -> LlmPlanningOutcome:
        profile = request.execution_profile
        started_at = time.perf_counter()
        response_data = self._post_openai_json(
            payload=self._build_plan_payload(request),
            timeout_seconds=profile.timeout_seconds or 30.0,
        )
        output, raw_response_text = self._parse_plan_response(request, response_data)
        latency_ms = round((time.perf_counter() - started_at) * 1000)
        response = LlmPlanResponse(
            provider_name="openai",
            model_name=self._response_model_name(response_data, profile.model_name),
            output=output,
            usage=self._build_usage(response_data.get("usage")),
            finish_reason=self._finish_reason(response_data),
            latency_ms=latency_ms,
            raw_response_text=raw_response_text,
        )
        return LlmPlanningOutcome(
            output=output,
            llm_response=response,
            attempt_count=attempt_count,
        )

    def _fallback_plan(
        self,
        request: LlmPlanRequest,
        error_message: str,
        *,
        attempt_count: int = 1,
    ) -> LlmPlanningOutcome:
        return LlmPlanningOutcome(
            output=self._deterministic_plan_output(request),
            error_message=error_message,
            fallback_used=True,
            attempt_count=attempt_count,
        )

    def _deterministic_plan_output(self, request: LlmPlanRequest) -> LlmPlanOutput:
        run_state = RunStateSnapshot(
            run_id=request.run_id,
            workflow_type=WorkflowType(request.workflow_type),
            status=RunStatus.PLANNING,
            user_goal=request.user_goal,
        )
        plan = build_run_plan(run_state)
        return LlmPlanOutput(
            run_id=plan.run_id,
            workflow_type=plan.workflow_type.value,
            template_name=plan.template_name,
            summary=plan.summary,
            tasks=plan.tasks,
        )

    def _post_openai_json(
        self,
        *,
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> dict[str, object]:
        base_url = os.getenv("LLM_API_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        api_key = os.getenv("LLM_API_KEY", "").strip()
        request = UrlRequest(
            f"{base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_seconds) as response:
                raw_response = response.read().decode("utf-8")
        except HTTPError as error:
            response_body = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"OpenAI planning request failed with status {error.code}: {response_body}"
            ) from error
        except URLError as error:
            raise RuntimeError(f"OpenAI planning request failed: {error.reason}") from error
        loaded = json.loads(raw_response)
        if not isinstance(loaded, dict):
            raise ValueError("OpenAI planning response must be a JSON object")
        return cast(dict[str, object], loaded)

    def _build_plan_payload(self, request: LlmPlanRequest) -> dict[str, object]:
        profile = request.execution_profile
        payload: dict[str, object] = {
            "model": profile.model_name or os.getenv("LLM_MODEL_NAME", "gpt-4.1-mini"),
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You generate execution plans for Agent Runway. Return only valid "
                        "JSON. Do not include markdown fences or extra text."
                    ),
                },
                {
                    "role": "user",
                    "content": self._build_plan_prompt(request),
                },
            ],
            "response_format": {"type": "json_object"},
        }
        if profile.temperature is not None:
            payload["temperature"] = profile.temperature
        if profile.max_output_tokens is not None:
            payload["max_tokens"] = profile.max_output_tokens
        return payload

    def _build_plan_prompt(self, request: LlmPlanRequest) -> str:
        example_payload = self._deterministic_plan_output(request).model_dump(mode="json")
        return "\n".join(
            [
                f"run_id: {request.run_id}",
                f"workflow_type: {request.workflow_type}",
                f"user_goal: {request.user_goal}",
                "Return a JSON object with keys run_id, workflow_type, template_name, summary, tasks.",
                "tasks must contain 2 to 6 task objects.",
                "Each task needs task_id, title, description, assigned_agent, dependency_ids, acceptance_criteria.",
                "Use stable snake_case task_id values.",
                "Only use dependency_ids that reference earlier task_id values.",
                "Use assigned_agent values from planner, researcher, writer, executor.",
                f"Example JSON shape: {json.dumps(example_payload)}",
            ]
        )

    def _parse_plan_response(
        self,
        request: LlmPlanRequest,
        response_data: dict[str, object],
    ) -> tuple[LlmPlanOutput, str]:
        choices = response_data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise ValueError("OpenAI planning response must include choices")
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise ValueError("OpenAI planning choice must be an object")
        message_payload = first_choice.get("message")
        if not isinstance(message_payload, dict):
            raise ValueError("OpenAI planning choice must include a message")
        raw_response_text = self._extract_response_text(message_payload.get("content"))
        loaded = json.loads(raw_response_text)
        if not isinstance(loaded, dict):
            raise ValueError("OpenAI planning content must be a JSON object")
        loaded["run_id"] = request.run_id
        loaded["workflow_type"] = request.workflow_type
        output = LlmPlanOutput.model_validate(loaded)
        self._validate_plan_dependencies(output)
        return output, raw_response_text

    def _validate_plan_dependencies(self, output: LlmPlanOutput) -> None:
        known_task_ids: set[str] = set()
        for task in output.tasks:
            if task.task_id in known_task_ids:
                raise ValueError(f"Duplicate task_id returned by planner: {task.task_id}")
            for dependency_id in task.dependency_ids:
                if dependency_id not in known_task_ids:
                    raise ValueError(
                        f"Task {task.task_id} has unknown or forward dependency {dependency_id}"
                    )
            known_task_ids.add(task.task_id)

    def _response_model_name(
        self,
        response_data: dict[str, object],
        fallback_model_name: str | None,
    ) -> str:
        model_name = response_data.get("model")
        if isinstance(model_name, str) and model_name:
            return model_name
        return fallback_model_name or os.getenv("LLM_MODEL_NAME", "gpt-4.1-mini")

    def _finish_reason(self, response_data: dict[str, object]) -> str | None:
        choices = response_data.get("choices")
        if not isinstance(choices, list) or not choices:
            return None
        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            return None
        finish_reason = first_choice.get("finish_reason")
        return finish_reason if isinstance(finish_reason, str) else None

    def _build_usage(self, usage_payload: object) -> LlmUsage:
        if not isinstance(usage_payload, dict):
            return LlmUsage()
        input_tokens = usage_payload.get("prompt_tokens")
        output_tokens = usage_payload.get("completion_tokens")
        total_tokens = usage_payload.get("total_tokens")
        parsed_input_tokens = input_tokens if isinstance(input_tokens, int) else 0
        parsed_output_tokens = output_tokens if isinstance(output_tokens, int) else 0
        parsed_total_tokens = (
            total_tokens
            if isinstance(total_tokens, int)
            else parsed_input_tokens + parsed_output_tokens
        )
        return LlmUsage(
            input_tokens=parsed_input_tokens,
            output_tokens=parsed_output_tokens,
            total_tokens=parsed_total_tokens,
        )

    def _extract_response_text(self, content: object) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text_parts: list[str] = []
            for item in content:
                if not isinstance(item, dict):
                    continue
                text_value = item.get("text")
                if isinstance(text_value, str):
                    text_parts.append(text_value)
            combined = "".join(text_parts).strip()
            if combined:
                return combined
        raise ValueError("OpenAI planning message content must contain text")

    def _build_providers(self) -> Mapping[str, LlmProvider]:
        providers: dict[str, LlmProvider] = {"fake": FakeLlmProvider()}
        openai_api_key = os.getenv("LLM_API_KEY")
        if openai_api_key is not None and openai_api_key.strip():
            providers["openai"] = OpenAiCompatibleProvider(
                api_key=openai_api_key,
                base_url=os.getenv("LLM_API_BASE_URL", "https://api.openai.com/v1"),
                default_model_name=os.getenv("LLM_MODEL_NAME", "gpt-4.1-mini"),
            )
        return providers

    def _fallback(
        self,
        request: LlmTurnRequest,
        error_message: str,
        *,
        attempt_count: int = 1,
    ) -> LlmExecutionOutcome:
        task = request.task
        output = StructuredTurnOutput(
            summary=build_turn_summary(task.assigned_agent, task.title),
            planned_tool_calls=[
                build_planned_tool_call(
                    agent_name=task.assigned_agent,
                    user_goal=request.user_goal,
                    task_title=task.title,
                )
            ],
        )
        return LlmExecutionOutcome(
            output=output,
            llm_response=None,
            error_message=error_message,
            fallback_used=True,
            attempt_count=attempt_count,
        )


app = create_app()
