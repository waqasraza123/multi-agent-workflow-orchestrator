import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    storage_backend: str
    database_url: str
    execution_backend: str
    llm_provider_name: str
    llm_model_name: str
    llm_api_base_url: str
    llm_api_key: str | None


def _read_storage_backend() -> str:
    value = os.getenv("STORAGE_BACKEND", "memory").strip().lower()
    if value not in {"memory", "sql"}:
        raise ValueError("STORAGE_BACKEND must be either memory or sql")
    return value


def _read_execution_backend() -> str:
    value = os.getenv("EXECUTION_BACKEND", "deterministic").strip().lower()
    if value not in {"deterministic", "llm"}:
        raise ValueError("EXECUTION_BACKEND must be either deterministic or llm")
    return value


def _read_llm_provider_name() -> str:
    value = os.getenv("LLM_PROVIDER_NAME", "fake").strip().lower()
    if not value:
        raise ValueError("LLM_PROVIDER_NAME must not be blank")
    return value


def _read_llm_model_name() -> str:
    value = os.getenv("LLM_MODEL_NAME", "fake-model").strip()
    if not value:
        raise ValueError("LLM_MODEL_NAME must not be blank")
    return value


def _read_llm_api_base_url() -> str:
    value = os.getenv("LLM_API_BASE_URL", "https://api.openai.com/v1").strip()
    if not value:
        raise ValueError("LLM_API_BASE_URL must not be blank")
    return value.rstrip("/")


def _read_optional_env(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    cleaned_value = value.strip()
    return cleaned_value or None


@lru_cache
def get_settings() -> Settings:
    return Settings(
        storage_backend=_read_storage_backend(),
        database_url=os.getenv(
            "DATABASE_URL",
            "sqlite:///./.workdir/multi_agent_platform.db",
        ),
        execution_backend=_read_execution_backend(),
        llm_provider_name=_read_llm_provider_name(),
        llm_model_name=_read_llm_model_name(),
        llm_api_base_url=_read_llm_api_base_url(),
        llm_api_key=_read_optional_env("LLM_API_KEY"),
    )


def reset_settings_cache() -> None:
    get_settings.cache_clear()
