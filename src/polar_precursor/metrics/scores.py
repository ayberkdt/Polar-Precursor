"""Scores on out-of-fold predictions (main plan, "Raporlanacak ölçüler").

Per model: mean and SD of the log-ratio residual (Bruinsma 2021 convention),
RMSE, correlation, skill 1 − MSE/MSE_ref against persistence and against the
reference step; per storm: MSE, peak amplitude and peak timing error. The unit
of the primary analysis is the storm, so ``per_storm_losses`` is the table the
statistics module consumes.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from polar_precursor.design.ladder import GROUP, INTENSITY, LEAD_BIN, TARGET


def score_summary(y: np.ndarray, prediction: np.ndarray) -> dict[str, float]:
    """n, mean and SD of the residual (y − prediction), RMSE and Pearson correlation."""
    y = np.asarray(y, dtype=np.float64)
    prediction = np.asarray(prediction, dtype=np.float64)
    ok = np.isfinite(y) & np.isfinite(prediction)
    n = int(ok.sum())
    if n == 0:
        return {
            "n": 0.0,
            "mean_residual": np.nan,
            "sd_residual": np.nan,
            "rmse": np.nan,
            "correlation": np.nan,
        }
    residual = y[ok] - prediction[ok]
    correlation = np.nan
    if n > 1 and np.std(y[ok]) > 0.0 and np.std(prediction[ok]) > 0.0:
        correlation = float(np.corrcoef(y[ok], prediction[ok])[0, 1])
    return {
        "n": float(n),
        "mean_residual": float(residual.mean()),
        "sd_residual": float(residual.std(ddof=1)) if n > 1 else np.nan,
        "rmse": float(np.sqrt(np.mean(residual**2))),
        "correlation": correlation,
    }


def skill_score(mse: float, mse_reference: float) -> float:
    """1 − MSE/MSE_ref; positive means better than the reference."""
    if not np.isfinite(mse_reference) or mse_reference <= 0.0:
        return float("nan")
    return float(1.0 - mse / mse_reference)


def per_storm_losses(
    design: pd.DataFrame, predictions: pd.DataFrame, models: Sequence[str] | None = None
) -> pd.DataFrame:
    """MSE per storm group and model, with the sample count and class of each group.

    Rows where a model has no prediction (B1 without a same-sector pass) are
    skipped for that model only; ``n_samples`` counts all rows of the group.
    """
    names = list(predictions.columns) if models is None else list(models)
    y = design[TARGET].to_numpy(dtype=np.float64)
    groups = design[GROUP].to_numpy()
    rows: list[dict[str, object]] = []
    for group in np.unique(groups):
        member = groups == group
        row: dict[str, object] = {
            GROUP: int(group),
            "n_samples": int(member.sum()),
            INTENSITY: str(design.loc[member, INTENSITY].iloc[0]),
        }
        for name in names:
            prediction = predictions[name].to_numpy(dtype=np.float64)[member]
            ok = np.isfinite(prediction)
            row[name] = (
                float(np.mean((y[member][ok] - prediction[ok]) ** 2)) if ok.any() else np.nan
            )
        rows.append(row)
    return pd.DataFrame(rows).set_index(GROUP)


def report_table(
    design: pd.DataFrame,
    predictions: pd.DataFrame,
    *,
    reference: str = "B3",
    persistence: str = "B1",
    by: Sequence[str] = (LEAD_BIN, INTENSITY),
) -> pd.DataFrame:
    """Score every model in every cell of ``by`` plus a pooled row per model."""
    y = design[TARGET].to_numpy(dtype=np.float64)
    keys = list(by)
    cells: list[tuple[str, ...]] = [("all",) * len(keys)]
    if keys:
        cells += [
            tuple(map(str, c)) for c in design[keys].drop_duplicates().itertuples(index=False)
        ]
    rows: list[dict[str, object]] = []
    for cell in cells:
        member = np.ones(len(design), dtype=bool)
        if cell[0] != "all":
            for key, value in zip(keys, cell, strict=True):
                member &= design[key].astype(str).to_numpy() == value
        if not member.any():
            continue
        mse_of: dict[str, float] = {}
        for name in predictions.columns:
            summary = score_summary(y[member], predictions[name].to_numpy()[member])
            mse_of[name] = summary["rmse"] ** 2
        for name in predictions.columns:
            summary = score_summary(y[member], predictions[name].to_numpy()[member])
            row: dict[str, object] = {"model": name}
            row.update(dict(zip(keys, cell, strict=True)))
            row.update(summary)
            row["skill_vs_persistence"] = (
                skill_score(mse_of[name], mse_of[persistence]) if persistence in mse_of else np.nan
            )
            row["skill_vs_reference"] = (
                skill_score(mse_of[name], mse_of[reference]) if reference in mse_of else np.nan
            )
            rows.append(row)
    return pd.DataFrame(rows)


def peak_errors(design: pd.DataFrame, predictions: pd.DataFrame, model: str) -> pd.DataFrame:
    """Per storm: predicted minus observed peak amplitude and peak time (minutes)."""
    y = design[TARGET].to_numpy(dtype=np.float64)
    prediction = predictions[model].to_numpy(dtype=np.float64)
    times = design["target_mid_utc"].to_numpy()
    groups = design[GROUP].to_numpy()
    rows: list[dict[str, object]] = []
    for group in np.unique(groups):
        member = np.where((groups == group) & np.isfinite(prediction) & np.isfinite(y))[0]
        if member.size == 0:
            continue
        observed_peak = member[int(np.argmax(y[member]))]
        predicted_peak = member[int(np.argmax(prediction[member]))]
        rows.append(
            {
                GROUP: int(group),
                "observed_peak": float(y[observed_peak]),
                "predicted_peak": float(prediction[predicted_peak]),
                "amplitude_error": float(prediction[predicted_peak] - y[observed_peak]),
                "timing_error_min": float(
                    (times[predicted_peak] - times[observed_peak]) / np.timedelta64(1, "m")
                ),
            }
        )
    return pd.DataFrame(rows).set_index(GROUP)


__all__ = ["peak_errors", "per_storm_losses", "report_table", "score_summary", "skill_score"]
