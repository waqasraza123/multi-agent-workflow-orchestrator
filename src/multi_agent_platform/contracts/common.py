from datetime import datetime, timezone
from uuid import uuid4


def utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def generate_identifier(prefix: str) -> str:
    cleaned_prefix = prefix.strip()
    if not cleaned_prefix:
        raise ValueError("Identifier prefix must not be blank")
    return f"{cleaned_prefix}_{uuid4().hex}"
