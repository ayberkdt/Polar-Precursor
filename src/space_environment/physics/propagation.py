"""Moving L1 measurements to the bow-shock nose: delay, restamping, binning.

OMNI already time-shifts solar-wind data to the nose with a phase-front
method. Data read directly from a spacecraft at L1 (``io.ace``) must be
shifted by the caller before they are compared with OMNI or used as a
driver. ``ballistic_delay_s`` is the plain ``(x_sc - x_target) / |vx|``
convection delay; the phase-front method is not reproduced here, so the
delay carries an error of the order of minutes that has not been measured
in this project yet.

Sidera destination: ``sidera.physics.space_environment.propagation``.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pandas as pd

FloatArray = npt.NDArray[np.float64]


def ballistic_delay_s(
    x_spacecraft_km: npt.ArrayLike,
    vx_gse_km_s: npt.ArrayLike,
    *,
    x_target_km: float,
) -> FloatArray:
    """Plain convection delay from the spacecraft to ``x_target_km`` (GSE x).

    The solar wind flows anti-sunward, so ``vx_gse_km_s`` is negative; a
    non-negative speed is an error, not a zero delay. A NaN speed gives a
    NaN delay. ``x_target_km`` is explicit because the natural targets differ
    (bow-shock nose for OMNI comparison, magnetopause for coupling studies).
    """
    x_sc = np.asarray(x_spacecraft_km, dtype=np.float64)
    vx = np.asarray(vx_gse_km_s, dtype=np.float64)
    finite = ~np.isnan(vx)
    if np.any(vx[finite] >= 0.0):
        raise ValueError("vx_gse_km_s must be negative (anti-sunward flow) wherever present.")
    delay = np.full(np.broadcast(x_sc, vx).shape, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        np.divide(x_sc - x_target_km, -vx, out=delay, where=finite & ~np.isnan(x_sc))
    return delay


def shift_by_delay(frame: pd.DataFrame, delay_s: npt.ArrayLike) -> pd.DataFrame:
    """Return ``frame`` with each record stamped at ``time + delay``.

    ``delay_s`` is a scalar or one value per record. Records whose delay is
    NaN are dropped, since their arrival time is unknown. The result is sorted,
    because a changing delay can reorder records.
    """
    delay = np.broadcast_to(np.asarray(delay_s, dtype=np.float64), (len(frame),))
    keep = ~np.isnan(delay)
    shifted = frame.loc[keep].copy()
    shifted.index = pd.DatetimeIndex(
        frame.index[keep] + pd.to_timedelta(delay[keep], unit="s"), name=frame.index.name
    )
    return shifted.sort_index()


def minute_means(
    frame: pd.DataFrame,
    *,
    columns: list[str] | None = None,
    min_samples: int = 1,
) -> pd.DataFrame:
    """Average records into 1-minute bins labelled by the bin start.

    This is the cadence of OMNI HRO. A bin with fewer than ``min_samples``
    present values in a column gets NaN in that column.
    """
    if min_samples < 1:
        raise ValueError("min_samples must be at least 1.")
    selected = frame if columns is None else frame[columns]
    grouped = selected.resample("1min", label="left", closed="left")
    means = grouped.mean()
    counts = grouped.count()
    return means.mask(counts < min_samples)


__all__ = ["ballistic_delay_s", "minute_means", "shift_by_delay"]
