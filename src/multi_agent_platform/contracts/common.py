from datetime import UTC, datetime
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def generate_identifier(prefix: str) -> str:
    cleaned_prefix = prefix.strip()
    if not cleaned_prefix:
        raise ValueError("Identifier prefix must not be blank")
    return f"{cleaned_prefix}_{uuid4().hex}"
