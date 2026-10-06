"""Readers for the SILSO sunspot-number files (WDC-SILSO, Royal Observatory of Belgium).

Files, all from ``https://www.sidc.be/SILSO/DATA/``:

``SN_m_tot_V2.0.txt``
    Monthly mean total sunspot number (version 2.0). Columns: year, month,
    decimal year, monthly mean, standard deviation, number of observations,
    and ``*`` marking provisional months. ``-1`` is a missing value.
``SN_ms_tot_V2.0.txt``
    The 13-month smoothed monthly number in the same layout; the smoothed
    value is missing (-1) for the latest six months.
``Cycles/TableCyclesMiMa.txt``
    Minimum and maximum of each cycle (year, month, smoothed SN) as SILSO
    defines them. Read 2026-10-06: cycle 23 minimum 1996-08 (11.2), maximum
    2001-11 (180.3); cycle 24 minimum 2008-12 (2.2), maximum 2014-04 (116.4);
    cycle 25 minimum 2019-12 (1.8), maximum not yet tabulated.

Sidera destination: ``sidera.io.space_weather.silso``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from space_environment.common.provenance import source_label


def read_silso_monthly(path: str | Path) -> pd.DataFrame:
    """Monthly (or smoothed monthly) SILSO table indexed by the first of each month.

    Columns: ``decimal_year``, ``sunspot_number``, ``standard_deviation``,
    ``observations`` and ``provisional`` (bool). Missing values (-1) are NaN.
    """
    file_path = Path(path)
    rows: list[tuple[datetime, float, float, float, int, bool]] = []
    with file_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, start=1):
            fields = line.split()
            if not fields:
                continue
            if len(fields) not in (6, 7):
                raise ValueError(
                    f"{file_path.name} line {line_number}: expected 6 or 7 fields, "
                    f"got {len(fields)}."
                )
            try:
                month = datetime(int(fields[0]), int(fields[1]), 1, tzinfo=timezone.utc)
                decimal_year = float(fields[2])
                number = float(fields[3])
                deviation = float(fields[4])
                observations = int(fields[5])
            except ValueError as error:
                raise ValueError(f"{file_path.name} line {line_number}: {error}") from error
            provisional = len(fields) == 7 and fields[6] == "*"
            rows.append((month, decimal_year, number, deviation, observations, provisional))
    if not rows:
        raise ValueError(f"{file_path.name}: no data rows.")
    index = pd.DatetimeIndex([row[0] for row in rows], name="month_utc")
    if not index.is_monotonic_increasing or index.has_duplicates:
        raise ValueError(f"{file_path.name}: months are not strictly increasing.")
    frame = pd.DataFrame(
        {
            "decimal_year": [row[1] for row in rows],
            "sunspot_number": [row[2] for row in rows],
            "standard_deviation": [row[3] for row in rows],
            "observations": [row[4] for row in rows],
            "provisional": [row[5] for row in rows],
        },
        index=index,
    )
    for column in ("sunspot_number", "standard_deviation"):
        frame[column] = frame[column].mask(frame[column] < 0.0, np.nan)
    frame.attrs["source"] = source_label(file_path)
    return frame


@dataclass(frozen=True, slots=True)
class SolarCycle:
    """One row of the SILSO min/max table. ``maximum`` is None for an open cycle."""

    number: int
    minimum: datetime
    minimum_sn: float
    maximum: datetime | None
    maximum_sn: float | None


def read_silso_cycle_table(path: str | Path) -> tuple[SolarCycle, ...]:
    """Parse ``TableCyclesMiMa.txt`` (two header lines, then one line per cycle)."""
    file_path = Path(path)
    cycles: list[SolarCycle] = []
    with file_path.open(encoding="ascii") as handle:
        for line_number, line in enumerate(handle, start=1):
            fields = line.split()
            if not fields or not fields[0].isdigit():
                continue
            if len(fields) not in (4, 9):
                raise ValueError(
                    f"{file_path.name} line {line_number}: expected 4 (open cycle) or 9 "
                    f"fields, got {len(fields)}."
                )
            try:
                number = int(fields[0])
                minimum = datetime(int(fields[1]), int(fields[2]), 1, tzinfo=timezone.utc)
                minimum_sn = float(fields[3])
                maximum = maximum_sn = None
                if len(fields) == 9:
                    maximum = datetime(int(fields[4]), int(fields[5]), 1, tzinfo=timezone.utc)
                    maximum_sn = float(fields[6])
            except ValueError as error:
                raise ValueError(f"{file_path.name} line {line_number}: {error}") from error
            cycles.append(SolarCycle(number, minimum, minimum_sn, maximum, maximum_sn))
    if not cycles:
        raise ValueError(f"{file_path.name}: no cycle rows.")
    numbers = [cycle.number for cycle in cycles]
    if numbers != list(range(numbers[0], numbers[0] + len(numbers))):
        raise ValueError(f"{file_path.name}: cycle numbers are not consecutive.")
    return tuple(cycles)


__all__ = ["SolarCycle", "read_silso_cycle_table", "read_silso_monthly"]
