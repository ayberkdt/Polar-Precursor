"""Storm-free reference density along a track: NRLMSIS 2.1 with Ap = 4 in every slot.

The thesis target is ``ln(rho_obs / rho_ref)`` per pass (``passes.segment_track``
with ``reference=``). The reference is the empirical model at the satellite's
position with the observed F10.7 (previous day and centred 81-day mean) but
the geomagnetic input fixed at the quiet value, so that the storm response is
what remains (main plan "Referans"; plan 03 measured that Ap = 4 in every slot
is identical to switching the geomagnetic term off).

Two ways to evaluate it implement the same ``ReferenceModel`` protocol:

- ``QuietNrlmsisReference`` calls ``pymsis`` directly and vectorised (one call
  per track). F10.7 comes from an ``IndexProvider``; ``f107s``, ``f107as`` and
  ``aps`` are always passed, so pymsis never downloads anything (its docstring,
  read 2026-10-06: historical data is fetched only when they are omitted).
- ``integration.sidera.SideraReferenceModel`` goes through Sidera's adapter,
  one sample at a time; slower, for cross-checks.

``add_reference_density`` evaluates the model every ``stride`` samples and
interpolates ``ln rho`` linearly in time for the rest. Measured on the 60-s
CHAMP track of 29 Oct 2003 (``tests/test_reference_density.py``): the largest
``|delta ln rho|`` is 0.006 for 2-minute nodes, 0.012 for 3, 0.051 for 6 and
0.13 for 10, growing about quadratically with the spacing. For the 10-s
product a stride of 6 (60-s nodes) is therefore the recommended setting.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.util import find_spec
from typing import Protocol

import numpy as np
import pandas as pd

from space_environment.physics.space_weather import QUIET_AP, IndexProvider

REFERENCE_COLUMN = "reference_density_kg_m3"


class ReferenceModel(Protocol):
    label: str

    def density(
        self,
        times: pd.DatetimeIndex,
        latitude_deg: np.ndarray,
        longitude_deg: np.ndarray,
        altitude_m: np.ndarray,
    ) -> np.ndarray:
        """Mass density in kg/m³ at each aligned (time, position)."""


def pymsis_available() -> bool:
    return find_spec("pymsis") is not None


@dataclass(frozen=True, slots=True)
class QuietNrlmsisReference:
    """NRLMSIS (pymsis) with observed F10.7 and every Ap slot at ``quiet_ap``."""

    provider: IndexProvider
    quiet_ap: float = QUIET_AP
    version: str = "2.1"

    @property
    def label(self) -> str:
        return f"NRLMSIS {self.version} via pymsis, ap={self.quiet_ap:g} in all 7 slots"

    def solar_inputs(self, times: pd.DatetimeIndex) -> tuple[np.ndarray, np.ndarray]:
        """Previous-day F10.7 and centred 81-day mean per sample, from the provider."""
        if times.tz is None:
            raise ValueError("times must be timezone-aware UTC.")
        days = times.tz_convert("UTC").floor("D")
        unique_days = pd.DatetimeIndex(days.unique())
        f107_by_day: dict[pd.Timestamp, float] = {}
        f107a_by_day: dict[pd.Timestamp, float] = {}
        for day in unique_days:
            moment = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
            state = self.provider.get(moment)
            f107_by_day[day] = float(state.f107)
            f107a_by_day[day] = float(state.f107a)
        f107 = np.array([f107_by_day[day] for day in days], dtype=np.float64)
        f107a = np.array([f107a_by_day[day] for day in days], dtype=np.float64)
        return f107, f107a

    def density(
        self,
        times: pd.DatetimeIndex,
        latitude_deg: np.ndarray,
        longitude_deg: np.ndarray,
        altitude_m: np.ndarray,
    ) -> np.ndarray:
        if not pymsis_available():
            raise ImportError("pymsis is not installed (extra 'reference').")
        from pymsis import msis

        n = len(times)
        latitude = np.asarray(latitude_deg, dtype=np.float64)
        longitude = np.asarray(longitude_deg, dtype=np.float64)
        altitude = np.asarray(altitude_m, dtype=np.float64)
        if not (len(latitude) == len(longitude) == len(altitude) == n):
            raise ValueError("times, latitude, longitude and altitude must have equal length.")
        f107, f107a = self.solar_inputs(times)
        aps = np.full((n, 7), self.quiet_ap, dtype=np.float64)
        dates = times.tz_convert("UTC").tz_localize(None).to_numpy()
        out = msis.calculate(
            dates,
            longitude,
            latitude,
            altitude / 1000.0,
            f107,
            f107a,
            aps,
            version=self.version,
            geomagnetic_activity=-1,
        )
        return np.asarray(out[:, 0], dtype=np.float64)


def add_reference_density(
    track: pd.DataFrame,
    model: ReferenceModel,
    *,
    stride: int = 1,
    column: str = REFERENCE_COLUMN,
) -> pd.DataFrame:
    """Copy of ``track`` with the reference density column (see module note on ``stride``)."""
    if stride < 1:
        raise ValueError("stride must be at least 1.")
    for name in ("latitude_deg", "longitude_deg", "altitude_m"):
        if name not in track.columns:
            raise ValueError(f"track lacks column {name!r}.")
    times = track.index
    if not isinstance(times, pd.DatetimeIndex) or times.tz is None:
        raise ValueError("track must be indexed by timezone-aware UTC times.")
    n = len(track)
    latitude = track["latitude_deg"].to_numpy(dtype=np.float64)
    longitude = track["longitude_deg"].to_numpy(dtype=np.float64)
    altitude = track["altitude_m"].to_numpy(dtype=np.float64)
    finite = np.isfinite(latitude) & np.isfinite(longitude) & np.isfinite(altitude)
    picks = np.arange(0, n, stride)
    if picks[-1] != n - 1:
        picks = np.append(picks, n - 1)
    # Records with a missing position (fill values in the product) cannot be
    # evaluated; the reference there is interpolated from the neighbouring
    # nodes, and the observed density at such records is normally flagged
    # invalid anyway. Measured 2026-10-06: a 2001-2015 coverage run hit this.
    picks = picks[finite[picks]]
    if picks.size == 0:
        picks = np.where(finite)[0]
    out = track.copy()
    if picks.size == 0:
        out[column] = np.nan
    else:
        evaluated = model.density(times[picks], latitude[picks], longitude[picks], altitude[picks])
        naive = times.tz_convert("UTC").tz_localize(None).to_numpy()
        seconds = (naive - naive[0]) / np.timedelta64(1, "s")
        log_density = np.interp(seconds, seconds[picks], np.log(evaluated))
        out[column] = np.exp(log_density)
    out.attrs = dict(track.attrs)
    out.attrs["reference_model"] = model.label
    out.attrs["reference_stride"] = stride
    return out


__all__ = [
    "REFERENCE_COLUMN",
    "QuietNrlmsisReference",
    "ReferenceModel",
    "add_reference_density",
    "pymsis_available",
]
