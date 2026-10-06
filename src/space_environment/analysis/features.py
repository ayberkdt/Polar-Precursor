"""Solar-wind driver features at a forecast time, built so they cannot see
past it.

For a forecast issued at ``t0`` the admissible inputs are samples at or
before ``t0``. Every feature here is computed from ``frame.loc[:t0]`` only:
instantaneous values are the sample at ``t0``, memory integrals are causal by
construction (``exponential_memory``), look-back window means end at ``t0``,
and the shock flag counts only shocks confirmed by ``t0``. ``tests`` check
that corrupting every sample after ``t0`` leaves the features unchanged.

Feature names
-------------
``bz_gsm_nt, by_gsm_nt, b_magnitude_nt, flow_speed_km_s, proton_density_cm3,
flow_pressure_npa, sym_h_nt``
    OMNI values at ``t0`` (NaN when OMNI has none).
``em_mv_m, em_saturated_mv_m, newell``
    Coupling functions at ``t0``.
``em_mem_{tau}h, bz_south_mem_{tau}h``
    Exponentially weighted causal means with time constant ``tau`` hours.
``em_lag_{a}_{b}h, bz_lag_{a}_{b}h, symh_lag_{a}_{b}h``
    Means over the window ``(t0 - b h, t0 - a h]``.
``em_valid_6h``
    Fraction of the last six hours with a merging field value: how much
    driver information exists at all (the OMNI-gap problem).
``hours_since_shock``
    From the latest confirmed shock, NaN if none is known.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

import numpy as np
import pandas as pd

from space_environment.physics.coupling import (
    merging_electric_field_mv_m,
    newell_coupling,
    saturated_merging_field_mv_m,
)
from space_environment.physics.memory import exponential_memory, lagged_window_means
from space_environment.physics.shock import ShockCandidate, hours_since_last_shock

_INSTANT_COLUMNS = (
    "bz_gsm_nt",
    "by_gsm_nt",
    "b_magnitude_nt",
    "flow_speed_km_s",
    "proton_density_cm3",
    "flow_pressure_npa",
    "sym_h_nt",
)


@dataclass(frozen=True, slots=True)
class DriverFeatureConfig:
    memory_taus_h: tuple[float, ...] = (1.0, 3.0, 6.0, 10.0, 17.0)
    lag_edges_h: tuple[float, ...] = (0.0, 1.0, 2.0, 3.0, 4.5, 6.0)
    memory_min_weight_fraction: float = 0.5
    lag_min_valid_fraction: float = 0.5

    def __post_init__(self) -> None:
        if any(tau <= 0.0 for tau in self.memory_taus_h):
            raise ValueError("memory_taus_h must be positive.")
        if list(self.lag_edges_h) != sorted(set(self.lag_edges_h)) or self.lag_edges_h[0] < 0:
            raise ValueError("lag_edges_h must be non-negative and strictly increasing.")


def _label(hours: float) -> str:
    return f"{hours:g}".replace(".", "p")


class DriverFeatureBuilder:
    """Features at forecast times from a 1-minute OMNI frame."""

    def __init__(
        self,
        omni: pd.DataFrame,
        *,
        config: DriverFeatureConfig | None = None,
        shocks: tuple[ShockCandidate, ...] = (),
    ) -> None:
        missing = [column for column in _INSTANT_COLUMNS if column not in omni.columns]
        if missing:
            raise ValueError(f"omni lacks columns {missing}.")
        index = omni.index
        if not isinstance(index, pd.DatetimeIndex) or len(index) < 2:
            raise ValueError("omni must have a DatetimeIndex with at least two samples.")
        if not np.all(np.diff(index.to_numpy()) == np.timedelta64(60, "s")):
            raise ValueError("omni must be regularly sampled at 1 minute (gaps as NaN).")
        self.config = config or DriverFeatureConfig()
        self.shocks = shocks
        frame = omni.loc[:, list(_INSTANT_COLUMNS)].astype(np.float64).copy()
        speed = frame["flow_speed_km_s"].to_numpy()
        by = frame["by_gsm_nt"].to_numpy()
        bz = frame["bz_gsm_nt"].to_numpy()
        frame["em_mv_m"] = merging_electric_field_mv_m(speed, by, bz)
        frame["em_saturated_mv_m"] = saturated_merging_field_mv_m(frame["em_mv_m"].to_numpy())
        frame["newell"] = newell_coupling(speed, by, bz)
        frame["bz_south_nt"] = np.where(np.isnan(bz), np.nan, np.maximum(-bz, 0.0))
        for tau in self.config.memory_taus_h:
            for source, target in (("em_mv_m", "em_mem"), ("bz_south_nt", "bz_south_mem")):
                frame[f"{target}_{_label(tau)}h"] = exponential_memory(
                    frame[source].to_numpy(),
                    step_s=60.0,
                    tau_s=tau * 3600.0,
                    min_weight_fraction=self.config.memory_min_weight_fraction,
                )
        self._frame = frame
        self._memory_columns = [column for column in frame.columns if "_mem_" in column]

    @property
    def feature_names(self) -> list[str]:
        edges = self.config.lag_edges_h
        lag_names = [
            f"{prefix}_lag_{_label(near)}_{_label(far)}h"
            for prefix in ("em", "bz", "symh")
            for near, far in zip(edges[:-1], edges[1:], strict=True)
        ]
        return [
            *_INSTANT_COLUMNS,
            "em_mv_m",
            "em_saturated_mv_m",
            "newell",
            *self._memory_columns,
            *lag_names,
            "em_valid_6h",
            "hours_since_shock",
        ]

    def features_at(self, t0: pd.Timestamp) -> dict[str, float]:
        """Feature values for a forecast issued at ``t0`` (must be a frame sample time)."""
        if t0 not in self._frame.index:
            raise ValueError(
                f"{t0.isoformat()} is not a sample time of the OMNI frame "
                f"({self._frame.index[0].isoformat()} to {self._frame.index[-1].isoformat()})."
            )
        past = self._frame.loc[:t0]
        row = past.iloc[-1]
        features: dict[str, float] = {
            column: float(row[column])
            for column in (*_INSTANT_COLUMNS, "em_mv_m", "em_saturated_mv_m", "newell")
        }
        for column in self._memory_columns:
            features[column] = float(row[column])
        edges = self.config.lag_edges_h
        for prefix, source in (("em", "em_mv_m"), ("bz", "bz_gsm_nt"), ("symh", "sym_h_nt")):
            means = lagged_window_means(
                past[source],
                t0,
                edges_h=edges,
                min_valid_fraction=self.config.lag_min_valid_fraction,
            )
            windows = zip(edges[:-1], edges[1:], strict=True)
            for (near, far), value in zip(windows, means, strict=True):
                features[f"{prefix}_lag_{_label(near)}_{_label(far)}h"] = float(value)
        six_hours_ago = t0 - pd.Timedelta(6, unit="h") + pd.Timedelta(1, unit="m")
        six_hours = past["em_mv_m"].loc[six_hours_ago:]
        features["em_valid_6h"] = float(six_hours.notna().sum() / 360.0)
        features["hours_since_shock"] = hours_since_last_shock(self.shocks, t0)
        return features

    def table(self, epochs: Iterable[pd.Timestamp]) -> pd.DataFrame:
        """Feature table indexed by forecast time, columns in ``feature_names`` order."""
        rows = {epoch: self.features_at(epoch) for epoch in epochs}
        table = pd.DataFrame.from_dict(rows, orient="index", columns=self.feature_names)
        table.index = pd.DatetimeIndex(table.index, name="t0_utc")
        return table


__all__ = ["DriverFeatureBuilder", "DriverFeatureConfig"]
