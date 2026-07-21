from datetime import UTC, datetime, timedelta


def create_token_expire_at(minutes: int) -> datetime:
    return datetime.now(UTC) + timedelta(minutes=minutes)
