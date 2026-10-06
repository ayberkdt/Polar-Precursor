"""Index conventions that thermosphere models expect.

These are small functions, but each encodes a convention that produces a
plausible, wrong density when it is off by one day or one 3-hour slot.

NRLMSIS inputs, as documented by pymsis and by Sidera's NRLMSIS adapter
(model description: Emmert et al. 2021, doi:10.1029/2020EA001321):

* daily F10.7 **of the previous day**,
* 81-day mean of F10.7 **centred** on the day,
* a 7-slot Ap array: daily Ap; the 3-hourly ap of the current interval; the ap
  3, 6 and 9 h earlier; the mean of the eight 3-hourly ap from 12 to 33 h
  earlier; the mean of the eight from 36 to 57 h earlier.

The slot indexing below was checked against ``pymsis.utils`` (pymsis 0.13.0),
which builds the same array from the CelesTrak file.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timedelta

import numpy as np

from space_environment.common.timeutil import require_utc, utc_day
from space_environment.io.gfz import GfzDailyTable

THREE_HOURS = timedelta(hours=3)
F107_AVERAGE_WINDOW_DAYS = 81


def centred_mean_f107(
    f107_by_day: Mapping[datetime, float | None],
    day: datetime,
    *,
    window_days: int = F107_AVERAGE_WINDOW_DAYS,
    min_valid_fraction: float = 0.9,
) -> float:
    """Arithmetic mean of daily F10.7 over ``window_days`` centred on ``day``.

    For the default 81 days this is day-40 through day+40. Missing days are
    left out of the mean; if fewer than ``min_valid_fraction`` of the window is
    present the function raises, because a centred mean built from one side of
    the window is a different quantity.
    """
    if window_days < 1 or window_days % 2 == 0:
        raise ValueError("window_days must be a positive odd number so the window has a centre.")
    centre = utc_day(day)
    half = window_days // 2
    values = [
        value
        for offset in range(-half, half + 1)
        if (value := f107_by_day.get(centre + timedelta(days=offset))) is not None
    ]
    if len(values) < min_valid_fraction * window_days:
        raise ValueError(
            f"Only {len(values)} of {window_days} daily F10.7 values are available around "
            f"{centre.date().isoformat()}; the centred mean is not defined on that basis."
        )
    return sum(values) / len(values)


def three_hourly_ap(table: GfzDailyTable) -> dict[datetime, int | None]:
    """Map the start of every 3-hour UT interval to its ap."""
    series: dict[datetime, int | None] = {}
    for record in table.records:
        for slot, value in enumerate(record.ap):
            series[record.day + slot * THREE_HOURS] = value
    return series


def nrlmsis_ap_history(
    ap_by_interval: Mapping[datetime, int | None], utc: datetime
) -> tuple[float, float, float, float, float, float]:
    """The six storm-mode Ap slots (NRLMSIS array elements 1-6) at ``utc``.

    Raises if any of the twenty 3-hourly values involved is missing: padding
    would model a quiet magnetosphere during a storm.
    """
    moment = require_utc(utc)
    current = utc_day(moment) + (moment.hour // 3) * THREE_HOURS

    def value(steps_back: int) -> float:
        key = current - steps_back * THREE_HOURS
        ap = ap_by_interval.get(key)
        if ap is None:
            raise ValueError(
                f"3-hourly ap for the interval starting {key.isoformat()} is missing; "
                f"the NRLMSIS Ap history at {moment.isoformat()} cannot be built."
            )
        return float(ap)

    mean_12_33 = sum(value(steps) for steps in range(4, 12)) / 8.0
    mean_36_57 = sum(value(steps) for steps in range(12, 20)) / 8.0
    return (value(0), value(1), value(2), value(3), mean_12_33, mean_36_57)


#: Daily F10.7 more than this factor above the median of its neighbours is a
#: solar radio burst, not solar activity (Tapping 2013 describes the burst
#: contamination of noon values). Measured in the GFZ file for 2001-2015:
#: 12 days exceed 1.5x the 7-day median, up to 938.6 sfu on 2011-03-07; four of
#: them fall the day before a major storm (2001-04-06, 2003-11-04, 2005-09-09,
#: 2011-03-07) and NRLMSIS returns NaN for such inputs.
F107_BURST_RATIO = 1.5
F107_BURST_WINDOW_DAYS = 7


def screen_f107_bursts(
    f107_by_day: Mapping[datetime, float | None],
    *,
    ratio: float = F107_BURST_RATIO,
    window_days: int = F107_BURST_WINDOW_DAYS,
) -> tuple[dict[datetime, float | None], tuple[datetime, ...]]:
    """Replace burst-contaminated daily F10.7 values by the mean of the nearest clean days.

    A day is flagged when its value exceeds ``ratio`` times the median of the
    other available values within ``window_days`` centred on it. Flagged days
    are replaced by the mean of the nearest unflagged values before and after
    (one side if the other is missing). Returns the cleaned mapping and the
    replaced days, so the substitution can be reported.
    """
    if ratio <= 1.0 or window_days < 3 or window_days % 2 == 0:
        raise ValueError("ratio must exceed 1 and window_days be an odd number of at least 3.")
    days = sorted(f107_by_day)
    values = {day: f107_by_day[day] for day in days}
    half = window_days // 2
    flagged: list[datetime] = []
    for day in days:
        value = values[day]
        if value is None:
            continue
        neighbours = [
            v
            for offset in range(-half, half + 1)
            if offset != 0 and (v := values.get(day + timedelta(days=offset))) is not None
        ]
        if len(neighbours) >= 2 and value > ratio * float(np.median(neighbours)):
            flagged.append(day)
    flagged_set = set(flagged)
    cleaned = dict(values)
    for day in flagged:
        before = next(
            (
                values[d]
                for d in reversed(days)
                if d < day and d not in flagged_set and values[d] is not None
            ),
            None,
        )
        after = next(
            (values[d] for d in days if d > day and d not in flagged_set and values[d] is not None),
            None,
        )
        clean = [v for v in (before, after) if v is not None]
        cleaned[day] = float(np.mean(clean)) if clean else None
    return cleaned, tuple(flagged)


__all__ = [
    "F107_BURST_RATIO",
    "F107_BURST_WINDOW_DAYS",
    "screen_f107_bursts",
    "F107_AVERAGE_WINDOW_DAYS",
    "THREE_HOURS",
    "centred_mean_f107",
    "nrlmsis_ap_history",
    "three_hourly_ap",
]
