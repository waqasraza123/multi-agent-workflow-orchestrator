import pytest
from fastapi.testclient import TestClient

from multi_agent_platform.api.dependencies import reset_api_state
from multi_agent_platform.main import app


@pytest.fixture(autouse=True)
def reset_state() -> None:
    reset_api_state()


def test_finalize_endpoint_returns_latest_output() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/runs",
        json={
            "user_goal": "Create a technical delivery plan",
            "workflow_type": "technical_plan",
        },
    )
    run_id = create_response.json()["item"]["run_id"]

    client.post(f"/runs/{run_id}/plan")
    client.post(f"/runs/{run_id}/turns/advance")
    client.post(f"/runs/{run_id}/turns/advance")
    client.post(f"/runs/{run_id}/turns/advance")
    client.post(f"/runs/{run_id}/verify")

    finalize_response = client.post(f"/runs/{run_id}/finalize")
    latest_output = client.get(f"/runs/{run_id}/outputs/latest")
    state_response = client.get(f"/runs/{run_id}/state")

    assert finalize_response.status_code == 200
    assert latest_output.status_code == 200
    assert (
        latest_output.json()["item"]["output_id"] == finalize_response.json()["item"]["output_id"]
    )
    assert state_response.json()["item"]["status"] == "completed"


def test_finalize_without_verification_returns_not_found() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/runs",
        json={
            "user_goal": "Create a technical delivery plan",
            "workflow_type": "technical_plan",
        },
    )
    run_id = create_response.json()["item"]["run_id"]

    client.post(f"/runs/{run_id}/plan")
    client.post(f"/runs/{run_id}/turns/advance")
    client.post(f"/runs/{run_id}/turns/advance")
    client.post(f"/runs/{run_id}/turns/advance")

    finalize_response = client.post(f"/runs/{run_id}/finalize")

    assert finalize_response.status_code == 404


def test_get_latest_output_for_missing_run_returns_not_found() -> None:
    client = TestClient(app)

    response = client.get("/runs/run_missing/outputs/latest")

    assert response.status_code == 404
