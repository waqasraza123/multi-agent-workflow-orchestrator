import pytest
from fastapi.testclient import TestClient

from multi_agent_platform.api.dependencies import reset_api_state
from multi_agent_platform.main import app


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_api_state()


def register_single_task(client: TestClient, run_id: str) -> None:
    response = client.post(
        f"/runs/{run_id}/tasks",
        json={
            "items": [
                {
                    "task_id": "task_1",
                    "title": "Review logs",
                    "description": "Review service logs",
                    "assigned_agent": "planner",
                    "acceptance_criteria": ["Logs reviewed"],
                }
            ]
        },
    )
    assert response.status_code == 200


def test_create_and_get_run_endpoints_return_wrapped_run_detail() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/runs",
        json={
            "user_goal": "Investigate the failed deployment",
            "workflow_type": "document_analysis",
        },
    )

    assert create_response.status_code == 201
    created_payload = create_response.json()["item"]
    run_id = created_payload["run_id"]

    assert created_payload["status"] == "planning"
    assert created_payload["workflow_type"] == "document_analysis"
    assert created_payload["task_count"] == 0
    assert created_payload["evidence_count"] == 0

    get_response = client.get(f"/runs/{run_id}")

    assert get_response.status_code == 200
    fetched_payload = get_response.json()["item"]
    assert fetched_payload["run_id"] == run_id
    assert fetched_payload["user_goal"] == "Investigate the failed deployment"


def test_list_runs_supports_pagination_and_filters() -> None:
    client = TestClient(app)

    client.post(
        "/runs",
        json={"user_goal": "Prepare a rollout plan", "workflow_type": "technical_plan"},
    )
    client.post(
        "/runs",
        json={
            "user_goal": "Analyze the incident report",
            "workflow_type": "document_analysis",
        },
    )

    list_response = client.get("/runs?limit=1&offset=0&workflow_type=document_analysis")

    assert list_response.status_code == 200
    payload = list_response.json()
    assert len(payload["items"]) == 1
    assert payload["items"][0]["user_goal"] == "Analyze the incident report"
    assert payload["items"][0]["workflow_type"] == "document_analysis"
    assert payload["page"] == {
        "limit": 1,
        "offset": 0,
        "total_count": 1,
        "has_more": False,
    }


def test_run_mutation_endpoints_progress_tasks_and_record_evidence() -> None:
    client = TestClient(app)

    create_response = client.post("/runs", json={"user_goal": "Handle an incident"})
    run_id = create_response.json()["item"]["run_id"]

    register_single_task(client, run_id)

    start_response = client.post(f"/runs/{run_id}/tasks/task_1/start")
    assert start_response.status_code == 200
    assert start_response.json()["item"]["current_task_id"] == "task_1"

    complete_response = client.post(f"/runs/{run_id}/tasks/task_1/complete")
    assert complete_response.status_code == 200
    task_statuses = [task["status"] for task in complete_response.json()["item"]["tasks"]]
    assert task_statuses == ["completed"]

    evidence_response = client.post(
        f"/runs/{run_id}/evidence",
        json={
            "evidence_id": "evidence_1",
            "source_type": "document",
            "source_ref": "incident-notes.md",
            "summary": "Notes confirm the deployment started the issue",
            "collected_by_agent": "researcher",
            "confidence": 0.91,
        },
    )

    assert evidence_response.status_code == 200
    assert len(evidence_response.json()["item"]["evidence"]) == 1


def test_run_events_endpoint_returns_timeline() -> None:
    client = TestClient(app)

    create_response = client.post("/runs", json={"user_goal": "Track event history"})
    run_id = create_response.json()["item"]["run_id"]

    register_single_task(client, run_id)

    response = client.get(f"/runs/{run_id}/events?limit=10&offset=0")

    assert response.status_code == 200
    payload = response.json()
    assert payload["page"]["total_count"] == 2
    assert payload["items"][0]["event_type"] == "tasks_registered"
    assert payload["items"][1]["event_type"] == "run_created"


def test_approval_endpoints_create_list_and_decide_requests() -> None:
    client = TestClient(app)

    create_response = client.post("/runs", json={"user_goal": "Approval flow"})
    run_id = create_response.json()["item"]["run_id"]

    approval_response = client.post(
        f"/runs/{run_id}/approvals",
        json={
            "requested_action": "Send deployment notice",
            "reason": "External communication is required",
            "risk_summary": "Incorrect message could confuse users",
            "proposed_next_step": "Wait for reviewer response",
        },
    )

    assert approval_response.status_code == 200
    approval_id = approval_response.json()["item"]["approval_id"]
    assert approval_response.json()["item"]["status"] == "pending"

    list_response = client.get(f"/runs/{run_id}/approvals?limit=10&offset=0&status=pending")
    assert list_response.status_code == 200
    assert list_response.json()["page"]["total_count"] == 1
    assert list_response.json()["items"][0]["approval_id"] == approval_id

    decision_response = client.post(
        f"/runs/{run_id}/approvals/{approval_id}/decide",
        json={
            "decision": "approve",
            "reviewer_id": "reviewer_1",
            "reviewer_note": "Approved for action",
        },
    )

    assert decision_response.status_code == 200
    assert decision_response.json()["item"]["status"] == "approved"

    event_response = client.get(f"/runs/{run_id}/events?limit=10&offset=0")
    assert event_response.status_code == 200
    assert event_response.json()["items"][0]["event_type"] == "approval_decided"


def test_redeciding_approval_returns_conflict() -> None:
    client = TestClient(app)

    create_response = client.post("/runs", json={"user_goal": "Approval conflict"})
    run_id = create_response.json()["item"]["run_id"]

    approval_response = client.post(
        f"/runs/{run_id}/approvals",
        json={
            "requested_action": "Publish summary",
            "reason": "Public statement is required",
            "risk_summary": "Incorrect summary could mislead users",
        },
    )
    approval_id = approval_response.json()["item"]["approval_id"]

    first_decision = client.post(
        f"/runs/{run_id}/approvals/{approval_id}/decide",
        json={
            "decision": "reject",
            "reviewer_id": "reviewer_1",
        },
    )
    second_decision = client.post(
        f"/runs/{run_id}/approvals/{approval_id}/decide",
        json={
            "decision": "approve",
            "reviewer_id": "reviewer_2",
        },
    )

    assert first_decision.status_code == 200
    assert second_decision.status_code == 409


def test_verification_endpoints_return_reports() -> None:
    client = TestClient(app)

    create_response = client.post("/runs", json={"user_goal": "Verify readiness"})
    run_id = create_response.json()["item"]["run_id"]
    register_single_task(client, run_id)
    client.post(f"/runs/{run_id}/tasks/task_1/start")
    client.post(f"/runs/{run_id}/tasks/task_1/complete")

    verify_response = client.post(f"/runs/{run_id}/verify")
    latest_response = client.get(f"/runs/{run_id}/verifications/latest")

    assert verify_response.status_code == 200
    assert verify_response.json()["item"]["verdict"] == "pass"
    assert latest_response.status_code == 200
    assert (
        latest_response.json()["item"]["verification_id"]
        == verify_response.json()["item"]["verification_id"]
    )


def test_verification_endpoint_fails_for_incomplete_run() -> None:
    client = TestClient(app)

    create_response = client.post("/runs", json={"user_goal": "Verify incomplete run"})
    run_id = create_response.json()["item"]["run_id"]
    register_single_task(client, run_id)

    verify_response = client.post(f"/runs/{run_id}/verify")

    assert verify_response.status_code == 200
    assert verify_response.json()["item"]["verdict"] == "fail"


def test_invalid_task_transition_returns_conflict() -> None:
    client = TestClient(app)

    create_response = client.post("/runs", json={"user_goal": "Test invalid transition"})
    run_id = create_response.json()["item"]["run_id"]

    response = client.post(f"/runs/{run_id}/tasks/missing_task/start")

    assert response.status_code == 409


def test_get_missing_run_returns_not_found() -> None:
    client = TestClient(app)

    response = client.get("/runs/run_missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Run run_missing does not exist"


def test_get_run_state_returns_wrapped_run_snapshot() -> None:
    client = TestClient(app)

    create_response = client.post("/runs", json={"user_goal": "Summarize uploaded documents"})
    run_id = create_response.json()["item"]["run_id"]

    state_response = client.get(f"/runs/{run_id}/state")

    assert state_response.status_code == 200
    assert state_response.json()["item"]["run_id"] == run_id
    assert state_response.json()["item"]["user_goal"] == "Summarize uploaded documents"
