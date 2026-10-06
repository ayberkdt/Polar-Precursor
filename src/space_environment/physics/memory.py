"""Causal memory features of a driver time series.

The thermosphere responds to solar-wind forcing with a delay and with memory,
so a forecast feature is rarely the instantaneous driver. Two forms are
provided, both strictly causal: a value at time t uses samples at or before t
and nothing later.

``exponential_memory``
    The time-weighted integral of Liu et al. (2010), Ann. Geophys. 28, 1633,
    Eq. (8): ``mean(t, tau) = int x(t') e^{(t'-t)/tau} dt' / int e^{(t'-t)/tau} dt'``.
    Liu et al. use tau = 3 h and report weak sensitivity for 1 h to 10 h.
``lagged_window_means``
    Plain means over a set of look-back windows ending at the forecast time.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import numpy.typing as npt
import pandas as pd

FloatArray = npt.NDArray[np.float64]


def exponential_memory(
    values: npt.ArrayLike,
    *,
    step_s: float,
    tau_s: float,
    min_weight_fraction: float = 0.5,
) -> FloatArray:
    """Exponentially weighted causal mean of a regularly sampled series.

    Missing samples (NaN) carry no weight: the mean is taken over the samples
    that exist, with their exponential weights. ``min_weight_fraction`` is the
    share of the full (infinite-history, gap-free) weight that must be present;
    below it the output is NaN. This covers both the start of the series and
    long data gaps, where a weighted mean would otherwise rest on stale values.
    """
    if step_s <= 0.0 or tau_s <= 0.0:
        raise ValueError("step_s and tau_s must be positive.")
    if not 0.0 <= min_weight_fraction <= 1.0:
        raise ValueError("min_weight_fraction must lie in [0, 1].")
    series = np.asarray(values, dtype=np.float64)
    if series.ndim != 1:
        raise ValueError("values must be one-dimensional.")
    decay = float(np.exp(-step_s / tau_s))
    full_weight = 1.0 / (1.0 - decay)
    out = np.full(series.shape, np.nan)
    weighted_sum = 0.0
    weight = 0.0
    for index, value in enumerate(series):
        weighted_sum *= decay
        weight *= decay
        if not np.isnan(value):
            weighted_sum += value
            weight += 1.0
        if weight >= min_weight_fraction * full_weight and weight > 0.0:
            out[index] = weighted_sum / weight
    return out


def lagged_window_means(
    series: pd.Series,
    at: pd.Timestamp,
    *,
    edges_h: Sequence[float] = (0.0, 1.0, 2.0, 3.0, 4.5, 6.0),
    min_valid_fraction: float = 0.5,
) -> FloatArray:
    """Means of ``series`` over look-back windows ending at ``at``.

    Window i covers ``(at - edges_h[i+1], at - edges_h[i]]``. The default edges
    give 0-1, 1-2, 2-3, 3-4.5 and 4.5-6 h, which span the 0-4.5 h delays of
    Liu et al. (2010) and the 180-350 min low-latitude lags of Weimer et al.
    (2023). A window with less than ``min_valid_fraction`` of its samples
    present returns NaN. Samples after ``at`` are never read.
    """
    if list(edges_h) != sorted(edges_h) or len(set(edges_h)) != len(edges_h) or edges_h[0] < 0:
        raise ValueError("edges_h must be non-negative and strictly increasing.")
    if not isinstance(series.index, pd.DatetimeIndex) or not series.index.is_monotonic_increasing:
        raise ValueError("series must have an increasing DatetimeIndex.")
    out = np.full(len(edges_h) - 1, np.nan)
    for i, (near_h, far_h) in enumerate(zip(edges_h[:-1], edges_h[1:], strict=True)):
        start = at - pd.Timedelta(far_h, unit="h")
        stop = at - pd.Timedelta(near_h, unit="h")
        left = series.index.searchsorted(start, side="right")
        right = series.index.searchsorted(stop, side="right")
        window = series.iloc[left:right]
        if len(window) and window.notna().mean() >= min_valid_fraction:
            out[i] = float(window.mean())
    return out


__all__ = ["exponential_memory", "lagged_window_means"]
