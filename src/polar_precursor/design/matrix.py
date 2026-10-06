"""Design-matrix builder: forecast samples + segments + storms + drivers → one frame.

Input is the output of ``space_environment.analysis.passes.build_samples`` (one
row per (polar pass, target) pair with segment ids) together with the segment
table it came from, the storm catalogue, and driver feature callables. Output
follows the column convention in ``ladder.py``. Causality: driver features are
evaluated at t0 floored to the minute (never later than t0); oracle features
are evaluated at the target mid time and only enter B3k.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

import numpy as np
import pandas as pd

from polar_precursor.design.ladder import GROUP, INTENSITY, LEAD_BIN, PERSISTENCE, TARGET
from space_environment.analysis.index_features import geometry_features

DriverFunction = Callable[[pd.Timestamp], Mapping[str, float]]


def lead_bin_labels(lead_time_min: np.ndarray, edges_min: Sequence[float]) -> np.ndarray:
    """Bin label ``"<lo>-<hi>"`` per sample; samples outside the edges get ``"out"``."""
    edges = np.asarray(edges_min, dtype=np.float64)
    labels = np.full(lead_time_min.shape, "out", dtype=object)
    for low, high in zip(edges[:-1], edges[1:], strict=True):
        inside = (lead_time_min >= low) & (lead_time_min < high)
        labels[inside] = f"{low:g}-{high:g}"
    last = lead_time_min == edges[-1]
    labels[last] = f"{edges[-2]:g}-{edges[-1]:g}"
    return labels


def assign_storms(t0: pd.Series, storms: pd.DataFrame) -> pd.DataFrame:
    """Storm row index, cluster and intensity for each t0 inside a catalogue window.

    Windows are ``[disturbance_utc, window_end_utc]``. Catalogue windows do not
    overlap (``build_storm_catalog`` caps each at the next disturbance), so at
    most one storm matches; samples outside every window get NaN.
    """
    for column in ("disturbance_utc", "window_end_utc", "cluster", "intensity"):
        if column not in storms.columns:
            raise ValueError(f"storms lacks column {column!r}.")
    starts = storms["disturbance_utc"].to_numpy()
    ends = storms["window_end_utc"].to_numpy()
    order = np.argsort(starts)
    starts, ends = starts[order], ends[order]
    if np.any(starts[1:] < ends[:-1]):
        raise ValueError("storm windows overlap; the catalogue must cap windows.")
    times = t0.to_numpy()
    position = np.searchsorted(starts, times, side="right") - 1
    inside = (position >= 0) & (times <= ends[np.clip(position, 0, len(ends) - 1)])
    rows = np.where(inside, order[np.clip(position, 0, len(order) - 1)], -1)
    out = pd.DataFrame(index=t0.index)
    out["storm_row"] = np.where(rows >= 0, rows, np.nan)
    cluster = storms["cluster"].to_numpy()
    intensity = storms["intensity"].astype(str).to_numpy()
    out[GROUP] = [int(cluster[r]) if r >= 0 else -1 for r in rows]
    out[INTENSITY] = [intensity[r] if r >= 0 else "none" for r in rows]
    return out


def _lagged(value_of: dict[int, float], ids: Sequence[int], count: int) -> list[float]:
    """Values of the given segments, most recent first, padded with NaN to ``count``."""
    recent_first = [value_of[int(i)] for i in ids][::-1]
    return (recent_first + [float("nan")] * count)[:count]


def _column_map(segments: pd.DataFrame, column: str) -> dict[int, float]:
    ids = segments["segment_id"].to_numpy()
    values = segments[column].to_numpy(dtype=np.float64)
    return {int(i): float(v) for i, v in zip(ids, values, strict=True)}


def build_design(
    samples: pd.DataFrame,
    segments: pd.DataFrame,
    *,
    storms: pd.DataFrame,
    satellite: str,
    lead_bin_edges_min: Sequence[float],
    drivers: DriverFunction | None = None,
    oracle_drivers: DriverFunction | None = None,
    inputs_low: int = 4,
    inputs_polar: int = 4,
    keep_outside_storms: bool = False,
) -> pd.DataFrame:
    """One design row per sample. Rows outside every storm window are dropped unless asked."""
    if samples.empty:
        return pd.DataFrame()
    by_id = segments.set_index("segment_id")
    value_of = _column_map(segments, "target_mean")
    altitude_of = _column_map(segments, "altitude_mean_m")
    rows: list[dict[str, object]] = []
    for _, sample in samples.iterrows():
        t0 = pd.Timestamp(sample["t0_utc"])
        target_segment = int(sample["target_segment"])
        target_direction = by_id.at[target_segment, "direction"]
        low_ids = list(sample["input_low_segments"])
        same_sector = [i for i in low_ids if by_id.at[i, "direction"] == target_direction]
        row: dict[str, object] = {
            "t0_utc": t0,
            "target_mid_utc": pd.Timestamp(sample["target_mid_utc"]),
            "satellite": satellite,
            "lead_time_min": float(sample["lead_time_min"]),
            TARGET: float(sample[TARGET]),
            PERSISTENCE: value_of[int(same_sector[-1])] if same_sector else float("nan"),
        }
        for k, value in enumerate(_lagged(value_of, low_ids, inputs_low), start=1):
            row[f"low_lag{k}"] = value
        for hemisphere in ("north", "south"):
            ids = list(sample[f"input_polar_{hemisphere}_segments"])
            for k, value in enumerate(_lagged(value_of, ids, inputs_polar), start=1):
                row[f"polar_{hemisphere}_lag{k}"] = value
        mid = sample["input_mid_segment"]
        row["mid_same"] = float("nan") if pd.isna(mid) else value_of[int(mid)]
        geometry = geometry_features(
            t0.to_pydatetime(),
            lead_time_h=float(sample["lead_time_min"]) / 60.0,
            target_local_solar_time_h=float(sample["target_lst_h"]) % 24.0,
            altitude_m=altitude_of[target_segment],
        )
        row.update({f"geo_{name}": value for name, value in geometry.items()})
        if drivers is not None:
            for name, value in drivers(t0.floor("min")).items():
                row[f"drv_{name}"] = float(value)
        if oracle_drivers is not None:
            target_time = pd.Timestamp(sample["target_mid_utc"]).floor("min")
            for name, value in oracle_drivers(target_time).items():
                row[f"drv_oracle_{name}"] = float(value)
        rows.append(row)
    design = pd.DataFrame(rows)
    design[LEAD_BIN] = lead_bin_labels(design["lead_time_min"].to_numpy(), lead_bin_edges_min)
    assignment = assign_storms(design["t0_utc"], storms)
    design[GROUP] = assignment[GROUP].to_numpy()
    design[INTENSITY] = assignment[INTENSITY].to_numpy()
    if not keep_outside_storms:
        design = design[design[GROUP] >= 0].reset_index(drop=True)
    return design


__all__ = ["DriverFunction", "assign_storms", "build_design", "lead_bin_labels"]
