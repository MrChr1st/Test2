from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

MOSCOW_TZ = timezone(timedelta(hours=3))

def to_moscow(dt: Any):
    if dt is None:
        return None
    if not isinstance(dt, datetime):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(MOSCOW_TZ)

def format_moscow(dt: Any, fmt: str = "%d.%m.%Y %H:%M") -> str:
    if dt is None:
        return ""
    if isinstance(dt, datetime):
        return to_moscow(dt).strftime(fmt)
    return str(dt)

def now_moscow_str(fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    return datetime.now(MOSCOW_TZ).strftime(fmt)
