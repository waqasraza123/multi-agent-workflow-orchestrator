from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _path_exists(root: Path, relative: str) -> bool:
    return (root / relative).exists()


def test_repo_has_pyproject_toml() -> None:
    root = _repo_root()
    assert _path_exists(root, "pyproject.toml")


def test_repo_has_python_version_pin() -> None:
    root = _repo_root()
    assert _path_exists(root, ".python-version")


def test_repo_has_env_example() -> None:
    root = _repo_root()
    assert _path_exists(root, ".env.example")


def test_repo_has_docs_and_toolchain_baseline() -> None:
    root = _repo_root()
    assert (root / "docs").is_dir()
    assert _path_exists(root, "docs/toolchain-baseline.md")


def test_repo_has_tests_structure() -> None:
    root = _repo_root()
    assert (root / "tests").is_dir()
    assert (root / "tests" / "unit").is_dir()


def test_repo_has_key_foundation_files() -> None:
    root = _repo_root()
    required = ["README.md", ".gitignore", "pyproject.toml"]
    for name in required:
        assert _path_exists(root, name), f"Missing required file: {name}"
