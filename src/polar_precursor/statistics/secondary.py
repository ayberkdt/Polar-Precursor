"""Secondary and exploratory comparisons (main plan "Çoklu test", "Ayrıştırmalar").

The primary test is one number (M vs B3, lead times pooled). Everything here
is secondary: the same cluster bootstrap applied per lead-time bin with Holm
correction, the other hypotheses (H4: B3 vs D) and the two controls (M vs B3t,
M vs B3k), and the per-class distribution of the paired loss difference that
the gate report asks for. One-sided bootstrap p-values are the fraction of
resamples in which the candidate does not beat the reference.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

from polar_precursor.design.ladder import GROUP, INTENSITY, LEAD_BIN
from polar_precursor.metrics.scores import per_storm_losses
from polar_precursor.statistics.bootstrap import BootstrapResult, cluster_bootstrap

PAIRS_SECONDARY: tuple[tuple[str, str, str], ...] = (
    ("B3", "M", "H1 primary: polar passes added"),
    ("D", "B3", "H4: own history added to drivers"),
    ("B3t", "M", "control: polar vs mid-latitude freshness (before the pass)"),
    ("B3t2", "M", "control: polar vs mid-latitude freshness (after the pass)"),
    ("B3k", "M", "control: polar vs oracle drivers"),
    ("B1", "B2", "ladder: autoregression over persistence"),
    ("B2", "B3", "ladder: drivers over own history"),
)


@dataclass(frozen=True, slots=True)
class PairResult:
    reference: str
    candidate: str
    label: str
    subset: str
    bootstrap: BootstrapResult

    def row(self) -> dict[str, object]:
        b = self.bootstrap
        return {
            "reference": self.reference,
            "candidate": self.candidate,
            "label": self.label,
            "subset": self.subset,
            "n_storms": b.n_storms,
            "relative_rmse_reduction": b.relative_rmse_reduction,
            "ci_low": b.ci_low,
            "ci_high": b.ci_high,
            "mean_loss_difference": b.mean_loss_difference,
            "fraction_storms_improved": b.fraction_storms_improved,
            "p_one_sided": b.p_one_sided,
        }


def compare_pair(
    per_storm: pd.DataFrame,
    reference: str,
    candidate: str,
    *,
    label: str = "",
    subset: str = "all",
    n_resamples: int,
    seed: int,
    confidence_level: float = 0.95,
    weight: str = "equal",
) -> PairResult:
    bootstrap = cluster_bootstrap(
        per_storm,
        reference=reference,
        candidate=candidate,
        n_resamples=n_resamples,
        seed=seed,
        confidence_level=confidence_level,
        weight=weight,
    )
    return PairResult(reference, candidate, label, subset, bootstrap)


def comparison_table(
    per_storm: pd.DataFrame,
    *,
    pairs: Sequence[tuple[str, str, str]] = PAIRS_SECONDARY,
    n_resamples: int,
    seed: int,
    confidence_level: float = 0.95,
    weight: str = "equal",
) -> pd.DataFrame:
    """One row per (reference, candidate) pair present in ``per_storm``."""
    rows = []
    for reference, candidate, label in pairs:
        if reference not in per_storm.columns or candidate not in per_storm.columns:
            continue
        rows.append(
            compare_pair(
                per_storm,
                reference,
                candidate,
                label=label,
                n_resamples=n_resamples,
                seed=seed,
                confidence_level=confidence_level,
                weight=weight,
            ).row()
        )
    return pd.DataFrame(rows)


def holm_adjust(p_values: Sequence[float]) -> np.ndarray:
    """Holm step-down adjusted p-values (monotone, capped at 1)."""
    p = np.asarray(p_values, dtype=np.float64)
    m = len(p)
    if m == 0:
        return p
    order = np.argsort(p)
    adjusted = np.empty(m)
    running = 0.0
    for rank, index in enumerate(order):
        value = min(1.0, (m - rank) * p[index])
        running = max(running, value)
        adjusted[index] = running
    return adjusted


def per_storm_losses_by(
    design: pd.DataFrame,
    predictions: pd.DataFrame,
    models: Sequence[str],
    *,
    by: str = LEAD_BIN,
) -> dict[str, pd.DataFrame]:
    """Per-storm loss tables restricted to each level of ``by`` (e.g. lead-time bin)."""
    tables: dict[str, pd.DataFrame] = {}
    for level in sorted(design[by].astype(str).unique()):
        member = (design[by].astype(str) == level).to_numpy()
        subset = design[member].reset_index(drop=True)
        subset_predictions = predictions[member].reset_index(drop=True)
        tables[level] = per_storm_losses(subset, subset_predictions, models)
    return tables


def lead_bin_tests(
    design: pd.DataFrame,
    predictions: pd.DataFrame,
    *,
    reference: str,
    candidate: str,
    n_resamples: int,
    seed: int,
    confidence_level: float = 0.95,
    weight: str = "equal",
    alpha: float = 0.05,
) -> pd.DataFrame:
    """Primary comparison per lead-time bin with Holm-adjusted one-sided p-values."""
    rows = []
    for level, table in per_storm_losses_by(
        design, predictions, [reference, candidate], by=LEAD_BIN
    ).items():
        ok = np.isfinite(table[reference]) & np.isfinite(table[candidate])
        if ok.sum() < 2:
            continue
        result = compare_pair(
            table[ok],
            reference,
            candidate,
            subset=level,
            n_resamples=n_resamples,
            seed=seed,
            confidence_level=confidence_level,
            weight=weight,
        )
        rows.append(result.row())
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out.rename(columns={"subset": LEAD_BIN, "p_one_sided": "p_raw"})
    out["p_holm"] = holm_adjust(out["p_raw"].to_numpy())
    out["significant_holm"] = out["p_holm"] <= alpha
    return out.drop(columns=["label"])


def h2_gain_peaks_mid_lead(
    lead_table: pd.DataFrame, *, mid_bins: Sequence[str] = ("105-150", "150-195")
) -> bool:
    """H2: the gain is highest in the 105-195 minute bins (descriptive, not a test)."""
    if lead_table.empty or "relative_rmse_reduction" not in lead_table.columns:
        return False
    values = lead_table["relative_rmse_reduction"].to_numpy(dtype=np.float64)
    best = lead_table[LEAD_BIN].to_numpy()[int(np.argmax(values))]
    return str(best) in set(mid_bins)


def loss_difference_by_class(
    per_storm: pd.DataFrame, reference: str, candidate: str
) -> pd.DataFrame:
    """Distribution of d_s = MSE_ref − MSE_cand per storm class (gate report item)."""
    d = (per_storm[reference] - per_storm[candidate]).rename("d")
    frame = pd.DataFrame({"d": d, INTENSITY: per_storm[INTENSITY]})
    frame = frame[np.isfinite(frame["d"])]
    grouped = frame.groupby(INTENSITY)["d"]
    out = pd.DataFrame(
        {
            "n_storms": grouped.size(),
            "mean_d": grouped.mean(),
            "sd_d": grouped.std(ddof=1),
            "median_d": grouped.median(),
            "fraction_improved": grouped.apply(lambda s: float(np.mean(s > 0.0))),
        }
    )
    out.index.name = INTENSITY
    return out.reset_index()


__all__ = [
    "GROUP",
    "PAIRS_SECONDARY",
    "PairResult",
    "compare_pair",
    "comparison_table",
    "h2_gain_peaks_mid_lead",
    "holm_adjust",
    "lead_bin_tests",
    "loss_difference_by_class",
    "per_storm_losses_by",
]
