"""Secondary comparisons, Holm correction, per-lead-bin tests and the gate report."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from polar_precursor.config import CrossValidation, ExperimentConfig, PrimaryTest, RidgeSettings
from polar_precursor.experiment.pipeline import run_experiment
from polar_precursor.experiment.report import gate_report
from polar_precursor.statistics import (
    comparison_table,
    h2_gain_peaks_mid_lead,
    holm_adjust,
    lead_bin_tests,
    loss_difference_by_class,
)
from polar_precursor.synthetic import SyntheticConfig, synthetic_design

FAST = ExperimentConfig(
    name="fast",
    cv=CrossValidation(outer_folds=5, inner_folds=3),
    ridge=RidgeSettings(alphas=(0.1, 10.0)),
    test=PrimaryTest(bootstrap_resamples=400, permutation_resamples=10),
)


def test_holm_adjustment_is_monotone_and_matches_hand_calculation():
    adjusted = holm_adjust([0.01, 0.04, 0.03, 0.2])
    # sorted: 0.01*4=0.04, 0.03*3=0.09, 0.04*2=0.09 (monotone), 0.2*1=0.2
    assert adjusted.tolist() == pytest.approx([0.04, 0.09, 0.09, 0.2])
    assert holm_adjust([]).size == 0
    assert holm_adjust([0.5, 0.9]).max() <= 1.0


def test_comparison_and_lead_bin_tables_on_synthetic_signal():
    design = synthetic_design(
        SyntheticConfig(n_storms=10, samples_per_storm=14, polar_gain=0.6), seed=21
    )
    result = run_experiment(design, FAST, with_permutation=False)
    table = comparison_table(result.per_storm, n_resamples=300, seed=1)
    assert set(table["candidate"]) >= {"M", "B3", "B2"}
    primary = table[(table["reference"] == "B3") & (table["candidate"] == "M")].iloc[0]
    assert primary["relative_rmse_reduction"] > 0.0 and 0.0 < primary["p_one_sided"] <= 1.0
    assert result.bootstrap.p_one_sided <= 0.5  # strong synthetic signal

    lead = lead_bin_tests(
        design, result.cv.predictions, reference="B3", candidate="M", n_resamples=300, seed=1
    )
    assert set(lead["lead_bin"]) == set(design["lead_bin"].unique())
    assert (lead["p_holm"] >= lead["p_raw"]).all()
    assert lead["n_storms"].max() <= 10
    assert isinstance(h2_gain_peaks_mid_lead(lead), bool)

    by_class = loss_difference_by_class(result.per_storm, "B3", "M")
    assert by_class["n_storms"].sum() == 10
    assert set(by_class.columns) >= {"intensity", "mean_d", "sd_d", "fraction_improved"}


def test_gate_report_contains_every_section():
    design = synthetic_design(
        SyntheticConfig(n_storms=8, samples_per_storm=10, polar_gain=0.4), seed=5
    )
    result = run_experiment(design, FAST, with_permutation=True, permutation_resamples=5)
    text = gate_report(result, design, title="Synthetic gate", secondary_resamples=200)
    for heading in (
        "# Synthetic gate",
        "## Primary result",
        "## Ladder, lead times pooled",
        "## Secondary comparisons",
        "## Primary comparison per lead-time bin",
        "## d_s by storm class",
        "## Peak errors of M",
        "## Power",
        "## Buffer check",
    ):
        assert heading in text
    assert "no violations" in text and "p =" in text
    assert "| B3 | M |" in text


def test_lead_bin_tests_skip_bins_without_two_storms():
    design = synthetic_design(SyntheticConfig(n_storms=4, samples_per_storm=6), seed=2)
    predictions = pd.DataFrame({"B3": np.zeros(len(design)), "M": np.zeros(len(design)) + 0.1})
    design = design.copy()
    design.loc[design.index[:1], "lead_bin"] = "lonely"
    lead = lead_bin_tests(
        design, predictions, reference="B3", candidate="M", n_resamples=50, seed=0
    )
    assert "lonely" not in set(lead["lead_bin"])
