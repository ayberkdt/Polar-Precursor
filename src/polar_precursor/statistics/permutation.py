"""Confirmatory test: permute the polar input block across storms, refit, compare.

Plan 07 decision 8: shuffle the polar columns between samples of different
storms within strata of storm class and lead-time bin, refit the candidate
model on the same folds, and place the observed primary metric in the null
distribution. The penalty chosen on the real data is reused per fold (the
inner loop is not repeated for every permutation; this is a documented
simplification, since re-tuning 1000 times would cost 5× more fits and the
penalty is a nuisance parameter here). Row-level shuffling within a stratum
breaks the polar→target link while keeping each stratum's marginal
distribution; a sample may occasionally receive the polar block of another
sample from its own storm, which only makes the null slightly conservative.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from polar_precursor.config import ExperimentConfig
from polar_precursor.design.ladder import LADDER, polar_columns
from polar_precursor.metrics.scores import per_storm_losses
from polar_precursor.statistics.bootstrap import relative_rmse_reduction
from polar_precursor.validation.crossval import CvResult, cross_validate


@dataclass(frozen=True, slots=True)
class PermutationResult:
    reference: str
    candidate: str
    observed: float
    null: np.ndarray
    n_resamples: int
    seed: int
    one_sided: bool

    @property
    def p_value(self) -> float:
        extreme = (
            self.null >= self.observed
            if self.one_sided
            else np.abs(self.null) >= abs(self.observed)
        )
        return float((1 + int(extreme.sum())) / (self.n_resamples + 1))

    def line(self) -> str:
        side = "one-sided" if self.one_sided else "two-sided"
        return (
            f"permutation ({side}, {self.n_resamples} resamples, seed {self.seed}): observed "
            f"{100 * self.observed:+.2f}%, null mean {100 * self.null.mean():+.2f}% "
            f"(SD {100 * self.null.std(ddof=1):.2f}%), p = {self.p_value:.4f}"
        )


def permute_polar_block(
    design: pd.DataFrame, *, strata: Sequence[str], rng: np.random.Generator
) -> pd.DataFrame:
    """Copy of ``design`` with the polar columns shuffled among rows of each stratum."""
    columns = polar_columns(design)
    if not columns:
        raise ValueError("design has no polar columns to permute.")
    permuted = design.copy()
    block = design[columns].to_numpy()
    if strata:
        keys = design[list(strata)].astype(str).agg("|".join, axis=1).to_numpy()
    else:
        keys = np.zeros(len(design), dtype=np.int64)
    new_block = block.copy()
    for key in np.unique(keys):
        rows = np.where(keys == key)[0]
        new_block[rows] = block[rng.permutation(rows)]
    permuted[columns] = new_block
    return permuted


def _statistic(per_storm: pd.DataFrame, reference: str, candidate: str, weight: str) -> float:
    ok = np.isfinite(per_storm[reference]) & np.isfinite(per_storm[candidate])
    table = per_storm[ok]
    weights = (
        np.ones(len(table)) if weight == "equal" else table["n_samples"].to_numpy(dtype=np.float64)
    )
    return relative_rmse_reduction(
        table[reference].to_numpy(dtype=np.float64),
        table[candidate].to_numpy(dtype=np.float64),
        weights,
    )


def permutation_test(
    design: pd.DataFrame,
    cv_result: CvResult,
    config: ExperimentConfig,
    *,
    n_resamples: int | None = None,
    seed: int | None = None,
) -> PermutationResult:
    """Null distribution of the primary metric with the polar block permuted across storms."""
    reference = config.test.reference_model
    candidate = config.test.candidate_model
    n = config.test.permutation_resamples if n_resamples is None else n_resamples
    used_seed = config.test.permutation_seed if seed is None else seed
    weight = config.test.storm_weight
    observed_losses = per_storm_losses(design, cv_result.predictions, [reference, candidate])
    observed = _statistic(observed_losses, reference, candidate, weight)
    reference_losses = observed_losses[reference]
    rng = np.random.default_rng(used_seed)
    spec = LADDER[candidate]
    fixed = {candidate: cv_result.alphas[candidate]}
    null = np.empty(n)
    for i in range(n):
        permuted = permute_polar_block(design, strata=config.test.permutation_strata, rng=rng)
        refit = cross_validate(permuted, [spec], config, fold=cv_result.fold, fixed_alphas=fixed)
        candidate_losses = per_storm_losses(permuted, refit.predictions, [candidate])
        table = pd.DataFrame(
            {
                reference: reference_losses,
                candidate: candidate_losses[candidate],
                "n_samples": observed_losses["n_samples"],
            }
        )
        null[i] = _statistic(table, reference, candidate, weight)
    return PermutationResult(
        reference, candidate, observed, null, n, used_seed, config.test.one_sided
    )


__all__ = ["PermutationResult", "permutation_test", "permute_polar_block"]
