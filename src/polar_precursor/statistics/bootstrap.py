"""Primary test: cluster bootstrap over storms of the paired loss difference.

Plan 07 decision 7: ``d_s = MSE_ref,s − MSE_cand,s`` per storm, one value per
storm; the headline number is the relative RMSE reduction with a percentile
confidence interval from resampling storms with replacement (Cameron and
Miller 2015 cluster bootstrap; the reference was not re-read in this project).
Storms are weighted equally by default (decision 2); ``weight="samples"``
weights each storm by its sample count.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class BootstrapResult:
    reference: str
    candidate: str
    n_storms: int
    n_resamples: int
    seed: int
    confidence_level: float
    relative_rmse_reduction: float
    ci_low: float
    ci_high: float
    mean_loss_difference: float
    loss_difference_ci_low: float
    loss_difference_ci_high: float
    fraction_storms_improved: float
    p_one_sided: float  # fraction of resamples where the candidate does not beat the reference

    @property
    def excludes_zero(self) -> bool:
        return self.ci_low > 0.0 or self.ci_high < 0.0

    def line(self) -> str:
        pct = 100.0 * self.confidence_level
        return (
            f"{self.candidate} vs {self.reference}: relative RMSE reduction "
            f"{100 * self.relative_rmse_reduction:+.2f}% "
            f"[{100 * self.ci_low:+.2f}%, {100 * self.ci_high:+.2f}%] ({pct:.0f}% cluster "
            f"bootstrap, {self.n_resamples} resamples, seed {self.seed}, G = {self.n_storms}); "
            f"storms improved {100 * self.fraction_storms_improved:.0f}%, bootstrap p "
            f"{self.p_one_sided:.4f}"
        )


def paired_losses(per_storm: pd.DataFrame, reference: str, candidate: str) -> pd.Series:
    """d_s = MSE_ref,s − MSE_cand,s (positive favours the candidate); NaN storms dropped."""
    d = (per_storm[reference] - per_storm[candidate]).astype(np.float64)
    return d[np.isfinite(d)].rename("loss_difference")


def _weights(per_storm: pd.DataFrame, weight: str) -> np.ndarray:
    if weight == "equal":
        return np.ones(len(per_storm))
    if weight == "samples":
        return per_storm["n_samples"].to_numpy(dtype=np.float64)
    raise ValueError("weight must be 'equal' or 'samples'.")


def relative_rmse_reduction(
    mse_reference: np.ndarray, mse_candidate: np.ndarray, weights: np.ndarray
) -> float:
    """1 − RMSE_cand/RMSE_ref with storm-weighted mean squared errors."""
    total = weights.sum()
    rmse_ref = np.sqrt(np.sum(weights * mse_reference) / total)
    rmse_cand = np.sqrt(np.sum(weights * mse_candidate) / total)
    return float(1.0 - rmse_cand / rmse_ref) if rmse_ref > 0.0 else float("nan")


def cluster_bootstrap(
    per_storm: pd.DataFrame,
    *,
    reference: str,
    candidate: str,
    n_resamples: int,
    seed: int,
    confidence_level: float = 0.95,
    weight: str = "equal",
) -> BootstrapResult:
    """Resample storms with replacement; percentile interval of the primary metric."""
    ok = np.isfinite(per_storm[reference]) & np.isfinite(per_storm[candidate])
    table = per_storm[ok]
    n_storms = len(table)
    if n_storms < 2:
        raise ValueError("at least two storms with both losses are needed.")
    if n_resamples < 1:
        raise ValueError("n_resamples must be positive.")
    mse_ref = table[reference].to_numpy(dtype=np.float64)
    mse_cand = table[candidate].to_numpy(dtype=np.float64)
    weights = _weights(table, weight)
    d = mse_ref - mse_cand
    point = relative_rmse_reduction(mse_ref, mse_cand, weights)
    mean_d = float(np.sum(weights * d) / weights.sum())

    rng = np.random.default_rng(seed)
    draws = rng.integers(0, n_storms, size=(n_resamples, n_storms))
    w = weights[draws]
    total = w.sum(axis=1)
    rmse_ref_b = np.sqrt(np.sum(w * mse_ref[draws], axis=1) / total)
    rmse_cand_b = np.sqrt(np.sum(w * mse_cand[draws], axis=1) / total)
    with np.errstate(divide="ignore", invalid="ignore"):
        reduction_b = 1.0 - rmse_cand_b / rmse_ref_b
    mean_d_b = np.sum(w * d[draws], axis=1) / total
    tail = (1.0 - confidence_level) / 2.0
    lo, hi = np.nanquantile(reduction_b, [tail, 1.0 - tail])
    d_lo, d_hi = np.quantile(mean_d_b, [tail, 1.0 - tail])
    return BootstrapResult(
        reference=reference,
        candidate=candidate,
        n_storms=n_storms,
        n_resamples=n_resamples,
        seed=seed,
        confidence_level=confidence_level,
        relative_rmse_reduction=point,
        ci_low=float(lo),
        ci_high=float(hi),
        mean_loss_difference=mean_d,
        loss_difference_ci_low=float(d_lo),
        loss_difference_ci_high=float(d_hi),
        fraction_storms_improved=float(np.mean(d > 0.0)),
        p_one_sided=float((1 + int(np.sum(~(reduction_b > 0.0)))) / (n_resamples + 1)),
    )


__all__ = ["BootstrapResult", "cluster_bootstrap", "paired_losses", "relative_rmse_reduction"]
