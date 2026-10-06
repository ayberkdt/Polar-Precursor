"""Storm catalogue built from the Richardson and Cane ICME list and OMNI.

Richardson and Cane, "Near-Earth Interplanetary Coronal Mass Ejections Since
January 1996", Harvard Dataverse doi:10.7910/DVN/C2MHTH (``icmetable2.xlsx``,
read 2026-10-06, 644 events from 1996-05 to 2026-07). The sheet has one
header row and these columns in order: disturbance time, ICME plasma/field
start and end, composition start/end offsets, magnetic-cloud start/end
offsets, BDE, BIF, quality, dV, V_ICME, V_max, B, MC flag, Dst, V_transit,
LASCO CME time. Values are a mixture of numbers and annotated strings
(``'...'`` not available, ``'ns'``/``'nc'`` no start/no clear boundary,
``'dg'`` data gap, ``'100 S'``, ``'-61 P'``, ``'2H'``, ``'(A)'`` suffixes on
times). The reader keeps every annotation letter next to its value instead
of discarding it; what each letter means is documented on the catalogue's
web page and was not re-read in this project, so the fields are named after
the column, not the meaning.

``build_storm_catalog`` turns ICME events into storm rows: minimum SYM-H
and its time in a window from the disturbance to ``tail_h`` after the ICME
end, the intensity class, the automatic main-phase onset, OMNI driver
coverage in the first day, and a cluster id grouping events whose windows
touch (consecutive ICMEs such as 28-30 October 2003 are one cluster, which
is the unit for cross-validation splits).
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from space_environment.common.provenance import source_label
from space_environment.physics.storm_intensity import classify_by_min_symh
from space_environment.physics.storm_onset import find_main_phase_onset

_TIME_PATTERN = re.compile(r"^(\d{4})/(\d{1,2})/(\d{1,2})\s+(\d{2})(\d{2})\s*(?:\(([A-Za-z])\))?$")
_VALUE_PATTERN = re.compile(r"^([+-]?\d+(?:\.\d+)?)\s*([A-Za-z]+)?$")
_MISSING_TOKENS = frozenset({"", "...", "..", "dg", "ns", "nc"})


@dataclass(frozen=True, slots=True)
class IcmeRecord:
    """One event of the Richardson and Cane list; ``*_note`` keeps annotation letters."""

    row: int
    disturbance_utc: datetime
    disturbance_note: str | None
    icme_start_utc: datetime
    icme_end_utc: datetime
    quality: int | None
    quality_note: str | None
    dv_km_s: float | None
    dv_note: str | None
    v_icme_km_s: float | None
    v_max_km_s: float | None
    b_nt: float | None
    mc: float | None
    mc_note: str | None
    dst_nt: float | None
    dst_note: str | None
    v_transit_km_s: float | None


@dataclass(frozen=True, slots=True)
class IcmeCatalogue:
    records: tuple[IcmeRecord, ...]
    source: str

    def between(self, first_year: int, last_year: int) -> tuple[IcmeRecord, ...]:
        """Events whose disturbance time falls in ``[first_year, last_year]``."""
        return tuple(
            record
            for record in self.records
            if first_year <= record.disturbance_utc.year <= last_year
        )


def _parse_time(value: Any, *, row: int, column: str) -> tuple[datetime, str | None]:
    if isinstance(value, datetime):
        return value.replace(tzinfo=timezone.utc), None
    match = _TIME_PATTERN.match(str(value).strip())
    if match is None:
        raise ValueError(f"icmetable2 row {row}, {column}: unparseable time {value!r}.")
    year, month, day, hour, minute = (int(group) for group in match.groups()[:5])
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc), match.group(6)


def _parse_value(value: Any) -> tuple[float | None, str | None]:
    """Number and annotation; (None, raw text) when the cell is not a number."""
    if value is None or isinstance(value, datetime | time):
        return None, None if value is None else str(value)
    if isinstance(value, int | float):
        return float(value), None
    text = str(value).strip()
    if text in _MISSING_TOKENS:
        return None, text or None
    match = _VALUE_PATTERN.match(text)
    if match is None:
        return None, text
    return float(match.group(1)), match.group(2)


def read_richardson_cane(path: str | Path) -> IcmeCatalogue:
    """Read ``icmetable2.xlsx`` (requires ``openpyxl``, optional dependency ``catalog``)."""
    import openpyxl

    file_path = Path(path)
    workbook = openpyxl.load_workbook(file_path, read_only=True)
    try:
        sheet = workbook[workbook.sheetnames[0]]
        rows = list(sheet.iter_rows(values_only=True))
    finally:
        workbook.close()
    if not rows or not str(rows[0][0]).startswith("Disturbance"):
        raise ValueError(f"{file_path.name}: first header cell is not the disturbance column.")
    records: list[IcmeRecord] = []
    for position, cells in enumerate(rows[1:], start=2):
        if cells[0] is None:
            continue
        disturbance, disturbance_note = _parse_time(cells[0], row=position, column="disturbance")
        start, _ = _parse_time(cells[1], row=position, column="ICME start")
        end, _ = _parse_time(cells[2], row=position, column="ICME end")
        # The disturbance may follow the ICME start by minutes (row 309, 2007-01-14:
        # 12:48 against 12:00); only start <= end is required.
        if start > end:
            raise ValueError(
                f"icmetable2 row {position}: ICME start {start} is after its end {end}."
            )
        quality, quality_note = _parse_value(cells[9])
        dv, dv_note = _parse_value(cells[10])
        v_icme, _ = _parse_value(cells[11])
        v_max, _ = _parse_value(cells[12])
        b_nt, _ = _parse_value(cells[13])
        mc, mc_note = _parse_value(cells[14])
        dst, dst_note = _parse_value(cells[15])
        v_transit, _ = _parse_value(cells[16])
        records.append(
            IcmeRecord(
                row=position,
                disturbance_utc=disturbance,
                disturbance_note=disturbance_note,
                icme_start_utc=start,
                icme_end_utc=end,
                quality=None if quality is None else int(quality),
                quality_note=quality_note,
                dv_km_s=dv,
                dv_note=dv_note,
                v_icme_km_s=v_icme,
                v_max_km_s=v_max,
                b_nt=b_nt,
                mc=mc,
                mc_note=mc_note,
                dst_nt=dst,
                dst_note=dst_note,
                v_transit_km_s=v_transit,
            )
        )
    if not records:
        raise ValueError(f"{file_path.name}: no event rows.")
    ordered = all(
        earlier.disturbance_utc <= later.disturbance_utc
        for earlier, later in zip(records, records[1:], strict=False)
    )
    if not ordered:
        raise ValueError(f"{file_path.name}: events are not in time order.")
    return IcmeCatalogue(tuple(records), source_label(file_path))


def _coverage(frame: pd.DataFrame, column: str, start: pd.Timestamp, stop: pd.Timestamp) -> float:
    """Fraction of the minutes in ``[start, stop]`` that hold a value."""
    expected = int((stop - start) / pd.Timedelta(1, unit="m")) + 1
    if expected <= 0:
        return 0.0
    present = int(frame[column].loc[start:stop].notna().sum())
    return present / expected


def build_storm_catalog(
    icmes: Sequence[IcmeRecord],
    omni: pd.DataFrame,
    *,
    tail_h: float = 24.0,
    driver_window_h: float = 24.0,
    cluster_gap_h: float = 24.0,
    min_symh_coverage: float = 0.8,
    onset_options: Mapping[str, Any] | None = None,
) -> pd.DataFrame:
    """One row per ICME with storm properties measured on 1-minute OMNI data.

    ``omni`` is the frame of ``read_omni_hro`` (needs ``sym_h_nt``,
    ``bz_gsm_nt``, ``flow_speed_km_s``, ``proton_density_cm3``). The minimum
    SYM-H is searched from the disturbance time to ``tail_h`` after the ICME
    end, but never past the next event's disturbance time; when less than
    ``min_symh_coverage`` of that window has SYM-H the minimum and class are
    left empty rather than taken from partial data.
    Driver coverage is measured over ``driver_window_h`` after the
    disturbance. ``cluster`` numbers events whose windows overlap or lie
    within ``cluster_gap_h`` of each other.
    """
    required = ("sym_h_nt", "bz_gsm_nt", "flow_speed_km_s", "proton_density_cm3")
    missing = [column for column in required if column not in omni.columns]
    if missing:
        raise ValueError(f"omni lacks columns {missing}.")
    if not isinstance(omni.index, pd.DatetimeIndex) or not omni.index.is_monotonic_increasing:
        raise ValueError("omni must have an increasing DatetimeIndex.")
    options = dict(onset_options or {})
    tail = pd.Timedelta(tail_h, unit="h")
    driver_window = pd.Timedelta(driver_window_h, unit="h")
    gap = pd.Timedelta(cluster_gap_h, unit="h")

    rows: list[dict[str, Any]] = []
    cluster = 0
    cluster_end: pd.Timestamp | None = None
    ordered = sorted(icmes, key=lambda item: item.disturbance_utc)
    for position, record in enumerate(ordered):
        disturbance = pd.Timestamp(record.disturbance_utc)
        window_end = pd.Timestamp(record.icme_end_utc) + tail
        if position + 1 < len(ordered):
            # Consecutive ICMEs: the minimum belongs to the event whose window it falls
            # in, so each window stops where the next disturbance begins (28-30 October
            # 2003 would otherwise all report the 30 October minimum).
            window_end = min(window_end, pd.Timestamp(ordered[position + 1].disturbance_utc))
        if cluster_end is None or disturbance > cluster_end + gap:
            cluster += 1
            cluster_end = window_end
        else:
            cluster_end = max(cluster_end, window_end)

        symh = omni["sym_h_nt"].loc[disturbance:window_end]
        symh_coverage = _coverage(omni, "sym_h_nt", disturbance, window_end)
        min_symh = float("nan")
        min_symh_time: pd.Timestamp | None = None
        intensity: str | None = None
        if symh_coverage >= min_symh_coverage and symh.notna().any():
            position = int(np.nanargmin(symh.to_numpy(dtype=np.float64)))
            min_symh = float(symh.iloc[position])
            min_symh_time = symh.index[position]
            intensity = classify_by_min_symh(min_symh).value

        onset = find_main_phase_onset(omni["bz_gsm_nt"], disturbance, **options)
        onset_offset = (
            float("nan")
            if onset.onset is None
            else (onset.onset - disturbance) / pd.Timedelta(1, unit="m")
        )
        driver_end = disturbance + driver_window
        rows.append(
            {
                "rc_row": record.row,
                "disturbance_utc": disturbance,
                "icme_start_utc": pd.Timestamp(record.icme_start_utc),
                "icme_end_utc": pd.Timestamp(record.icme_end_utc),
                "window_end_utc": window_end,
                "symh_coverage": symh_coverage,
                "min_symh_nt": min_symh,
                "min_symh_utc": min_symh_time,
                "intensity": intensity,
                "rc_dst_nt": record.dst_nt,
                "onset_status": onset.status,
                "onset_utc": onset.onset,
                "onset_minus_disturbance_min": onset_offset,
                "bz_coverage": _coverage(omni, "bz_gsm_nt", disturbance, driver_end),
                "speed_coverage": _coverage(omni, "flow_speed_km_s", disturbance, driver_end),
                "density_coverage": _coverage(omni, "proton_density_cm3", disturbance, driver_end),
                "cluster": cluster,
            }
        )
    catalog = pd.DataFrame(rows)
    catalog.attrs["omni_source"] = omni.attrs.get("source")
    return catalog


__all__ = ["IcmeCatalogue", "IcmeRecord", "build_storm_catalog", "read_richardson_cane"]
