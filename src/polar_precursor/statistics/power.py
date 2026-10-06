"""Power bookkeeping for the paired storm test (main plan, "Güç").

Detectable mean difference at 80 % power and two-sided 0.05 is approximately
2.8 × SD / √G, with SD the storm-to-storm standard deviation of the paired loss
difference and G the number of storms. The factor 2.8 ≈ z_{0.975} + z_{0.80}
(1.960 + 0.842 = 2.802). The plan labels this an estimate, not a sourced
result; the SD is measured in the pilot.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import pandas as pd

POWER_FACTOR = 1.959964 + 0.841621  # z_{0.975} + z_{0.80}


def detectable_difference_sd(n_storms: int, *, factor: float = POWER_FACTOR) -> float:
    """Smallest detectable mean difference in units of the per-storm SD."""
    if n_storms < 2:
        raise ValueError("n_storms must be at least 2.")
    return factor / math.sqrt(n_storms)


def required_storms(effect_sd: float, *, factor: float = POWER_FACTOR) -> int:
    """Storms needed to detect a mean difference of ``effect_sd`` SDs."""
    if effect_sd <= 0.0:
        raise ValueError("effect_sd must be positive.")
    return math.ceil((factor / effect_sd) ** 2)


def power_table(
    storm_counts: Sequence[int], *, sd_loss_difference: float | None = None
) -> pd.DataFrame:
    """Detectable difference per G, optionally in loss units given the pilot SD."""
    rows = []
    for g in storm_counts:
        row: dict[str, float] = {"n_storms": float(g), "detectable_sd": detectable_difference_sd(g)}
        if sd_loss_difference is not None:
            row["detectable_loss_difference"] = row["detectable_sd"] * sd_loss_difference
        rows.append(row)
    return pd.DataFrame(rows)


__all__ = ["POWER_FACTOR", "detectable_difference_sd", "power_table", "required_storms"]
