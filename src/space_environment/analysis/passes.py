"""Band segments along a density track and the forecast samples built from them.

A low-Earth polar orbit crosses the polar cap, the mid latitudes and the low
latitudes twice per revolution. The thesis design (plans/04) turns an
accelerometer density track into *segments*: contiguous runs of samples inside
a latitude band, each with its times and statistics. A forecast sample is then
a pair (polar pass that just ended, low-latitude segment one to four hours
ahead), with the preceding segments as inputs.

Latitude used for the bands is whatever column the caller names (quasi-dipole
latitude when ``space_environment.physics.magnetic_coordinates`` has been
applied, geographic latitude otherwise); the orbit direction (ascending or
descending) always comes from the geographic latitude.

Rules (plans/04, "Geçiş bölütleme"):

- Samples whose validity flag is not 0 or whose density is missing count as
  invalid; a segment is ``complete`` when its valid fraction reaches
  ``min_valid_fraction`` (0.7 to start; the pilot fixes it).
- The polar band is one segment from the moment the track exceeds the
  threshold until it drops below it again, even though that spans two half
  orbits.
- Per segment: start, end, mid time, hemisphere, direction, orbit number,
  sample count, valid fraction, mean and maximum of the target quantity,
  mean altitude, mean local solar time, mean magnetic local time (if present),
  highest absolute band latitude reached, cusp fraction (polar samples with
  10-14 MLT).

The target quantity is ``log(density / reference)`` when a reference column is
given, else ``log(density)``. Sidera destination:
``sidera.analysis.space_environment.passes``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

Hemisphere = Literal["north", "south", "both"]
Direction = Literal["ascending", "descending", "mixed"]


@dataclass(frozen=True, slots=True)
class Band:
    """Absolute-latitude band ``[lower, upper)`` in degrees; ``split`` separates the hemispheres."""

    name: str
    lower_deg: float
    upper_deg: float
    split_hemispheres: bool = True

    def __post_init__(self) -> None:
        if not 0.0 <= self.lower_deg < self.upper_deg <= 90.0:
            raise ValueError(f"Band {self.name!r}: need 0 <= lower < upper <= 90 degrees.")


#: plans/04: target |lat| < 30, polar input |lat| > 63, freshness band 40-55.
DEFAULT_BANDS: tuple[Band, ...] = (
    Band("polar", 63.0, 90.0),
    Band("mid", 40.0, 55.0),
    Band("low", 0.0, 30.0, split_hemispheres=False),
)


@dataclass(frozen=True, slots=True)
class SegmentationConfig:
    bands: tuple[Band, ...] = DEFAULT_BANDS
    min_valid_fraction: float = 0.7
    cusp_mlt_h: tuple[float, float] = (10.0, 14.0)
    #: A gap in the record longer than this ends a segment.
    max_gap_s: float = 600.0
    #: Latitude extrema closer than this to the equator are jitter, not turning points.
    min_turning_latitude_deg: float = 45.0


REQUIRED_COLUMNS = (
    "latitude_deg",
    "density_kg_m3",
    "validity_flag",
    "local_solar_time_h",
    "altitude_m",
)


def _check_frame(frame: pd.DataFrame, band_latitude: str) -> None:
    missing = [c for c in (*REQUIRED_COLUMNS, band_latitude) if c not in frame.columns]
    if missing:
        raise ValueError(f"track lacks columns {missing}.")
    if not isinstance(frame.index, pd.DatetimeIndex) or not frame.index.is_monotonic_increasing:
        raise ValueError("track must have an increasing DatetimeIndex.")
    if frame.index.has_duplicates:
        raise ValueError("track has duplicate time stamps.")


def orbit_direction(latitude_deg: np.ndarray, *, min_turning_latitude_deg: float) -> np.ndarray:
    """+1 where geographic latitude is increasing (ascending), -1 where decreasing.

    Turning points are sign changes of the latitude difference at
    ``|lat| >= min_turning_latitude_deg``; sign changes nearer the equator are
    treated as noise and the previous direction is kept.
    """
    diff = np.diff(latitude_deg, prepend=latitude_deg[0])
    direction = np.zeros(len(latitude_deg), dtype=np.int8)
    current = 1 if (diff[1:] > 0).sum() >= (diff[1:] < 0).sum() else -1
    # Seed from the first non-zero difference.
    for value in diff[1:]:
        if value != 0.0:
            current = 1 if value > 0 else -1
            break
    for index, value in enumerate(diff):
        if value != 0.0:
            candidate = 1 if value > 0 else -1
            if candidate != current and abs(latitude_deg[index]) >= min_turning_latitude_deg:
                current = candidate
        direction[index] = current
    return direction


def orbit_numbers(latitude_deg: np.ndarray, direction: np.ndarray) -> np.ndarray:
    """Orbit counter incremented at each ascending equator crossing (0 before the first)."""
    crossing = (latitude_deg[1:] >= 0.0) & (latitude_deg[:-1] < 0.0) & (direction[1:] > 0)
    numbers = np.zeros(len(latitude_deg), dtype=np.int64)
    numbers[1:] = np.cumsum(crossing)
    return numbers


def segment_track(
    track: pd.DataFrame,
    *,
    band_latitude: str = "latitude_deg",
    reference: str | None = None,
    mlt: str | None = None,
    config: SegmentationConfig | None = None,
) -> pd.DataFrame:
    """One row per band segment of ``track`` (see the module docstring for the columns)."""
    cfg = config or SegmentationConfig()
    _check_frame(track, band_latitude)
    if reference is not None and reference not in track.columns:
        raise ValueError(f"reference column {reference!r} is not in the track.")
    if mlt is not None and mlt not in track.columns:
        raise ValueError(f"mlt column {mlt!r} is not in the track.")

    times = track.index
    geo_lat = track["latitude_deg"].to_numpy(dtype=np.float64)
    band_lat = track[band_latitude].to_numpy(dtype=np.float64)
    density = track["density_kg_m3"].to_numpy(dtype=np.float64)
    flags = track["validity_flag"].to_numpy()
    valid = (flags == 0) & ~np.isnan(density)
    with np.errstate(divide="ignore", invalid="ignore"):
        target = np.log(density)
        if reference is not None:
            target = target - np.log(track[reference].to_numpy(dtype=np.float64))
    # A record without a finite target (reference missing or non-positive) is
    # not a valid sample even when the density flag is nominal.
    valid &= np.isfinite(target)
    target = np.where(valid, target, np.nan)
    direction = orbit_direction(geo_lat, min_turning_latitude_deg=cfg.min_turning_latitude_deg)
    orbit = orbit_numbers(geo_lat, direction)
    steps_s = np.diff(times.to_numpy()).astype("timedelta64[ns]").astype(np.int64) / 1e9
    step_s = float(np.median(steps_s))
    gap_break = steps_s > cfg.max_gap_s
    mlt_values = None if mlt is None else track[mlt].to_numpy(dtype=np.float64)

    rows: list[dict[str, object]] = []
    for band in cfg.bands:
        inside = (np.abs(band_lat) >= band.lower_deg) & (np.abs(band_lat) < band.upper_deg)
        inside &= ~np.isnan(band_lat)
        if band.split_hemispheres:
            groups = [("north", inside & (band_lat >= 0.0)), ("south", inside & (band_lat < 0.0))]
        else:
            groups = [("both", inside)]
        for hemisphere, member in groups:
            for start, stop in _runs(member, gap_break):
                sl = slice(start, stop + 1)
                n = stop + 1 - start
                expected = int(round((times[stop] - times[start]).total_seconds() / step_s)) + 1
                valid_fraction = float(valid[sl].sum() / max(expected, n))
                seg_target = target[sl]
                has_valid = bool(np.any(~np.isnan(seg_target)))
                seg_dir = direction[sl]
                if np.all(seg_dir > 0):
                    direction_label: Direction = "ascending"
                elif np.all(seg_dir < 0):
                    direction_label = "descending"
                else:
                    direction_label = "mixed"
                cusp = float("nan")
                mean_mlt = float("nan")
                if mlt_values is not None:
                    seg_mlt = mlt_values[sl]
                    present = ~np.isnan(seg_mlt)
                    if present.any():
                        mean_mlt = _circular_mean_hours(seg_mlt[present])
                        lo, hi = cfg.cusp_mlt_h
                        cusp = float(((seg_mlt[present] >= lo) & (seg_mlt[present] < hi)).mean())
                rows.append(
                    {
                        "band": band.name,
                        "hemisphere": hemisphere,
                        "direction": direction_label,
                        "orbit": int(orbit[start]),
                        "start_utc": times[start],
                        "end_utc": times[stop],
                        "mid_utc": times[start] + (times[stop] - times[start]) / 2,
                        "samples": int(n),
                        "valid_fraction": valid_fraction,
                        "complete": valid_fraction >= cfg.min_valid_fraction,
                        "target_mean": float(np.nanmean(seg_target)) if has_valid else float("nan"),
                        "target_max": float(np.nanmax(seg_target)) if has_valid else float("nan"),
                        "altitude_mean_m": float(np.nanmean(track["altitude_m"].to_numpy()[sl])),
                        "lst_mean_h": _circular_mean_hours(
                            track["local_solar_time_h"].to_numpy(dtype=np.float64)[sl]
                        ),
                        "mlt_mean_h": mean_mlt,
                        "max_abs_band_latitude_deg": float(np.nanmax(np.abs(band_lat[sl]))),
                        "cusp_fraction": cusp,
                    }
                )
    segments = pd.DataFrame(rows)
    if segments.empty:
        return segments
    segments = segments.sort_values(["start_utc", "band"]).reset_index(drop=True)
    segments.insert(0, "segment_id", np.arange(len(segments)))
    segments.attrs["band_latitude"] = band_latitude
    segments.attrs["reference"] = reference
    segments.attrs["step_s"] = step_s
    return segments


def _runs(member: np.ndarray, gap_break: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous True runs of ``member``; a flagged gap between i and i+1 also ends a run."""
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index, inside in enumerate(member):
        if inside and start is None:
            start = index
        ends_here = inside and (
            index == len(member) - 1 or not member[index + 1] or gap_break[index]
        )
        if start is not None and ends_here:
            runs.append((start, index))
            start = None
        elif not inside:
            start = None
    return runs


def _circular_mean_hours(hours: np.ndarray) -> float:
    present = hours[~np.isnan(hours)]
    if present.size == 0:
        return float("nan")
    angle = 2.0 * np.pi * present / 24.0
    mean = np.arctan2(np.sin(angle).mean(), np.cos(angle).mean())
    return float((mean / (2.0 * np.pi) * 24.0) % 24.0)


@dataclass(frozen=True, slots=True)
class SampleConfig:
    lead_window_min: tuple[float, float] = (60.0, 270.0)
    inputs_low: int = 4
    inputs_polar: int = 4
    require_complete: bool = True


def build_samples(segments: pd.DataFrame, *, config: SampleConfig | None = None) -> pd.DataFrame:
    """Forecast samples: (polar pass end = t0, low-latitude target 1-4.5 h ahead).

    Inputs attached to each sample are segment ids: the last ``inputs_low``
    low segments ending at or before t0, the last ``inputs_polar`` polar passes
    per hemisphere ending at or before t0 (the one ending at t0 included), and
    the last mid-latitude segment ending at or before t0. Every input ends at
    or before t0 and the target starts after t0; ``check_no_leakage`` asserts it.
    """
    cfg = config or SampleConfig()
    if segments.empty:
        return pd.DataFrame()
    usable = segments[segments["complete"]] if cfg.require_complete else segments
    polar = usable[usable["band"] == "polar"]
    low = usable[usable["band"] == "low"]
    mid = usable[usable["band"] == "mid"]
    lead_lo = pd.Timedelta(cfg.lead_window_min[0], unit="m")
    lead_hi = pd.Timedelta(cfg.lead_window_min[1], unit="m")
    rows: list[dict[str, object]] = []
    for _, pass_row in polar.iterrows():
        t0 = pass_row["end_utc"]
        targets = low[(low["mid_utc"] >= t0 + lead_lo) & (low["mid_utc"] <= t0 + lead_hi)]
        targets = targets[targets["start_utc"] > t0]
        if targets.empty:
            continue
        low_inputs = low[low["end_utc"] <= t0].tail(cfg.inputs_low)
        polar_north = polar[(polar["end_utc"] <= t0) & (polar["hemisphere"] == "north")].tail(
            cfg.inputs_polar
        )
        polar_south = polar[(polar["end_utc"] <= t0) & (polar["hemisphere"] == "south")].tail(
            cfg.inputs_polar
        )
        mid_inputs = mid[mid["end_utc"] <= t0].tail(1)
        mid_after_all = mid[
            (mid["start_utc"] >= t0) & (mid["hemisphere"] == pass_row["hemisphere"])
        ]
        for _, target in targets.iterrows():
            rows.append(
                {
                    "t0_utc": t0,
                    "polar_segment": int(pass_row["segment_id"]),
                    "polar_hemisphere": pass_row["hemisphere"],
                    "target_segment": int(target["segment_id"]),
                    "target_mid_utc": target["mid_utc"],
                    "lead_time_min": (target["mid_utc"] - t0) / pd.Timedelta(1, unit="m"),
                    "target_value": target["target_mean"],
                    "target_lst_h": target["lst_mean_h"],
                    "input_low_segments": tuple(int(i) for i in low_inputs["segment_id"]),
                    "input_polar_north_segments": tuple(int(i) for i in polar_north["segment_id"]),
                    "input_polar_south_segments": tuple(int(i) for i in polar_south["segment_id"]),
                    "input_mid_segment": None
                    if mid_inputs.empty
                    else int(mid_inputs["segment_id"].iloc[0]),
                    "input_mid_after_segment": _mid_after(mid_after_all, target["start_utc"]),
                }
            )
    samples = pd.DataFrame(rows)
    if not samples.empty:
        check_no_leakage(samples, segments)
    return samples


def _mid_after(candidates: pd.DataFrame, target_start: pd.Timestamp) -> int | None:
    """First mid-latitude segment after the polar pass that ends before the target starts.

    This is the second B3t definition (plan 04): a mid-latitude measurement
    *fresher* than the polar pass. It ends after t0 by construction, so it is
    exempt from the t0 rule in ``check_no_leakage`` but must end before the
    target starts.
    """
    usable = candidates[candidates["end_utc"] < target_start]
    return None if usable.empty else int(usable["segment_id"].iloc[0])


def check_no_leakage(samples: pd.DataFrame, segments: pd.DataFrame) -> None:
    """Raise if an input segment ends after its sample t0 or a target starts at or before it.

    ``input_mid_after_segment`` is the one input allowed to end after t0 (it
    defines a later issue time); it must still end before the target starts.
    """
    by_id = segments.set_index("segment_id")
    for _, sample in samples.iterrows():
        t0 = sample["t0_utc"]
        inputs: list[int] = [
            *sample["input_low_segments"],
            *sample["input_polar_north_segments"],
            *sample["input_polar_south_segments"],
        ]
        if not pd.isna(sample["input_mid_segment"]):
            inputs.append(int(sample["input_mid_segment"]))
        late = [i for i in inputs if by_id.at[i, "end_utc"] > t0]
        if late:
            raise AssertionError(f"inputs {late} end after t0 = {t0.isoformat()}.")
        target_start = by_id.at[int(sample["target_segment"]), "start_utc"]
        if target_start <= t0:
            raise AssertionError(f"target {sample['target_segment']} starts at or before t0.")
        mid_after = sample.get("input_mid_after_segment")
        if mid_after is not None and not pd.isna(mid_after):
            if by_id.at[int(mid_after), "end_utc"] >= target_start:
                raise AssertionError(f"mid_after {int(mid_after)} ends at or after the target.")


__all__ = [
    "DEFAULT_BANDS",
    "Band",
    "SampleConfig",
    "SegmentationConfig",
    "build_samples",
    "check_no_leakage",
    "orbit_direction",
    "orbit_numbers",
    "segment_track",
]
