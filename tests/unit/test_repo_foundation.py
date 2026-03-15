from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def relative_path_exists(relative_path: str) -> bool:
    return (repo_root() / relative_path).exists()


def test_foundation_files_exist() -> None:
    required_files = [
        ".editorconfig",
        ".env.example",
        ".gitignore",
        ".github/workflows/ci.yml",
        ".python-version",
        "Makefile",
        "README.md",
        "docs/architecture-overview.md",
        "docs/decision-log.md",
        "docs/execution-charter.md",
        "docs/phase-status.md",
        "docs/toolchain-baseline.md",
        "pyproject.toml",
        "src/multi_agent_platform/agents/__init__.py",
        "src/multi_agent_platform/agents/runtime.py",
        "src/multi_agent_platform/api/app.py",
        "src/multi_agent_platform/api/routes/runs.py",
        "src/multi_agent_platform/application/run_approvals.py",
        "src/multi_agent_platform/application/run_events.py",
        "src/multi_agent_platform/application/run_outputs.py",
        "src/multi_agent_platform/application/run_plans.py",
        "src/multi_agent_platform/application/run_tool_calls.py",
        "src/multi_agent_platform/application/run_turns.py",
        "src/multi_agent_platform/application/run_verifications.py",
        "src/multi_agent_platform/application/run_views.py",
        "src/multi_agent_platform/application/runs.py",
        "src/multi_agent_platform/config/__init__.py",
        "src/multi_agent_platform/config/settings.py",
        "src/multi_agent_platform/contracts/run_approvals.py",
        "src/multi_agent_platform/contracts/run_approval_views.py",
        "src/multi_agent_platform/contracts/run_commands.py",
        "src/multi_agent_platform/contracts/run_event_views.py",
        "src/multi_agent_platform/contracts/run_events.py",
        "src/multi_agent_platform/contracts/run_output_views.py",
        "src/multi_agent_platform/contracts/run_outputs.py",
        "src/multi_agent_platform/contracts/run_plan_views.py",
        "src/multi_agent_platform/contracts/run_plans.py",
        "src/multi_agent_platform/contracts/run_queries.py",
        "src/multi_agent_platform/contracts/run_tool_call_views.py",
        "src/multi_agent_platform/contracts/run_tool_calls.py",
        "src/multi_agent_platform/contracts/run_turn_views.py",
        "src/multi_agent_platform/contracts/run_turns.py",
        "src/multi_agent_platform/contracts/run_verification_views.py",
        "src/multi_agent_platform/contracts/run_verifications.py",
        "src/multi_agent_platform/contracts/run_views.py",
        "src/multi_agent_platform/orchestration/state.py",
        "src/multi_agent_platform/planning/__init__.py",
        "src/multi_agent_platform/planning/templates.py",
        "src/multi_agent_platform/storage/db/__init__.py",
        "src/multi_agent_platform/storage/db/base.py",
        "src/multi_agent_platform/storage/db/models.py",
        "src/multi_agent_platform/storage/db/session.py",
        "src/multi_agent_platform/storage/run_approval_repository.py",
        "src/multi_agent_platform/storage/run_event_repository.py",
        "src/multi_agent_platform/storage/run_output_repository.py",
        "src/multi_agent_platform/storage/run_plan_repository.py",
        "src/multi_agent_platform/storage/run_repository.py",
        "src/multi_agent_platform/storage/run_tool_call_repository.py",
        "src/multi_agent_platform/storage/run_turn_repository.py",
        "src/multi_agent_platform/storage/run_verification_repository.py",
        "src/multi_agent_platform/storage/sql_repository.py",
        "src/multi_agent_platform/tools/__init__.py",
        "src/multi_agent_platform/tools/registry.py",
        "tests/integration/test_sql_persistence.py",
        "tests/unit/agents/test_runtime.py",
        "tests/unit/api/test_run_outputs.py",
        "tests/unit/application/test_run_outputs.py",
        "tests/unit/storage/test_run_output_repository.py",
        "tests/unit/storage/test_run_tool_call_repository.py",
        "tests/unit/tools/test_registry.py",
    ]
    for relative_path in required_files:
        assert relative_path_exists(relative_path), (
            f"Missing required file: {relative_path}"
        )


def test_foundation_directories_exist() -> None:
    required_directories = [
        ".github",
        ".github/workflows",
        "apps",
        "docs",
        "infra",
        "packages",
        "services",
        "src",
        "src/multi_agent_platform",
        "src/multi_agent_platform/agents",
        "src/multi_agent_platform/api",
        "src/multi_agent_platform/api/routes",
        "src/multi_agent_platform/application",
        "src/multi_agent_platform/config",
        "src/multi_agent_platform/contracts",
        "src/multi_agent_platform/orchestration",
        "src/multi_agent_platform/planning",
        "src/multi_agent_platform/storage",
        "src/multi_agent_platform/storage/db",
        "src/multi_agent_platform/tools",
        "tests",
        "tests/integration",
        "tests/unit",
        "tests/unit/agents",
        "tests/unit/api",
        "tests/unit/application",
        "tests/unit/contracts",
        "tests/unit/planning",
        "tests/unit/storage",
        "tests/unit/tools",
    ]
    for relative_path in required_directories:
        assert (repo_root() / relative_path).is_dir(), (
            f"Missing required directory: {relative_path}"
        )
