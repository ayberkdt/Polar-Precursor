"""Quasi-dipole latitude and magnetic local time along a track, via apexpy.

Choice (plans/04): quasi-dipole (QD) coordinates from apexpy (Emmert et al.
2010 apex formulation on IGRF), because the reference studies say only
"MLAT/MLT" and QD is the standard choice for ionospheric-thermospheric
work at these altitudes. ``apexpy`` is an optional dependency (extra
``magnetic``); it needs a Fortran build on Windows (recipe in plans/04).

An ``Apex`` object holds one epoch. The field changes slowly, so one epoch
per calendar month is enough (plans/04); ``add_quasi_dipole`` groups the
track by month and sets the epoch to the month's decimal year.

Sidera destination: ``sidera.physics.space_environment.magnetic_coordinates``
(or ``sidera.physics.geomagnetism`` next to the IGRF model).
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def decimal_year(moment: pd.Timestamp) -> float:
    """Calendar year plus the elapsed fraction of that year (UTC)."""
    start = pd.Timestamp(year=moment.year, month=1, day=1, tz="UTC")
    end = pd.Timestamp(year=moment.year + 1, month=1, day=1, tz="UTC")
    return moment.year + (moment - start) / (end - start)


def apexpy_available() -> bool:
    try:
        import apexpy  # noqa: F401
    except ImportError:
        return False
    return True


def _require_apexpy() -> Any:
    try:
        import apexpy
    except ImportError as error:
        raise ImportError(
            "Quasi-dipole coordinates need apexpy (optional extra 'magnetic'); on Windows "
            "it must be built from source, see plans/04."
        ) from error
    return apexpy


def add_quasi_dipole(
    track: pd.DataFrame,
    *,
    latitude: str = "latitude_deg",
    longitude: str = "longitude_deg",
    altitude: str = "altitude_m",
) -> pd.DataFrame:
    """Return ``track`` with ``qd_latitude_deg``, ``qd_longitude_deg`` and ``mlt_h`` added.

    The index must be a UTC DatetimeIndex. Rows with a missing coordinate get
    NaN. The apexpy epoch is set per calendar month to that month's start.
    """
    apexpy = _require_apexpy()
    if not isinstance(track.index, pd.DatetimeIndex) or track.index.tz is None:
        raise ValueError("track must have a tz-aware (UTC) DatetimeIndex.")
    for column in (latitude, longitude, altitude):
        if column not in track.columns:
            raise ValueError(f"track lacks column {column!r}.")
    out = track.copy()
    qd_lat = np.full(len(track), np.nan)
    qd_lon = np.full(len(track), np.nan)
    mlt = np.full(len(track), np.nan)
    positions = np.arange(len(track))
    months = track.index.tz_convert(None).to_period("M")
    for month in months.unique():
        rows = positions[months == month]
        epoch = decimal_year(month.start_time.tz_localize("UTC"))
        apex = apexpy.Apex(date=epoch)
        lat = track[latitude].to_numpy(dtype=np.float64)[rows]
        lon = track[longitude].to_numpy(dtype=np.float64)[rows]
        height_km = track[altitude].to_numpy(dtype=np.float64)[rows] / 1000.0
        present = ~(np.isnan(lat) | np.isnan(lon) | np.isnan(height_km))
        if not present.any():
            continue
        qlat, qlon = apex.geo2qd(lat[present], lon[present], height_km[present])
        qd_lat[rows[present]] = qlat
        qd_lon[rows[present]] = qlon
        times = track.index[rows[present]].tz_convert(None).to_pydatetime()
        mlt[rows[present]] = apex.mlon2mlt(qlon, times)
    out["qd_latitude_deg"] = qd_lat
    out["qd_longitude_deg"] = qd_lon
    out["mlt_h"] = mlt
    out.attrs["magnetic_coordinates"] = f"apexpy {apexpy.__version__} quasi-dipole, monthly epochs"
    return out


__all__ = ["add_quasi_dipole", "apexpy_available", "decimal_year"]
