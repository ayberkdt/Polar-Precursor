"""Index and geometry features at a forecast time, with the same causal rule
as the driver features.

The A-layer feature table (plans/06) has three groups that are not solar-wind
drivers:

``index`` (this module, :class:`IndexFeatureBuilder`)
    F10.7 of the previous day and its centred 81-day mean, daily Ap, the Kp of
    the current 3-hour interval (GFZ daily table); ap30 of the latest
    *complete* half hour and its means over the last 0-3 h and 3-6 h (GFZ
    Hp30/ap30 table); Dst of the latest complete hour (Kyoto).
``symh`` (added to the driver builder)
    SYM-H look-back window means, same edges as the driver windows.
``geometry`` (:func:`geometry_features`)
    Target local solar time and day of year as sine/cosine pairs, altitude,
    lead time.

Causality: a half-hourly or hourly index is only known once its interval has
ended, so the value used at ``t0`` is the last interval whose *end* is at or
before ``t0``. The daily F10.7 convention is already "previous day"; the
centred 81-day mean is not causal by construction (it needs 40 days after the
epoch) and is kept because NRLMSIS uses it, but it is flagged in
``feature_names`` so a strictly real-time variant can drop it.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from space_environment.common.timeutil import require_utc
from space_environment.io.gfz import HpoRecord
from space_environment.io.kyoto import latest_complete_hour
from space_environment.physics.space_weather import IndexProvider

HALF_HOUR = timedelta(minutes=30)


def _label(hours: float) -> str:
    return f"{hours:g}".replace(".", "p")


@dataclass(frozen=True, slots=True)
class IndexFeatureConfig:
    ap30_window_edges_h: tuple[float, ...] = (0.0, 3.0, 6.0)
    ap30_min_valid_fraction: float = 0.5

    def __post_init__(self) -> None:
        edges = self.ap30_window_edges_h
        if list(edges) != sorted(set(edges)) or edges[0] < 0.0 or len(edges) < 2:
            raise ValueError("ap30_window_edges_h must be non-negative, strictly increasing.")


class IndexFeatureBuilder:
    """Index features at forecast times from GFZ daily, Hp30/ap30 and Kyoto Dst sources.

    ``hpo`` and ``dst`` are optional; their features are NaN when absent, so a
    table built without them has the same columns.
    """

    def __init__(
        self,
        daily: IndexProvider,
        *,
        hpo: Sequence[HpoRecord] | None = None,
        dst: pd.DataFrame | None = None,
        config: IndexFeatureConfig | None = None,
    ) -> None:
        self.daily = daily
        self.dst = dst
        self.config = config or IndexFeatureConfig()
        if hpo is None:
            self._ap30 = None
        else:
            starts = pd.DatetimeIndex([record.start for record in hpo], name="start_utc")
            if not starts.is_monotonic_increasing or starts.has_duplicates:
                raise ValueError("Hp30/ap30 records must be in strictly increasing order.")
            values = np.array(
                [np.nan if record.ap30 is None else float(record.ap30) for record in hpo]
            )
            # Index the series by interval END: the value is known from then on.
            self._ap30 = pd.Series(values, index=starts + HALF_HOUR)

    @property
    def feature_names(self) -> list[str]:
        edges = self.config.ap30_window_edges_h
        windows = [
            f"ap30_lag_{_label(near)}_{_label(far)}h"
            for near, far in zip(edges[:-1], edges[1:], strict=True)
        ]
        return [
            "f107_prev_day_sfu",
            "f107a_centred_sfu",  # not causal: needs 40 days after t0
            "ap_daily",
            "kp_current_3h",
            "ap30_latest",
            *windows,
            "dst_latest_hour_nt",
        ]

    def features_at(self, t0: pd.Timestamp) -> dict[str, float]:
        moment = require_utc(t0.to_pydatetime())
        state = self.daily.get(moment)
        features: dict[str, float] = {
            "f107_prev_day_sfu": state.f107,
            "f107a_centred_sfu": state.f107a,
            "ap_daily": state.ap_daily,
            "kp_current_3h": float("nan") if state.kp is None else state.kp,
        }
        features.update(self._ap30_features(t0))
        features["dst_latest_hour_nt"] = (
            float("nan") if self.dst is None else latest_complete_hour(self.dst, t0)
        )
        return features

    def _ap30_features(self, t0: pd.Timestamp) -> dict[str, float]:
        edges = self.config.ap30_window_edges_h
        names = [
            f"ap30_lag_{_label(near)}_{_label(far)}h"
            for near, far in zip(edges[:-1], edges[1:], strict=True)
        ]
        out = {"ap30_latest": float("nan"), **{name: float("nan") for name in names}}
        if self._ap30 is None:
            return out
        known = self._ap30.loc[:t0]  # intervals that ended at or before t0
        if known.empty:
            return out
        out["ap30_latest"] = float(known.iloc[-1])
        for name, (near, far) in zip(names, zip(edges[:-1], edges[1:], strict=True), strict=True):
            start = t0 - pd.Timedelta(far, unit="h")
            stop = t0 - pd.Timedelta(near, unit="h")
            window = known.loc[known.index > start].loc[:stop]
            expected = int(round((far - near) * 2))  # half-hour intervals in the window
            if (
                expected > 0
                and window.notna().sum() >= self.config.ap30_min_valid_fraction * expected
            ):
                out[name] = float(window.mean())
        return out

    def table(self, epochs: Sequence[pd.Timestamp]) -> pd.DataFrame:
        rows = {epoch: self.features_at(epoch) for epoch in epochs}
        table = pd.DataFrame.from_dict(rows, orient="index", columns=self.feature_names)
        table.index = pd.DatetimeIndex(table.index, name="t0_utc")
        return table


GEOMETRY_FEATURE_NAMES: tuple[str, ...] = (
    "target_lst_sin",
    "target_lst_cos",
    "doy_sin",
    "doy_cos",
    "altitude_km",
    "lead_time_h",
)


def geometry_features(
    t0: datetime,
    *,
    lead_time_h: float,
    target_local_solar_time_h: float,
    altitude_m: float,
) -> dict[str, float]:
    """Sine/cosine encodings of target local time and day of year, altitude, lead time.

    Local solar time and day of year are periodic, so their sine and cosine
    enter a linear model without a jump at midnight or new year.
    """
    moment = require_utc(t0)
    if lead_time_h < 0.0:
        raise ValueError("lead_time_h must be non-negative.")
    if not 0.0 <= target_local_solar_time_h < 24.0:
        raise ValueError("target_local_solar_time_h must lie in [0, 24).")
    if not math.isfinite(altitude_m):
        raise ValueError("altitude_m must be finite.")
    lst_angle = 2.0 * math.pi * target_local_solar_time_h / 24.0
    doy_angle = 2.0 * math.pi * (moment.timetuple().tm_yday - 1) / 365.25
    return {
        "target_lst_sin": math.sin(lst_angle),
        "target_lst_cos": math.cos(lst_angle),
        "doy_sin": math.sin(doy_angle),
        "doy_cos": math.cos(doy_angle),
        "altitude_km": altitude_m / 1000.0,
        "lead_time_h": lead_time_h,
    }


__all__ = [
    "GEOMETRY_FEATURE_NAMES",
    "IndexFeatureBuilder",
    "IndexFeatureConfig",
    "geometry_features",
]
