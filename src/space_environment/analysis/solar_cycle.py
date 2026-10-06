"""Solar-cycle context of an epoch: cycle number, phase and smoothed activity.

The sunspot number is used for context only (which cycle, which phase, how
high the smoothed activity), never as a model driver; the models take F10.7
and the SET indices. The phase rule is this project's definition: from the
cycle minimum to its maximum is "rising", from the maximum to the next
cycle's minimum is "declining", with the fraction counted in calendar months
on the SILSO min/max table.

Sidera destination: ``sidera.analysis.space_environment.solar_cycle``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

import numpy as np
import pandas as pd

from space_environment.common.timeutil import require_utc
from space_environment.io.silso import SolarCycle

CyclePhase = Literal["rising", "declining"]


@dataclass(frozen=True, slots=True)
class CycleContext:
    """Where an epoch sits in the solar cycle.

    ``phase_fraction`` runs 0 to 1 from the cycle minimum to its maximum
    (rising) or from the maximum to the next cycle's minimum (declining),
    computed on calendar months.
    """

    cycle: int
    phase: CyclePhase
    phase_fraction: float
    months_since_minimum: int


def _months_between(earlier: datetime, later: datetime) -> int:
    return (later.year - earlier.year) * 12 + (later.month - earlier.month)


def cycle_context(cycles: tuple[SolarCycle, ...], utc: datetime) -> CycleContext:
    """Cycle number and phase for ``utc``; raises outside the tabulated range."""
    moment = require_utc(utc)
    month = moment.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current: SolarCycle | None = None
    following: SolarCycle | None = None
    for index, cycle in enumerate(cycles):
        if cycle.minimum <= month:
            current = cycle
            following = cycles[index + 1] if index + 1 < len(cycles) else None
    if current is None:
        raise ValueError(f"{month.date().isoformat()} is before the first tabulated cycle.")
    if current.maximum is None:
        raise ValueError(
            f"Cycle {current.number} has no tabulated maximum yet; the phase of "
            f"{month.date().isoformat()} cannot be stated."
        )
    since_minimum = _months_between(current.minimum, month)
    if month < current.maximum:
        rise = _months_between(current.minimum, current.maximum)
        return CycleContext(current.number, "rising", since_minimum / rise, since_minimum)
    if following is None:
        raise ValueError(
            f"Cycle {current.number} is past maximum but the next minimum is not tabulated; "
            f"the declining-phase fraction of {month.date().isoformat()} cannot be stated."
        )
    decline = _months_between(current.maximum, following.minimum)
    since_maximum = _months_between(current.maximum, month)
    return CycleContext(current.number, "declining", since_maximum / decline, since_minimum)


def smoothed_sunspot_number(smoothed: pd.DataFrame, utc: datetime) -> float:
    """The 13-month smoothed number of the month containing ``utc`` (NaN if absent)."""
    moment = require_utc(utc)
    month = pd.Timestamp(moment.replace(day=1, hour=0, minute=0, second=0, microsecond=0))
    position = int(smoothed.index.get_indexer(pd.DatetimeIndex([month]))[0])
    if position < 0:
        return float("nan")
    return float(smoothed["sunspot_number"].to_numpy(dtype=np.float64)[position])


__all__ = ["CycleContext", "CyclePhase", "cycle_context", "smoothed_sunspot_number"]
