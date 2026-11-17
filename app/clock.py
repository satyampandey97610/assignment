"""Application clock providing timezone-aware current time and test overrides."""

from datetime import datetime
from zoneinfo import ZoneInfo

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
_fixed_time: datetime | None = None


def now(tz: ZoneInfo | None = None) -> datetime:
    """Return the current datetime, defaulting to Asia/Kolkata timezone."""
    target_tz = tz or KOLKATA_TZ
    if _fixed_time is not None:
        return _fixed_time.astimezone(target_tz)
    return datetime.now(target_tz)


def set_fixed_now(dt: datetime | None) -> None:
    """Set a fixed time for deterministic testing, or None to reset."""
    global _fixed_time
    _fixed_time = dt
