"""Nested, storm-grouped cross-validation producing out-of-fold predictions.

Outer loop: ``cv.outer_folds`` grouped folds. Inner loop (fitted steps only):
``cv.inner_folds`` grouped folds inside the training part, used solely to pick
the ridge penalty from ``ridge.alphas`` by pooled inner MSE. Scaling and
imputation are fitted on the training rows of each (outer or inner) fold. The
result holds one prediction per row and model, the outer fold id of each row,
and the penalty chosen in each outer fold, so a later refit (permutation test)
can reuse the penalties instead of re-tuning.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from polar_precursor.config import ExperimentConfig
from polar_precursor.design.ladder import GROUP, PERSISTENCE, TARGET, ModelSpec
from polar_precursor.models.ridge import fit_ridge
from polar_precursor.validation.folds import grouped_folds


@dataclass(frozen=True, slots=True)
class CvResult:
    predictions: pd.DataFrame  # row-aligned with the design; one column per model
    fold: np.ndarray  # outer fold id per row
    alphas: dict[str, tuple[float, ...]] = field(default_factory=dict)  # per model, per outer fold


def _select_alpha(train: pd.DataFrame, columns: list[str], config: ExperimentConfig) -> float:
    groups = train[GROUP].to_numpy()
    n_groups = len(np.unique(groups))
    inner_folds = min(config.cv.inner_folds, n_groups)
    if inner_folds < 2 or len(config.ridge.alphas) == 1:
        return config.ridge.alphas[0]
    fold = grouped_folds(groups, train["t0_utc"].to_numpy(), inner_folds)
    y = train[TARGET].to_numpy(dtype=np.float64)
    errors = np.zeros(len(config.ridge.alphas))
    for k in range(inner_folds):
        fit_rows = fold != k
        test_rows = ~fit_rows
        for position, alpha in enumerate(config.ridge.alphas):
            model = fit_ridge(
                train[fit_rows],
                columns,
                y[fit_rows],
                alpha=alpha,
                standardise=config.ridge.standardise,
            )
            residual = y[test_rows] - model.predict(train[test_rows])
            errors[position] += float(np.sum(residual**2))
    return config.ridge.alphas[int(np.argmin(errors))]


def predict_step(
    spec: ModelSpec,
    train: pd.DataFrame,
    test: pd.DataFrame,
    *,
    alpha: float | None,
    config: ExperimentConfig,
) -> tuple[np.ndarray, float]:
    """Fit ``spec`` on ``train`` (tuning alpha when None) and predict ``test``."""
    if spec.name == "B0":
        return np.zeros(len(test)), float("nan")
    if spec.name == "B1":
        return test[PERSISTENCE].to_numpy(dtype=np.float64), float("nan")
    if not spec.fitted:
        raise ValueError(f"{spec.name}: unfitted step without a prediction rule.")
    columns = spec.columns(train)
    chosen = _select_alpha(train, columns, config) if alpha is None else alpha
    model = fit_ridge(
        train,
        columns,
        train[TARGET].to_numpy(dtype=np.float64),
        alpha=chosen,
        standardise=config.ridge.standardise,
    )
    return model.predict(test), chosen


def cross_validate(
    design: pd.DataFrame,
    specs: list[ModelSpec],
    config: ExperimentConfig,
    *,
    fold: np.ndarray | None = None,
    fixed_alphas: dict[str, tuple[float, ...]] | None = None,
) -> CvResult:
    """Out-of-fold predictions for every ladder step.

    ``fold`` overrides the fold assignment (so a permuted design can be scored
    on the same folds); ``fixed_alphas`` skips the inner loop for the named
    models and uses the given penalty per outer fold.
    """
    if design.empty:
        raise ValueError("design is empty.")
    if fold is None:
        fold = grouped_folds(
            design[GROUP].to_numpy(), design["t0_utc"].to_numpy(), config.cv.outer_folds
        )
    n_folds = int(fold.max()) + 1
    predictions = pd.DataFrame(
        np.full((len(design), len(specs)), np.nan), columns=[s.name for s in specs]
    )
    alphas: dict[str, list[float]] = {s.name: [] for s in specs}
    for k in range(n_folds):
        test_rows = fold == k
        train = design[~test_rows]
        test = design[test_rows]
        for spec in specs:
            alpha = None
            if fixed_alphas is not None and spec.name in fixed_alphas:
                alpha = fixed_alphas[spec.name][k]
            prediction, chosen = predict_step(spec, train, test, alpha=alpha, config=config)
            predictions.loc[test_rows, spec.name] = prediction
            alphas[spec.name].append(chosen)
    return CvResult(predictions, fold, {name: tuple(v) for name, v in alphas.items()})


__all__ = ["CvResult", "cross_validate", "predict_step"]
