"""Storm-grouped folds and the inter-group buffer check (plan 07, CV skeleton).

Groups are storm clusters (``design["group"]``). Folds are assigned by dealing
the groups, sorted by their first forecast time, to folds in turn, so that each
fold spans the whole period and the solar-cycle phase cannot leak into a fold.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from polar_precursor.design.ladder import GROUP


def grouped_folds(groups: np.ndarray, order_key: np.ndarray, n_folds: int) -> np.ndarray:
    """Fold id per row. Groups are sorted by their earliest ``order_key`` and dealt round-robin."""
    groups = np.asarray(groups)
    if n_folds < 2:
        raise ValueError("n_folds must be at least 2.")
    unique = np.unique(groups)
    if len(unique) < n_folds:
        raise ValueError(f"{len(unique)} groups cannot fill {n_folds} folds.")
    first_time = {g: order_key[groups == g].min() for g in unique}
    ordered = sorted(unique, key=lambda g: (first_time[g], g))
    fold_of_group = {g: position % n_folds for position, g in enumerate(ordered)}
    return np.array([fold_of_group[g] for g in groups], dtype=np.int64)


@dataclass(frozen=True, slots=True)
class BufferViolation:
    earlier_group: int
    later_group: int
    gap_h: float


def check_group_buffer(design: pd.DataFrame, *, buffer_h: float) -> list[BufferViolation]:
    """Pairs of consecutive groups whose sample windows lie closer than ``buffer_h``.

    A violation means two storms that should have been merged into one cluster
    (the longest feature memory would let one storm's drivers reach the other).
    The caller decides whether to raise; the experiment pipeline does.
    """
    if GROUP not in design.columns:
        raise ValueError("design lacks the group column.")
    window = design.groupby(GROUP).agg(start=("t0_utc", "min"), end=("target_mid_utc", "max"))
    window = window.sort_values("start")
    violations: list[BufferViolation] = []
    starts = window["start"].to_numpy()
    ends = window["end"].to_numpy()
    ids = window.index.to_numpy()
    for i in range(1, len(window)):
        gap_h = (starts[i] - ends[i - 1]) / np.timedelta64(1, "h")
        if gap_h < buffer_h:
            violations.append(BufferViolation(int(ids[i - 1]), int(ids[i]), float(gap_h)))
    return violations


__all__ = ["BufferViolation", "check_group_buffer", "grouped_folds"]
