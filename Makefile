.PHONY: bootstrap lint format format-check typecheck test check smoke-memory smoke-sql release-check

bootstrap:
	uv sync --group dev

lint:
	uv run ruff check .

format:
	uv run ruff format .

format-check:
	uv run ruff format --check .

typecheck:
	uv run mypy src tests

test:
	uv run pytest -q

check:
	$(MAKE) lint
	$(MAKE) format-check
	$(MAKE) typecheck
	$(MAKE) test

smoke-memory:
	uv run python -c 'from fastapi.testclient import TestClient; from multi_agent_platform.api.dependencies import reset_api_state; from multi_agent_platform.main import app; reset_api_state(); client = TestClient(app); created = client.post("/runs", json={"user_goal": "Create a technical delivery plan", "workflow_type": "technical_plan"}); run_id = created.json()["item"]["run_id"]; client.post(f"/runs/{run_id}/plan"); client.post(f"/runs/{run_id}/turns/advance"); client.post(f"/runs/{run_id}/turns/advance"); client.post(f"/runs/{run_id}/turns/advance"); client.post(f"/runs/{run_id}/verify"); finalized = client.post(f"/runs/{run_id}/finalize"); print(finalized.status_code, finalized.json()["item"]["run_id"])'

smoke-sql:
	uv run python -c 'import os; from fastapi.testclient import TestClient; from multi_agent_platform.api.dependencies import reset_api_state; from multi_agent_platform.main import app; os.environ["STORAGE_BACKEND"] = "sql"; os.environ["DATABASE_URL"] = "sqlite:///./.workdir/multi_agent_platform.db"; reset_api_state(); client = TestClient(app); created = client.post("/runs", json={"user_goal": "Create a technical delivery plan", "workflow_type": "technical_plan"}); run_id = created.json()["item"]["run_id"]; client.post(f"/runs/{run_id}/plan"); client.post(f"/runs/{run_id}/turns/advance"); client.post(f"/runs/{run_id}/turns/advance"); client.post(f"/runs/{run_id}/turns/advance"); client.post(f"/runs/{run_id}/verify"); client.post(f"/runs/{run_id}/finalize"); reset_api_state(); persisted = TestClient(app); state = persisted.get(f"/runs/{run_id}/state"); print(state.status_code, state.json()["item"]["status"])'

release-check:
	$(MAKE) check
	$(MAKE) smoke-memory
	$(MAKE) smoke-sql
