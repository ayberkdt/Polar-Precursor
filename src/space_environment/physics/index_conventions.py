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


__all__ = [
    "F107_AVERAGE_WINDOW_DAYS",
    "THREE_HOURS",
    "centred_mean_f107",
    "nrlmsis_ap_history",
    "three_hourly_ap",
]
