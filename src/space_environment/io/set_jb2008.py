"""Readers for the JB2008 driver-index files of Space Environment Technologies.

Two files from ``https://sol.spacenvironment.net/JB2008/indices/``:

``SOLFSMY.TXT``
    Daily F10, S10, M10, Y10 and their 81-day centred means, from 1997. The
    file header (read 2026-10-06, release 8_1_0) states: all values are
    reported in sfu at 12 UT and should be used as a daily value for the
    calendar date; in JB2008 F10 and S10 are 1-day lagged, M10 2-day and Y10
    5-day lagged, and the 81-day centred values use the same lags. ``Ssrc``
    holds one source character per index (0 = spline-filled or missing).
``DTCFILE.TXT``
    Lines ``DTC YYYY DDD`` followed by 24 values, one per hour of the UT day.
    The file has no header. That the values are the JB2008 temperature
    correction dTc in kelvin is the usual JB2008 convention and was **not**
    verified from a primary document in this project. The hour mapping was
    checked against an independent implementation (pyatmos 1.2.7, read
    2026-10-06): it reads the same 24 columns, takes value k as valid at
    k:30 UT and interpolates linearly, and hands the result to the JB2008
    kernel as ``DSTDTC``. ``read_dtcfile`` stamps value k at k:00 (start of
    the hour); ``physics.space_weather.dtc_at(..., interpolate=True)``
    reproduces the pyatmos reading.

The lag convention itself (which day's value JB2008 consumes at an epoch)
lives in ``space_environment.physics.space_weather``.

Sidera destination: ``sidera.io.space_weather.set_jb2008``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from space_environment.common.provenance import source_label

SOLFSMY_COLUMNS: tuple[str, ...] = (
    "f10_sfu",
    "f81c_sfu",
    "s10_sfu",
    "s81c_sfu",
    "m10_sfu",
    "m81c_sfu",
    "y10_sfu",
    "y81c_sfu",
)


def _day_from_year_doy(year: int, day_of_year: int) -> datetime:
    return datetime(year, 1, 1, tzinfo=timezone.utc) + timedelta(days=day_of_year - 1)


def read_solfsmy(path: str | Path) -> pd.DataFrame:
    """Daily SOLFSMY table indexed by UTC day, values in sfu.

    Columns: ``f10_sfu, f81c_sfu, s10_sfu, s81c_sfu, m10_sfu, m81c_sfu,
    y10_sfu, y81c_sfu`` and ``source_flags`` (the four ``Ssrc`` characters,
    in the order F10, S10, M10, Y10). Indices whose source flag is ``0`` are
    spline-filled or missing in the file and are set to NaN here.
    """
    file_path = Path(path)
    rows: list[tuple[datetime, list[float], str]] = []
    with file_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            fields = line.split()
            if len(fields) != 12:
                raise ValueError(
                    f"{file_path.name} line {line_number}: expected 12 fields, got {len(fields)}."
                )
            try:
                day = _day_from_year_doy(int(fields[0]), int(fields[1]))
                values = [float(field) for field in fields[3:11]]
            except ValueError as error:
                raise ValueError(f"{file_path.name} line {line_number}: {error}") from error
            flags = fields[11]
            if len(flags) != 4:
                raise ValueError(
                    f"{file_path.name} line {line_number}: Ssrc must have 4 characters, "
                    f"got {flags!r}."
                )
            rows.append((day, values, flags))
    if not rows:
        raise ValueError(f"{file_path.name}: no data rows.")
    index = pd.DatetimeIndex([row[0] for row in rows], name="day_utc")
    if not index.is_monotonic_increasing or index.has_duplicates:
        raise ValueError(f"{file_path.name}: days are not strictly increasing.")
    frame = pd.DataFrame([row[1] for row in rows], index=index, columns=list(SOLFSMY_COLUMNS))
    frame["source_flags"] = [row[2] for row in rows]
    for position, name in enumerate(("f", "s", "m", "y")):
        missing = frame["source_flags"].str[position] == "0"
        frame.loc[missing, [f"{name}10_sfu", f"{name}81c_sfu"]] = np.nan
    frame.attrs["source"] = source_label(file_path)
    return frame


def read_dtcfile(path: str | Path) -> pd.Series:
    """Hourly dTc series indexed by the start of each UT hour (see module note)."""
    file_path = Path(path)
    times: list[datetime] = []
    values: list[float] = []
    with file_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, start=1):
            fields = line.split()
            if not fields:
                continue
            if fields[0] != "DTC" or len(fields) != 27:
                raise ValueError(
                    f"{file_path.name} line {line_number}: expected 'DTC YYYY DDD' and 24 "
                    f"hourly values, got {len(fields)} fields."
                )
            try:
                day = _day_from_year_doy(int(fields[1]), int(fields[2]))
                hourly = [float(field) for field in fields[3:]]
            except ValueError as error:
                raise ValueError(f"{file_path.name} line {line_number}: {error}") from error
            times.extend(day + timedelta(hours=hour) for hour in range(24))
            values.extend(hourly)
    if not values:
        raise ValueError(f"{file_path.name}: no data rows.")
    index = pd.DatetimeIndex(times, name="time_utc")
    if not index.is_monotonic_increasing or index.has_duplicates:
        raise ValueError(f"{file_path.name}: hours are not strictly increasing.")
    series = pd.Series(np.asarray(values, dtype=np.float64), index=index, name="dtc_k")
    series.attrs["source"] = source_label(file_path)
    return series


__all__ = ["SOLFSMY_COLUMNS", "read_dtcfile", "read_solfsmy"]
