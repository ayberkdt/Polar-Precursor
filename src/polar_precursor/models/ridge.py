"""Ridge regression in closed form, with train-only standardisation and imputation.

No third-party ML dependency: the thesis needs interpretable coefficients and a
fit that is cheap enough to repeat thousands of times (permutation test,
skeleton test). The intercept is not penalised; features are centred and
scaled with statistics of the training rows only; missing values are replaced
by the training mean of their column (plan 07: scaling and imputation are fitted
inside each fold).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class Preprocessor:
    columns: tuple[str, ...]
    means: np.ndarray
    scales: np.ndarray

    @classmethod
    def fit(cls, frame: pd.DataFrame, columns: list[str], *, standardise: bool) -> Preprocessor:
        values = frame.loc[:, columns].to_numpy(dtype=np.float64)
        with np.errstate(all="ignore"):
            means = np.nanmean(values, axis=0)
            scales = np.nanstd(values, axis=0) if standardise else np.ones(len(columns))
        means = np.where(np.isfinite(means), means, 0.0)
        scales = np.where(np.isfinite(scales) & (scales > 0.0), scales, 1.0)
        return cls(tuple(columns), means, scales)

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        values = frame.loc[:, list(self.columns)].to_numpy(dtype=np.float64)
        filled = np.where(np.isnan(values), self.means, values)
        return (filled - self.means) / self.scales


@dataclass(frozen=True, slots=True)
class RidgeModel:
    preprocessor: Preprocessor
    intercept: float
    coefficients: np.ndarray  # on standardised features
    alpha: float

    def predict(self, frame: pd.DataFrame) -> np.ndarray:
        return self.intercept + self.preprocessor.transform(frame) @ self.coefficients

    def coefficient_table(self) -> pd.Series:
        """Coefficients per standardised feature (change in y per one SD of the feature)."""
        return pd.Series(self.coefficients, index=list(self.preprocessor.columns), name="beta")


def fit_ridge(
    frame: pd.DataFrame,
    columns: list[str],
    target: np.ndarray,
    *,
    alpha: float,
    standardise: bool = True,
) -> RidgeModel:
    """Minimise ||y − b0 − Zβ||² + α||β||² with Z the standardised features."""
    if alpha < 0.0:
        raise ValueError("alpha must be non-negative.")
    y = np.asarray(target, dtype=np.float64)
    if np.any(~np.isfinite(y)):
        raise ValueError("target contains non-finite values.")
    preprocessor = Preprocessor.fit(frame, columns, standardise=standardise)
    z = preprocessor.transform(frame)
    intercept = float(y.mean())
    centred = y - intercept
    gram = z.T @ z + alpha * np.eye(z.shape[1])
    beta = np.linalg.solve(gram, z.T @ centred)
    return RidgeModel(preprocessor, intercept, beta, alpha)


__all__ = ["Preprocessor", "RidgeModel", "fit_ridge"]
