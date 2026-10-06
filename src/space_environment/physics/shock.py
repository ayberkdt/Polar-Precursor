"""Interplanetary shock flag from 1-minute solar-wind data.

A forward shock at the bow-shock nose shows as a simultaneous step in flow
speed, field magnitude and proton density. On OMNI data around the
Richardson-Cane disturbance times (read 2026-10-06): 28 Oct 2003 02:03-02:04
UT, speed 489 to 570 km/s, |B| 9.8 to 15.7 nT, density 1.0 to 1.4 cm^-3 at
first and 4.0 four minutes later; 7 Nov 2004 18:27-18:31 UT, 493 to 643 km/s,
|B| 24.7 to 47.8 nT, density 12 to 29; 24 Aug 2005 06:09-06:13, 476 to 550
km/s, |B| 14 to 22.7 nT, density 11 to 20; 24 Nov 2001 05:51-05:59, 506 to
895 km/s, |B| 8.8 to 33.6 nT, density 7 to 24.

Rule: at each minute compare the median of the ``before_min`` minutes before
it with the median of the ``after_min`` minutes starting at it. A minute is
flagged when the speed rises by at least ``min_speed_jump_km_s`` and both
|B| and density rise by the given ratios. Flagged minutes closer than
``merge_min`` are one candidate, timed at the first flagged minute.

The detector looks ``after_min`` minutes ahead, so a shock is only *known*
at ``confirmed_at = time + after_min``; forecast features must use
``hours_since_last_shock`` with that rule, never the raw shock time. The
thresholds are this project's choice, calibrated on the four events above.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class ShockCandidate:
    time: pd.Timestamp
    confirmed_at: pd.Timestamp
    speed_jump_km_s: float
    b_ratio: float
    density_ratio: float


def _require_minute_index(frame: pd.DataFrame) -> None:
    index = frame.index
    if not isinstance(index, pd.DatetimeIndex) or len(index) < 2:
        raise ValueError("frame must have a DatetimeIndex with at least two samples.")
    steps = np.diff(index.to_numpy())
    if not np.all(steps == np.timedelta64(60, "s")):
        raise ValueError("frame must be regularly sampled at 1 minute (gaps as NaN).")


def _before_after_medians(
    series: pd.Series, before_min: int, after_min: int, min_valid_fraction: float
) -> tuple[pd.Series, pd.Series]:
    min_before = max(int(np.ceil(min_valid_fraction * before_min)), 1)
    min_after = max(int(np.ceil(min_valid_fraction * after_min)), 1)
    before = series.rolling(before_min, min_periods=min_before).median().shift(1)
    after = series.iloc[::-1].rolling(after_min, min_periods=min_after).median().iloc[::-1]
    return before, after


def detect_shocks(
    frame: pd.DataFrame,
    *,
    before_min: int = 10,
    after_min: int = 10,
    min_speed_jump_km_s: float = 40.0,
    min_b_ratio: float = 1.3,
    min_density_ratio: float = 1.3,
    min_valid_fraction: float = 0.5,
    merge_min: float = 30.0,
) -> tuple[ShockCandidate, ...]:
    """Shock candidates in a 1-minute frame with ``flow_speed_km_s``,
    ``b_magnitude_nt`` and ``proton_density_cm3``."""
    _require_minute_index(frame)
    for column in ("flow_speed_km_s", "b_magnitude_nt", "proton_density_cm3"):
        if column not in frame.columns:
            raise ValueError(f"frame lacks column {column!r}.")
    if before_min < 1 or after_min < 1:
        raise ValueError("before_min and after_min must be at least 1 minute.")
    if min_b_ratio <= 0.0 or min_density_ratio <= 0.0 or min_speed_jump_km_s < 0.0:
        raise ValueError("ratios must be positive and the speed jump non-negative.")

    speed_before, speed_after = _before_after_medians(
        frame["flow_speed_km_s"], before_min, after_min, min_valid_fraction
    )
    b_before, b_after = _before_after_medians(
        frame["b_magnitude_nt"], before_min, after_min, min_valid_fraction
    )
    n_before, n_after = _before_after_medians(
        frame["proton_density_cm3"], before_min, after_min, min_valid_fraction
    )
    speed_jump = speed_after - speed_before
    with np.errstate(divide="ignore", invalid="ignore"):
        b_ratio = b_after / b_before
        n_ratio = n_after / n_before
    flagged = (
        (speed_jump >= min_speed_jump_km_s)
        & (b_ratio >= min_b_ratio)
        & (n_ratio >= min_density_ratio)
    ).to_numpy()

    merge = pd.Timedelta(merge_min, unit="m")
    confirm = pd.Timedelta(after_min, unit="m")
    candidates: list[ShockCandidate] = []
    group_start: int | None = None
    group_last: int | None = None
    for raw_position in np.flatnonzero(flagged):
        position = int(raw_position)
        if group_last is not None and frame.index[position] - frame.index[group_last] <= merge:
            group_last = position
            continue
        if group_start is not None and group_last is not None:
            candidates.append(
                _summarise(frame, group_start, group_last, speed_jump, b_ratio, n_ratio, confirm)
            )
        group_start = group_last = position
    if group_start is not None and group_last is not None:
        candidates.append(
            _summarise(frame, group_start, group_last, speed_jump, b_ratio, n_ratio, confirm)
        )
    return tuple(candidates)


def _summarise(
    frame: pd.DataFrame,
    start: int,
    last: int,
    speed_jump: pd.Series,
    b_ratio: pd.Series,
    n_ratio: pd.Series,
    confirm: pd.Timedelta,
) -> ShockCandidate:
    window = slice(start, last + 1)
    return ShockCandidate(
        time=frame.index[start],
        confirmed_at=frame.index[start] + confirm,
        speed_jump_km_s=float(np.nanmax(speed_jump.iloc[window])),
        b_ratio=float(np.nanmax(b_ratio.iloc[window])),
        density_ratio=float(np.nanmax(n_ratio.iloc[window])),
    )


def hours_since_last_shock(shocks: tuple[ShockCandidate, ...], at: pd.Timestamp) -> float:
    """Hours from the latest shock that was already confirmed at ``at``; NaN if none."""
    known = [shock for shock in shocks if shock.confirmed_at <= at]
    if not known:
        return float("nan")
    latest = max(known, key=lambda shock: shock.time)
    return (at - latest.time) / pd.Timedelta(1, unit="h")


__all__ = ["ShockCandidate", "detect_shocks", "hours_since_last_shock"]
