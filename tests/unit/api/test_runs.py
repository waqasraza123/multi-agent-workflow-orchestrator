import pytest
from fastapi.testclient import TestClient

from multi_agent_platform.api.dependencies import reset_api_state
from multi_agent_platform.main import app


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_api_state()


def test_create_and_get_run_endpoints_return_created_run() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/runs",
        json={"user_goal": "Investigate the failed deployment"},
    )

    assert create_response.status_code == 201
    created_payload = create_response.json()
    assert created_payload["status"] == "planning"
    assert created_payload["workflow_type"] == "technical_plan"

    get_response = client.get(f"/runs/{created_payload['run_id']}")
    assert get_response.status_code == 200

    fetched_payload = get_response.json()
    assert fetched_payload["run_id"] == created_payload["run_id"]
    assert fetched_payload["user_goal"] == "Investigate the failed deployment"


def test_list_runs_returns_created_runs() -> None:
    client = TestClient(app)

    first_response = client.post("/runs", json={"user_goal": "Prepare a rollout plan"})
    second_response = client.post("/runs", json={"user_goal": "Analyze the incident report"})

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    list_response = client.get("/runs")
    assert list_response.status_code == 200

    items = list_response.json()["items"]
    assert len(items) == 2
    assert items[0]["user_goal"] == "Analyze the incident report"
    assert items[1]["user_goal"] == "Prepare a rollout plan"


def test_get_missing_run_returns_not_found() -> None:
    client = TestClient(app)

    response = client.get("/runs/run_missing")

    assert response.status_code == 404
    assert response.json()["detail"] == "Run run_missing does not exist"


def test_get_run_state_returns_run_snapshot() -> None:
    client = TestClient(app)

    create_response = client.post("/runs", json={"user_goal": "Summarize uploaded documents"})
    run_id = create_response.json()["run_id"]

    state_response = client.get(f"/runs/{run_id}/state")

    assert state_response.status_code == 200
    assert state_response.json()["run_id"] == run_id
