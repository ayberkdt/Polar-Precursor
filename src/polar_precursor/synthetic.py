"""Synthetic storms with a known polar contribution (plan 07, skeleton test).

The generator produces a design frame in the real column convention, so the
whole chain (ladder → grouped CV → bootstrap → permutation) runs on it
unchanged. Per storm, at a 46-minute pass cadence:

    d_t   = 0.8 d_{t-1} + η_t                     driver (observed at t0 and, for B3k, at target)
    h_t   = 0.7 h_{t-1} + ζ_t                     hidden high-latitude heating
    x_t   = s + a x_{t-1} + b d_t + γ h_{t-3} + ε_t  low-latitude log density ratio
    p_t   = h_t + ν_t                             polar pass (north; south adds more noise)

``polar_gain`` γ is the knob: 0 makes the polar block independent of the target
given drivers and history (null case); γ > 0 is information available only
through the polar passes, lagged by three cadences (≈ 2.3 h, the lead seen on
29 Oct 2003). ``s`` is a storm random effect so storms differ in level.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from polar_precursor.design.ladder import GROUP, INTENSITY, LEAD_BIN, PERSISTENCE, TARGET
from polar_precursor.design.matrix import lead_bin_labels

CLASSES: tuple[str, ...] = ("weak", "moderate", "strong", "severe", "extreme")
CADENCE_MIN = 46.0


@dataclass(frozen=True, slots=True)
class SyntheticConfig:
    n_storms: int = 30
    samples_per_storm: int = 40
    polar_gain: float = 0.0
    polar_lag_steps: int = 3
    low_ar: float = 0.6
    driver_gain: float = 0.5
    storm_sd: float = 0.3
    noise_sd: float = 0.2
    polar_noise_sd: float = 0.3
    inputs_low: int = 4
    inputs_polar: int = 4
    n_driver_lags: int = 3
    lead_steps: tuple[int, ...] = (2, 3, 4, 5)  # 92-230 min at 46-min cadence
    lead_bin_edges_min: tuple[float, ...] = (60.0, 105.0, 150.0, 195.0, 240.0, 270.0)
    storm_spacing_h: float = 200.0
    start: str = "2003-01-01T00:00:00Z"

    def __post_init__(self) -> None:
        if self.n_storms < 2 or self.samples_per_storm < 2:
            raise ValueError("need at least two storms and two samples per storm.")
        if not 0.0 <= self.low_ar < 1.0:
            raise ValueError("low_ar must lie in [0, 1).")


def synthetic_design(config: SyntheticConfig, *, seed: int) -> pd.DataFrame:
    """Design frame with known structure; ``seed`` fixes every random draw."""
    rng = np.random.default_rng(seed)
    warmup = max(
        config.inputs_low, config.inputs_polar, config.n_driver_lags, config.polar_lag_steps
    )
    rows: list[dict[str, object]] = []
    start = pd.Timestamp(config.start)
    step = pd.Timedelta(CADENCE_MIN, unit="m")
    max_lead = max(config.lead_steps)
    for storm in range(config.n_storms):
        length = warmup + config.samples_per_storm + max_lead
        d = np.zeros(length)
        h = np.zeros(length)
        x = np.zeros(length)
        level = rng.normal(0.0, config.storm_sd)
        for t in range(1, length):
            d[t] = 0.8 * d[t - 1] + rng.normal(0.0, 1.0)
            h[t] = 0.7 * h[t - 1] + rng.normal(0.0, 1.0)
            lagged_h = h[t - config.polar_lag_steps] if t >= config.polar_lag_steps else 0.0
            x[t] = (
                level
                + config.low_ar * x[t - 1]
                + config.driver_gain * d[t]
                + config.polar_gain * lagged_h
                + rng.normal(0.0, config.noise_sd)
            )
        p_north = h + rng.normal(0.0, config.polar_noise_sd, size=length)
        p_south = h + rng.normal(0.0, 2.0 * config.polar_noise_sd, size=length)
        mid = 0.5 * x + rng.normal(0.0, config.noise_sd, size=length)
        storm_start = start + pd.Timedelta(storm * config.storm_spacing_h, unit="h")
        intensity = CLASSES[storm % len(CLASSES)]
        for t in range(warmup, warmup + config.samples_per_storm):
            lead = int(rng.choice(config.lead_steps))
            t0 = storm_start + t * step
            row: dict[str, object] = {
                "t0_utc": t0,
                "target_mid_utc": t0 + lead * step,
                "satellite": "SYNTHETIC",
                "lead_time_min": lead * CADENCE_MIN,
                TARGET: float(x[t + lead]),
                PERSISTENCE: float(x[t]),
                GROUP: storm,
                INTENSITY: intensity,
            }
            for k in range(1, config.inputs_low + 1):
                row[f"low_lag{k}"] = float(x[t - k + 1])
            for k in range(1, config.inputs_polar + 1):
                row[f"polar_north_lag{k}"] = float(p_north[t - k + 1])
                row[f"polar_south_lag{k}"] = float(p_south[t - k + 1])
            row["mid_same"] = float(mid[t])
            for k in range(config.n_driver_lags):
                row[f"drv_d_lag{k}"] = float(d[t - k])
            row["drv_oracle_d_target"] = float(d[t + lead])
            lst = rng.uniform(0.0, 24.0)
            row["geo_lead_time_h"] = lead * CADENCE_MIN / 60.0
            row["geo_target_lst_sin"] = float(np.sin(2.0 * np.pi * lst / 24.0))
            row["geo_target_lst_cos"] = float(np.cos(2.0 * np.pi * lst / 24.0))
            rows.append(row)
    design = pd.DataFrame(rows)
    design[LEAD_BIN] = lead_bin_labels(
        design["lead_time_min"].to_numpy(), config.lead_bin_edges_min
    )
    return design


__all__ = ["CADENCE_MIN", "CLASSES", "SyntheticConfig", "synthetic_design"]
