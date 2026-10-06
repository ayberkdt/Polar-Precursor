"""Design matrices per storm window from daily density files (the pilot's input).

The unit of the thesis is the storm. For each catalogue row the daily ESA
density files covering ``[disturbance − pre_hours, window_end]`` are read and
concatenated into one track (so that the first samples of a storm see the
passes of the previous day), then: quasi-dipole coordinates (when apexpy is
installed; geographic latitude otherwise, recorded in the coverage row),
quiet reference density, band segments, forecast samples, and the design
matrix with drivers. Samples are kept only when ``t0`` lies inside the storm
window. One parquet per storm is cached under ``cache_dir`` and reused when
its configuration digest matches.

File names: CHAMP ``CH_OPER_DNS_ACC_2__<YYYYMMDD>T000000_<YYYYMMDD>T235959_<vvvv>.cdf``
(verified on disk, 2026-10-06); GRACE-A ``GR_OPER_DNS1ACC_2__…`` and GRACE-B
``GR_OPER_DNS2ACC_2__…`` are the names plan 01 lists and were **not** verified
against a downloaded file yet.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from polar_precursor.config import ExperimentConfig
from polar_precursor.design.matrix import DESIGN_VERSION, DriverFunction, build_design
from space_environment.analysis.passes import SampleConfig, build_samples, segment_track
from space_environment.analysis.reference_density import (
    REFERENCE_COLUMN,
    ReferenceModel,
    add_reference_density,
)
from space_environment.io.toleos import read_dns_acc_cdf
from space_environment.physics.magnetic_coordinates import add_quasi_dipole, apexpy_available

FILE_PREFIX: dict[str, str] = {
    "CHAMP": "CH_OPER_DNS_ACC_2__",
    "GRACE-A": "GR_OPER_DNS1ACC_2__",
    "GRACE-B": "GR_OPER_DNS2ACC_2__",
}


def daily_file(cdf_dir: Path, satellite: str, day: pd.Timestamp) -> Path | None:
    """The daily product file for ``day`` (any version suffix), or None."""
    if satellite not in FILE_PREFIX:
        raise ValueError(f"unknown satellite {satellite!r}; known: {list(FILE_PREFIX)}.")
    stamp = day.strftime("%Y%m%d")
    pattern = f"{FILE_PREFIX[satellite]}{stamp}T000000_{stamp}T235959_*.cdf"
    matches = sorted(cdf_dir.rglob(pattern))
    return matches[-1] if matches else None


def storm_days(start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    first = start.tz_convert("UTC").floor("D")
    last = end.tz_convert("UTC").floor("D")
    return list(pd.date_range(first, last, freq="D"))


@dataclass(frozen=True, slots=True)
class StormCoverage:
    storm_row: int
    group: int
    intensity: str
    start: pd.Timestamp
    end: pd.Timestamp
    days_needed: int
    days_found: int
    track_records: int
    valid_fraction: float
    segments: int
    samples: int
    design_rows: int
    magnetic: str
    cached: bool

    def as_dict(self) -> dict[str, object]:
        return {
            "storm_row": self.storm_row,
            "group": self.group,
            "intensity": self.intensity,
            "start": self.start,
            "end": self.end,
            "days_needed": self.days_needed,
            "days_found": self.days_found,
            "track_records": self.track_records,
            "valid_fraction": self.valid_fraction,
            "segments": self.segments,
            "samples": self.samples,
            "design_rows": self.design_rows,
            "magnetic": self.magnetic,
            "cached": self.cached,
        }


def _cache_key(
    config: ExperimentConfig,
    satellite: str,
    storm_identity: str,
    stride: int,
    *,
    has_drivers: bool,
    has_oracle: bool,
    reference_label: str = "",
) -> str:
    """Cache identity: design version, configuration, satellite, storm, reference stride,
    and whether driver / oracle columns were attached (a coverage-only build without
    drivers must never be served to a run that expects them).

    The storm is identified by its disturbance time, not by its row in the
    catalogue table: row numbers restart in every catalogue build (measured
    2026-10-06: a 2006-2010 coverage run was served 2001-2005 designs).
    """
    text = (
        f"v{DESIGN_VERSION}|{config.digest()}|{satellite}|{storm_identity}|{stride}"
        f"|drv={int(has_drivers)}|oracle={int(has_oracle)}|ref={reference_label}"
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def build_storm_design(
    storm: pd.Series,
    storms: pd.DataFrame,
    *,
    cdf_dir: Path,
    satellite: str,
    reference_model: ReferenceModel,
    drivers: DriverFunction | None,
    config: ExperimentConfig,
    oracle_drivers: DriverFunction | None = None,
    pre_hours: float = 6.0,
    reference_stride: int = 6,
    cache_dir: Path | None = None,
    force: bool = False,
) -> tuple[pd.DataFrame, StormCoverage]:
    """Design rows of one storm window plus a coverage record (empty frame when no file)."""
    storm_row = int(str(storm.name))
    start = pd.Timestamp(storm["disturbance_utc"]) - pd.Timedelta(pre_hours, unit="h")
    end = pd.Timestamp(storm["window_end_utc"])
    group = int(storm["cluster"])
    intensity = str(storm["intensity"])
    days = storm_days(start, end)
    cache_file = None
    if cache_dir is not None:
        key = _cache_key(
            config,
            satellite,
            pd.Timestamp(storm["disturbance_utc"]).isoformat(),
            reference_stride,
            has_drivers=drivers is not None,
            has_oracle=oracle_drivers is not None,
            reference_label=reference_model.label,
        )
        stamp = pd.Timestamp(storm["disturbance_utc"]).strftime("%Y%m%dT%H%M")
        cache_file = cache_dir / f"{satellite}_{stamp}_{key}.parquet"
        if cache_file.exists() and not force:
            design = pd.read_parquet(cache_file)
            meta = design.attrs
            return design, StormCoverage(
                storm_row,
                group,
                intensity,
                start,
                end,
                len(days),
                int(meta.get("days_found", -1)),
                int(meta.get("track_records", -1)),
                float(meta.get("valid_fraction", float("nan"))),
                int(meta.get("segments", -1)),
                int(meta.get("samples", -1)),
                len(design),
                str(meta.get("magnetic", "?")),
                True,
            )

    files = [daily_file(cdf_dir, satellite, day) for day in days]
    found = [path for path in files if path is not None]
    empty = pd.DataFrame()

    def coverage(
        records: int, valid: float, n_segments: int, n_samples: int, rows: int, magnetic: str
    ) -> StormCoverage:
        return StormCoverage(
            storm_row,
            group,
            intensity,
            start,
            end,
            len(days),
            len(found),
            records,
            valid,
            n_segments,
            n_samples,
            rows,
            magnetic,
            False,
        )

    if not found:
        return empty, coverage(0, float("nan"), 0, 0, 0, "none")
    track = pd.concat([read_dns_acc_cdf(path) for path in found]).sort_index()
    track = track[(track.index >= start - pd.Timedelta(6, unit="h")) & (track.index <= end)]
    if track.empty:
        return empty, coverage(0, float("nan"), 0, 0, 0, "none")
    valid = float((track["validity_flag"] == 0).mean())
    if apexpy_available():
        track = add_quasi_dipole(track)
        band_latitude, mlt, magnetic = "qd_latitude_deg", "mlt_h", "quasi-dipole (apexpy)"
    else:
        band_latitude, mlt, magnetic = "latitude_deg", None, "geographic (apexpy missing)"
    track = add_reference_density(track, reference_model, stride=reference_stride)
    segments = segment_track(
        track, band_latitude=band_latitude, mlt=mlt, reference=REFERENCE_COLUMN
    )
    samples = build_samples(
        segments,
        config=SampleConfig(
            lead_window_min=config.samples.lead_window_min,
            inputs_low=config.samples.inputs_low,
            inputs_polar=config.samples.inputs_polar,
        ),
    )
    if not samples.empty:
        samples = samples[(samples["t0_utc"] >= start) & (samples["t0_utc"] <= end)].reset_index(
            drop=True
        )
    if samples.empty:
        return empty, coverage(len(track), valid, len(segments), 0, 0, magnetic)
    design = build_design(
        samples,
        segments,
        storms=storms,
        satellite=satellite,
        lead_bin_edges_min=config.samples.lead_bin_edges_min,
        drivers=drivers,
        oracle_drivers=oracle_drivers,
        inputs_low=config.samples.inputs_low,
        inputs_polar=config.samples.inputs_polar,
        keep_outside_storms=True,
    )
    design = design[design["group"] == group]  # t0 inside this storm's window only
    design = design.reset_index(drop=True)
    design.attrs.update(
        {
            "days_found": len(found),
            "track_records": len(track),
            "valid_fraction": valid,
            "segments": len(segments),
            "samples": len(samples),
            "magnetic": magnetic,
            "reference_model": reference_model.label,
            "reference_stride": reference_stride,
            "files": [str(path) for path in found],
        }
    )
    if cache_file is not None:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        design.to_parquet(cache_file, index=False)
    return design, coverage(len(track), valid, len(segments), len(samples), len(design), magnetic)


def build_dataset(
    storms: pd.DataFrame,
    *,
    cdf_dir: Path,
    satellite: str,
    reference_model: ReferenceModel,
    drivers: DriverFunction | None,
    config: ExperimentConfig,
    oracle_drivers: DriverFunction | None = None,
    storm_rows: Sequence[int] | None = None,
    pre_hours: float = 6.0,
    reference_stride: int = 6,
    cache_dir: Path | None = None,
    force: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Concatenated design over the selected storms and one coverage row per storm."""
    selected = storms if storm_rows is None else storms.loc[list(storm_rows)]
    designs: list[pd.DataFrame] = []
    coverage: list[dict[str, object]] = []
    for _, storm in selected.iterrows():
        design, record = build_storm_design(
            storm,
            storms,
            cdf_dir=cdf_dir,
            satellite=satellite,
            reference_model=reference_model,
            drivers=drivers,
            config=config,
            oracle_drivers=oracle_drivers,
            pre_hours=pre_hours,
            reference_stride=reference_stride,
            cache_dir=cache_dir,
            force=force,
        )
        coverage.append(record.as_dict())
        if not design.empty:
            designs.append(design)
    dataset = pd.concat(designs, ignore_index=True) if designs else pd.DataFrame()
    report = pd.DataFrame(coverage)
    if not dataset.empty:
        dataset = dataset[dataset["group"] >= 0].reset_index(drop=True)
        assert np.all(np.isfinite(dataset["target_value"]))
    return dataset, report


__all__ = [
    "FILE_PREFIX",
    "StormCoverage",
    "build_dataset",
    "build_storm_design",
    "daily_file",
    "storm_days",
]
