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
    ]
    for relative_path in required_files:
        assert relative_path_exists(relative_pathMissing required file: {relative_path}"


def test_foundation_directories_exist() -> None:
    required_directories = [
        ".github",
        ".github/workflows",
        "apps",
        "docs",
        "infra",
        "packages",
        "services",
        "tests",
        "tests/unit",
    ]
    for relative_path in required_directories:
        assert (repo_root() / relative_path).is_dir(), f"Missing required directory: {relative_path}"
