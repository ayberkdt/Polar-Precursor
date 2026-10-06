"""Readers for the GFZ Potsdam geomagnetic and solar index files.

Two files are covered, both distributed by GFZ under CC BY 4.0 (the sunspot
number column of the daily file is CC BY-NC 4.0):

``Kp_ap_Ap_SN_F107_since_1932.txt``
    One row per UT day: eight Kp, eight 3-hourly ap, daily Ap, sunspot number,
    observed and adjusted F10.7. 40 header lines starting with ``#``.
``Hp30_ap30_complete_series.txt``
    One row per 30 minutes: Hp30 and ap30, from 1985-01-01. 30 header lines.

Missing values are written by GFZ as ``-1.000`` (Kp, Hp30), ``-1`` (ap, Ap, SN,
ap30) and ``-1.0`` (F10.7); they are returned as ``None`` and never as numbers.

Primary sources: Matzka et al. (2021), doi:10.1029/2020SW002641, for Kp/ap;
Yamazaki et al. (2022), doi:10.1029/2022GL098860, for Hp30/ap30.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from space_environment.common.provenance import source_label

_DAILY_FIELD_COUNT = 28
_HPO_FIELD_COUNT = 10


@dataclass(frozen=True, slots=True)
class GfzDailyRecord:
    """Indices for one UT day as listed in the GFZ daily file.

    ``f107_obs_sfu`` is the flux measured at the Earth's actual distance from
    the Sun; ``f107_adj_sfu`` is scaled to 1 AU. Thermosphere models take the
    observed value.
    """

    day: datetime
    kp: tuple[float | None, ...]
    ap: tuple[int | None, ...]
    ap_daily: int | None
    sunspot_number: int | None
    f107_obs_sfu: float | None
    f107_adj_sfu: float | None
    definitive: int


@dataclass(frozen=True, slots=True)
class GfzDailyTable:
    """The parsed daily file: records in date order and where they came from."""

    records: tuple[GfzDailyRecord, ...]
    source: str

    @property
    def first_day(self) -> datetime:
        return self.records[0].day

    @property
    def last_day(self) -> datetime:
        return self.records[-1].day

    def by_day(self) -> dict[datetime, GfzDailyRecord]:
        return {record.day: record for record in self.records}


@dataclass(frozen=True, slots=True)
class HpoRecord:
    """One half-hour interval of the Hp30/ap30 series; ``start`` opens the interval."""

    start: datetime
    hp30: float | None
    ap30: int | None
    definitive: int


def _missing_float(text: str) -> float | None:
    value = float(text)
    return None if value < 0.0 else value


def _missing_int(text: str) -> int | None:
    value = int(text)
    return None if value < 0 else value


def _data_lines(path: Path) -> list[tuple[int, str]]:
    if not path.is_file():
        raise ValueError(f"GFZ index file not found: {path}")
    lines: list[tuple[int, str]] = []
    with path.open("r", encoding="utf-8-sig") as handle:
        for number, raw in enumerate(handle, start=1):
            if raw.startswith("#") or not raw.strip():
                continue
            lines.append((number, raw))
    if not lines:
        raise ValueError(f"{path} holds no data rows.")
    return lines


def read_gfz_daily(path: str | Path) -> GfzDailyTable:
    """Parse ``Kp_ap_Ap_SN_F107`` (full file, yearly file or an excerpt of either).

    Every data row must parse and carry all 28 fields; a malformed row raises
    with its line number rather than being skipped. Rows must be in strictly
    increasing date order, as GFZ publishes them.
    """
    file_path = Path(path).expanduser()
    records: list[GfzDailyRecord] = []
    for number, raw in _data_lines(file_path):
        fields = raw.split()
        try:
            if len(fields) != _DAILY_FIELD_COUNT:
                raise ValueError(f"expected {_DAILY_FIELD_COUNT} fields, found {len(fields)}")
            day = datetime(int(fields[0]), int(fields[1]), int(fields[2]), tzinfo=timezone.utc)
            record = GfzDailyRecord(
                day=day,
                kp=tuple(_missing_float(text) for text in fields[7:15]),
                ap=tuple(_missing_int(text) for text in fields[15:23]),
                ap_daily=_missing_int(fields[23]),
                sunspot_number=_missing_int(fields[24]),
                f107_obs_sfu=_missing_float(fields[25]),
                f107_adj_sfu=_missing_float(fields[26]),
                definitive=int(fields[27]),
            )
        except ValueError as exc:
            raise ValueError(f"{file_path} line {number}: {exc}") from exc
        if records and record.day <= records[-1].day:
            raise ValueError(f"{file_path} line {number}: dates are not strictly increasing.")
        records.append(record)
    return GfzDailyTable(records=tuple(records), source=source_label(file_path))


def read_gfz_hpo(path: str | Path) -> tuple[HpoRecord, ...]:
    """Parse ``Hp30_ap30`` (complete series, nowcast file or an excerpt)."""
    file_path = Path(path).expanduser()
    records: list[HpoRecord] = []
    for number, raw in _data_lines(file_path):
        fields = raw.split()
        try:
            if len(fields) != _HPO_FIELD_COUNT:
                raise ValueError(f"expected {_HPO_FIELD_COUNT} fields, found {len(fields)}")
            start = datetime(
                int(fields[0]), int(fields[1]), int(fields[2]), tzinfo=timezone.utc
            ) + timedelta(hours=float(fields[3]))
            record = HpoRecord(
                start=start,
                hp30=_missing_float(fields[7]),
                ap30=_missing_int(fields[8]),
                definitive=int(fields[9]),
            )
        except ValueError as exc:
            raise ValueError(f"{file_path} line {number}: {exc}") from exc
        if records and record.start <= records[-1].start:
            raise ValueError(f"{file_path} line {number}: times are not strictly increasing.")
        records.append(record)
    return tuple(records)


__all__ = [
    "GfzDailyRecord",
    "GfzDailyTable",
    "HpoRecord",
    "read_gfz_daily",
    "read_gfz_hpo",
]
