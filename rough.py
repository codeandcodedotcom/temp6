# app/utils/datetime_utils.py
from datetime import datetime, timezone

def utcnow_naive() -> datetime:
    """
    Returns current UTC time as a timezone-naive datetime.
    Safe for TIMESTAMP WITHOUT TIME ZONE.
    Sonar-safe replacement for utcnow().
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
