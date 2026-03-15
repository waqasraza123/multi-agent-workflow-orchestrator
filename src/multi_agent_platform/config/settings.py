import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class Settings:
    storage_backend: str
    database_url: str


def _read_storage_backend() -> str:
    value = os.getenv("STORAGE_BACKEND", "memory").strip().lower()
    if value not in {"memory", "sql"}:
        raise ValueError("STORAGE_BACKEND must be either memory or sql")
    return value


@lru_cache
def get_settings() -> Settings:
    return Settings(
        storage_backend=_read_storage_backend(),
        database_url=os.getenv(
            "DATABASE_URL",
            "sqlite:///./.workdir/multi_agent_platform.db",
        ),
    )


def reset_settings_cache() -> None:
    get_settings.cache_clear()
