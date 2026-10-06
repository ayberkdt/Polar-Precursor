"""Space-weather providers and index conventions for thermosphere models.

This is the module that merges into ``sidera.physics.atmosphere.space_weather``.
``IndexState`` and ``GfzIndexProvider.get`` deliberately mirror the field
names and call shape of Sidera's ``SpaceWeatherState`` / ``SpaceWeatherProvider``,
so the provider can drive Sidera's NRLMSIS adapter through
``space_environment.integration.sidera`` without either package importing
the other at module load.

What this adds over Sidera's daily CSV provider:

- the 3-hourly Ap history, so NRLMSIS storm-time mode can be driven by
  measured indices (Sidera's ``TimeSeriesSpaceWeatherProvider`` never fills
  ``ap_history``);
- the F10.7 conventions (previous day, centred 81-day mean) applied from the
  raw observed flux instead of being expected pre-computed in the input file;
- a prescribed quiet geomagnetic state at the measured solar flux, the
  storm-free reference atmosphere;
- the JB2008 input convention (which day's SOLFSMY row and which DTCFILE
  hour an epoch consumes), ready for a JB2008 atmosphere adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, Protocol

import numpy as np
import pandas as pd

from space_environment.common.timeutil import require_utc, utc_day
from space_environment.io.gfz import GfzDailyRecord, GfzDailyTable, read_gfz_daily
from space_environment.physics.index_conventions import (
    centred_mean_f107,
    nrlmsis_ap_history,
    screen_f107_bursts,
    three_hourly_ap,
)

GeomagneticMode = Literal["measured", "quiet"]

#: Ap value of the prescribed quiet state. With every slot at 4, NRLMSIS 2.1
#: returned exactly the density it gives with its geomagnetic switches off, on
#: real CHAMP tracks at both high and low solar flux (measured 2026-10-05; see
#: plans/kanit/gercek_iz_kontrol_cikti_2026-10-05.txt).
QUIET_AP: float = 4.0


@dataclass(frozen=True, slots=True)
class IndexState:
    """Solar and geomagnetic indices at one epoch, with their origin.

    ``f107`` is the previous day's observed flux and ``f107a`` the centred
    81-day mean, both in sfu. ``ap_history`` holds the six NRLMSIS storm-mode
    slots.
    """

    f107: float
    f107a: float
    ap_daily: float
    ap_history: tuple[float, float, float, float, float, float] | None
    kp: float | None
    source: str

    def nrlmsis_ap_array(self, *, storm_mode: bool) -> tuple[float, ...]:
        """The 7-element Ap array NRLMSIS consumes (same rule as Sidera's state)."""
        if not storm_mode:
            return (self.ap_daily,) * 7
        if self.ap_history is None:
            raise ValueError("Storm-time mode needs the six 3-hourly Ap slots; none are present.")
        return (self.ap_daily, *self.ap_history)


@dataclass(frozen=True, slots=True)
class GfzIndexProvider:
    """Indices at any UTC epoch covered by a GFZ daily table.

    ``geomagnetic="measured"`` returns the published Ap, Kp and Ap history.
    ``geomagnetic="quiet"`` keeps the measured solar flux but prescribes
    Ap = 4 in every slot: the storm-free reference atmosphere at the real
    solar-activity level. The returned ``source`` says which one was used.
    """

    table: GfzDailyTable
    geomagnetic: GeomagneticMode = "measured"
    f107_burst_screen: bool = True  # replace radio-burst days (see index_conventions)
    f107_replaced_days: tuple[datetime, ...] = field(init=False, repr=False, compare=False)
    _by_day: dict[datetime, GfzDailyRecord] = field(init=False, repr=False, compare=False)
    _f107: dict[datetime, float | None] = field(init=False, repr=False, compare=False)
    _ap3h: dict[datetime, int | None] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.geomagnetic not in ("measured", "quiet"):
            raise ValueError("geomagnetic must be 'measured' or 'quiet'.")
        by_day = self.table.by_day()
        object.__setattr__(self, "_by_day", by_day)
        f107: dict[datetime, float | None] = {
            day: record.f107_obs_sfu for day, record in by_day.items()
        }
        replaced: tuple[datetime, ...] = ()
        if self.f107_burst_screen:
            f107, replaced = screen_f107_bursts(f107)
        object.__setattr__(self, "_f107", f107)
        object.__setattr__(self, "f107_replaced_days", replaced)
        object.__setattr__(self, "_ap3h", three_hourly_ap(self.table))

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        *,
        geomagnetic: GeomagneticMode = "measured",
        f107_burst_screen: bool = True,
    ) -> GfzIndexProvider:
        return cls(
            table=read_gfz_daily(path),
            geomagnetic=geomagnetic,
            f107_burst_screen=f107_burst_screen,
        )

    @property
    def f107_source(self) -> str:
        if not self.f107_burst_screen:
            return "F10.7 observed, no burst screen"
        return f"F10.7 observed, burst screen replaced {len(self.f107_replaced_days)} days"

    def get(self, utc: datetime) -> IndexState:
        moment = require_utc(utc)
        day = utc_day(moment)
        record = self._by_day.get(day)
        if record is None:
            raise ValueError(
                f"No GFZ record for {day.date().isoformat()} in {self.table.source!r} "
                f"(covers {self.table.first_day.date().isoformat()} to "
                f"{self.table.last_day.date().isoformat()})."
            )
        previous = self._f107.get(day - timedelta(days=1))
        if previous is None:
            raise ValueError(
                f"Observed F10.7 for {(day - timedelta(days=1)).date().isoformat()} is "
                "missing; NRLMSIS takes the previous day's flux and none is substituted."
            )
        f107a = centred_mean_f107(self._f107, day)

        if self.geomagnetic == "quiet":
            return IndexState(
                f107=previous,
                f107a=f107a,
                ap_daily=QUIET_AP,
                ap_history=(QUIET_AP,) * 6,
                kp=None,
                source=f"{self.table.source} [F10.7 measured; Ap prescribed quiet = {QUIET_AP:g}]",
            )

        if record.ap_daily is None:
            raise ValueError(f"Daily Ap for {day.date().isoformat()} is missing.")
        kp = record.kp[moment.hour // 3]
        return IndexState(
            f107=previous,
            f107a=f107a,
            ap_daily=float(record.ap_daily),
            ap_history=nrlmsis_ap_history(self._ap3h, moment),
            kp=kp,
            source=self.table.source,
        )


class IndexProvider(Protocol):
    """Anything that answers ``get(utc) -> IndexState`` (the Sidera provider shape)."""

    def get(self, utc: datetime) -> IndexState: ...


@dataclass(frozen=True, slots=True)
class QuietGeomagneticProvider:
    """Wrap any provider so its geomagnetic state is the prescribed quiet level.

    Solar flux passes through unchanged; Ap becomes ``quiet_ap`` in the daily
    value and every history slot, Kp is dropped, and the source string says
    so. This is the storm-free reference atmosphere for any index source,
    which is the form that fits Sidera: it wraps ``TimeSeriesSpaceWeatherProvider``
    as well as ``GfzIndexProvider`` (whose ``geomagnetic="quiet"`` flag gives
    the same result; see the tests).
    """

    inner: IndexProvider
    quiet_ap: float = QUIET_AP

    def __post_init__(self) -> None:
        if not 0.0 <= self.quiet_ap <= 400.0:
            raise ValueError("quiet_ap must lie in the Ap range [0, 400].")

    def get(self, utc: datetime) -> IndexState:
        state = self.inner.get(utc)
        return IndexState(
            f107=state.f107,
            f107a=state.f107a,
            ap_daily=self.quiet_ap,
            ap_history=(self.quiet_ap,) * 6,
            kp=None,
            source=f"{state.source} [F10.7 measured; Ap prescribed quiet = {self.quiet_ap:g}]",
        )


# ---------------------------------------------------------------------------
# JB2008 input convention (SET SOLFSMY / DTCFILE)
# ---------------------------------------------------------------------------

#: Days of lag JB2008 applies to each index (SOLFSMY header, read 2026-10-06).
JB2008_LAG_DAYS: dict[str, int] = {"f10": 1, "s10": 1, "m10": 2, "y10": 5}


@dataclass(frozen=True, slots=True)
class Jb2008SolarInputs:
    """The eight solar inputs of JB2008 for one epoch, lags already applied."""

    f10: float
    f10b: float
    s10: float
    s10b: float
    m10: float
    m10b: float
    y10: float
    y10b: float
    source: str


def _value_on(frame: pd.DataFrame, when: datetime, column: str) -> float:
    """Scalar float at an index label (the label must exist)."""
    position = int(frame.index.get_indexer(pd.DatetimeIndex([when]))[0])
    return float(frame[column].to_numpy(dtype=np.float64)[position])


def jb2008_solar_inputs(table: pd.DataFrame, utc: datetime) -> Jb2008SolarInputs:
    """Lagged SOLFSMY values for ``utc`` (F10/S10 -1 d, M10 -2 d, Y10 -5 d).

    ``table`` is the frame of ``space_environment.io.set_jb2008.read_solfsmy``.
    A missing lagged value raises: JB2008 has no defined behaviour for a
    missing index and nothing is substituted here.
    """
    day = utc_day(require_utc(utc))
    picked: dict[str, float] = {}
    for name, lag in JB2008_LAG_DAYS.items():
        lagged_day = day - timedelta(days=lag)
        if lagged_day not in table.index:
            raise ValueError(
                f"SOLFSMY has no row for {lagged_day.date().isoformat()} "
                f"({name.upper()} lagged {lag} d from {day.date().isoformat()})."
            )
        daily = _value_on(table, lagged_day, f"{name}_sfu")
        centred = _value_on(table, lagged_day, f"{name[0]}81c_sfu")
        if np.isnan(daily) or np.isnan(centred):
            raise ValueError(
                f"{name.upper()} for {lagged_day.date().isoformat()} is spline-filled or "
                "missing (source flag 0); not substituted."
            )
        picked[name] = daily
        picked[name + "b"] = centred
    return Jb2008SolarInputs(
        f10=picked["f10"],
        f10b=picked["f10b"],
        s10=picked["s10"],
        s10b=picked["s10b"],
        m10=picked["m10"],
        m10b=picked["m10b"],
        y10=picked["y10"],
        y10b=picked["y10b"],
        source=str(table.attrs.get("source", "")),
    )


def dtc_at(series: pd.Series, utc: datetime, *, interpolate: bool = False) -> float:
    """dTc for ``utc`` from the hourly series of ``io.set_jb2008.read_dtcfile``.

    ``interpolate=False`` returns the value of the UT hour containing ``utc``.
    ``interpolate=True`` follows the convention of the independent pyatmos
    implementation (read 2026-10-06): hourly value k holds at k:30 UT and the
    series is linear in between, so a time before 00:30 uses the previous day
    and after 23:30 the next day. Either way a missing hour raises.
    """
    moment = pd.Timestamp(require_utc(utc))
    values = series.to_numpy(dtype=np.float64)
    if not interpolate:
        hour = moment.floor("h")
        position = int(series.index.get_indexer(pd.DatetimeIndex([hour]))[0])
        if position < 0:
            raise ValueError(f"DTCFILE has no value for the hour starting {hour.isoformat()}.")
        return float(values[position])
    half = pd.Timedelta(30, unit="m")
    earlier = (moment - half).floor("h")
    later = earlier + pd.Timedelta(1, unit="h")
    positions = series.index.get_indexer(pd.DatetimeIndex([earlier, later]))
    if (positions < 0).any():
        raise ValueError(
            f"DTCFILE lacks the hours {earlier.isoformat()} and/or {later.isoformat()} "
            "needed to interpolate."
        )
    fraction = (moment - (earlier + half)) / pd.Timedelta(1, unit="h")
    first, second = values[positions[0]], values[positions[1]]
    return float(first + fraction * (second - first))


__all__ = [
    "JB2008_LAG_DAYS",
    "QUIET_AP",
    "GeomagneticMode",
    "GfzIndexProvider",
    "IndexProvider",
    "IndexState",
    "Jb2008SolarInputs",
    "QuietGeomagneticProvider",
    "dtc_at",
    "jb2008_solar_inputs",
]
