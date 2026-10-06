"""UTC handling shared by the readers and providers."""

from __future__ import annotations

from datetime import datetime, timezone


def require_utc(moment: datetime) -> datetime:
    """Return ``moment`` in UTC, refusing naive datetimes.

    The indices are published on UTC calendar days; a naive datetime would leave
    the time scale ambiguous, so it is rejected rather than assumed.
    """
    if moment.tzinfo is None:
        raise ValueError(
            "Space-environment epochs must be timezone-aware UTC datetimes; a naive "
            "datetime leaves the time scale ambiguous."
        )
    return moment.astimezone(timezone.utc)


def utc_day(moment: datetime) -> datetime:
    """Start of the UTC calendar day containing ``moment``."""
    return require_utc(moment).replace(hour=0, minute=0, second=0, microsecond=0)
