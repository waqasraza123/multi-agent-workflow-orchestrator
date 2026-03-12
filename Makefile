.PHONY: bootstrap lint format format-check typecheck test check run-api

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

run-api:
	uv run uvicorn multi_agent_platform.main:app --reload
