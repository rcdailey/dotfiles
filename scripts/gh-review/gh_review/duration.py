"""Parse relative duration strings into datetime offsets."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone

_DURATION_RE = re.compile(r"^(\d+)\s*([mhdw])$", re.IGNORECASE)

_UNITS: dict[str, str] = {
    "m": "minutes",
    "h": "hours",
    "d": "days",
    "w": "weeks",
}


def parse_duration(value: str) -> datetime:
    """Parse a relative duration (e.g. '1h', '2d', '1w') into a UTC datetime.

    Returns a datetime representing 'now minus duration'.
    """
    m = _DURATION_RE.match(value.strip())
    if not m:
        raise ValueError(f"invalid duration: {value!r} (expected format: 30m, 1h, 2d, 1w)")
    amount = int(m.group(1))
    unit = _UNITS[m.group(2).lower()]
    delta = timedelta(**{unit: amount})
    return datetime.now(timezone.utc) - delta
