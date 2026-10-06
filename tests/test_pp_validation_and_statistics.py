"""polar_precursor: folds, buffer check, nested CV, scores, bootstrap, permutation, power."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from polar_precursor.config import CrossValidation, ExperimentConfig, PrimaryTest, RidgeSettings
from polar_precursor.design import GROUP, TARGET, ladder, polar_columns
from polar_precursor.metrics import peak_errors, per_storm_losses, report_table, score_summary
from polar_precursor.statistics import (
    cluster_bootstrap,
    detectable_difference_sd,
    paired_losses,
    permutation_test,
    permute_polar_block,
    power_table,
    required_storms,
)
from polar_precursor.synthetic import SyntheticConfig, synthetic_design
from polar_precursor.validation import check_group_buffer, cross_validate, grouped_folds

FAST = ExperimentConfig(
    cv=CrossValidation(outer_folds=5, inner_folds=3),
    ridge=RidgeSettings(alphas=(0.1, 10.0)),
    test=PrimaryTest(bootstrap_resamples=500, permutation_resamples=20),
)


def test_grouped_folds_round_robin_by_epoch():
    groups = np.array([3, 3, 1, 1, 2, 2, 5, 5])
    times = np.array([30, 31, 10, 11, 20, 21, 40, 41])
    fold = grouped_folds(groups, times, 2)
    # groups ordered by first time: 1, 2, 3, 5 -> folds 0, 1, 0, 1
    assert list(fold) == [0, 0, 0, 0, 1, 1, 1, 1]
    assert len({fold[groups == g][0] for g in (1, 3)}) == 1
    with pytest.raises(ValueError):
        grouped_folds(groups, times, 5)


def test_buffer_check_flags_close_groups():
    design = synthetic_design(
        SyntheticConfig(n_storms=3, samples_per_storm=4, storm_spacing_h=200.0), seed=0
    )
    assert check_group_buffer(design, buffer_h=57.0) == []
    close = synthetic_design(
        SyntheticConfig(n_storms=3, samples_per_storm=4, storm_spacing_h=20.0), seed=0
    )
    violations = check_group_buffer(close, buffer_h=57.0)
    assert len(violations) == 2 and violations[0].gap_h < 57.0


def test_cross_validation_predictions_are_out_of_fold_and_alpha_tuned():
    design = synthetic_design(SyntheticConfig(n_storms=10, samples_per_storm=12), seed=3)
    result = cross_validate(design, ladder(("B0", "B1", "B3", "M")), FAST)
    assert list(result.predictions.columns) == ["B0", "B1", "B3", "M"]
    assert (result.predictions["B0"] == 0.0).all()
    assert np.allclose(result.predictions["B1"], design["persistence"])
    assert np.isfinite(result.predictions[["B3", "M"]].to_numpy()).all()
    assert len(result.alphas["M"]) == 5 and set(result.alphas["M"]) <= {0.1, 10.0}
    assert len(np.unique(result.fold)) == 5
    # every group sits in exactly one fold
    folds_per_group = pd.Series(result.fold).groupby(design[GROUP].to_numpy()).nunique()
    assert (folds_per_group == 1).all()


def test_scores_and_per_storm_tables():
    design = synthetic_design(SyntheticConfig(n_storms=6, samples_per_storm=10), seed=5)
    result = cross_validate(design, ladder(("B1", "B3", "M")), FAST)
    summary = score_summary(design[TARGET].to_numpy(), result.predictions["B3"].to_numpy())
    assert summary["n"] == len(design) and summary["rmse"] > 0.0
    losses = per_storm_losses(design, result.predictions)
    assert list(losses.index) == list(range(6)) and losses["n_samples"].sum() == len(design)
    table = report_table(design, result.predictions, reference="B3", persistence="B1")
    pooled = table[(table["lead_bin"] == "all")].set_index("model")
    assert abs(pooled.loc["B3", "skill_vs_reference"]) < 1e-12
    assert abs(pooled.loc["B1", "skill_vs_persistence"]) < 1e-12
    peaks = peak_errors(design, result.predictions, "M")
    assert set(peaks.columns) == {
        "observed_peak",
        "predicted_peak",
        "amplitude_error",
        "timing_error_min",
    }
    assert (peaks["timing_error_min"] % 46.0 == 0.0).all()


def test_bootstrap_interval_contains_point_estimate_and_is_reproducible():
    per_storm = pd.DataFrame(
        {
            "B3": [1.0, 1.2, 0.9, 1.1, 1.0],
            "M": [0.8, 1.0, 0.9, 0.7, 0.9],
            "n_samples": [10, 20, 10, 10, 5],
        }
    )
    first = cluster_bootstrap(per_storm, reference="B3", candidate="M", n_resamples=2000, seed=1)
    second = cluster_bootstrap(per_storm, reference="B3", candidate="M", n_resamples=2000, seed=1)
    assert first == second
    assert first.ci_low <= first.relative_rmse_reduction <= first.ci_high
    assert first.relative_rmse_reduction == pytest.approx(1.0 - np.sqrt(4.3 / 5.2))
    assert paired_losses(per_storm, "B3", "M").tolist() == pytest.approx([0.2, 0.2, 0.0, 0.4, 0.1])
    weighted = cluster_bootstrap(
        per_storm, reference="B3", candidate="M", n_resamples=200, seed=1, weight="samples"
    )
    assert weighted.relative_rmse_reduction != first.relative_rmse_reduction
    assert "relative RMSE reduction" in first.line()


def test_permutation_keeps_marginals_and_breaks_link():
    design = synthetic_design(
        SyntheticConfig(n_storms=8, samples_per_storm=10, polar_gain=0.5), seed=7
    )
    rng = np.random.default_rng(0)
    permuted = permute_polar_block(design, strata=("intensity", "lead_bin"), rng=rng)
    columns = polar_columns(design)
    assert sorted(permuted[columns[0]].tolist()) == sorted(design[columns[0]].tolist())
    non_polar = [c for c in design.columns if c not in columns]
    pd.testing.assert_frame_equal(permuted[non_polar], design[non_polar])
    for key, rows in design.groupby(["intensity", "lead_bin"]).groups.items():
        assert sorted(permuted.loc[rows, columns[0]]) == sorted(design.loc[rows, columns[0]]), key


def test_permutation_test_runs_and_reports_p_value():
    design = synthetic_design(
        SyntheticConfig(n_storms=10, samples_per_storm=12, polar_gain=0.6), seed=11
    )
    cv = cross_validate(design, ladder(("B3", "M")), FAST)
    result = permutation_test(design, cv, FAST, n_resamples=20, seed=3)
    assert result.null.shape == (20,)
    assert 0.0 < result.p_value <= 1.0
    assert result.p_value == (1 + np.sum(result.null >= result.observed)) / 21
    assert "p =" in result.line()


def test_power_relations():
    assert detectable_difference_sd(30) == pytest.approx(0.511, abs=0.002)
    assert detectable_difference_sd(150) == pytest.approx(0.229, abs=0.002)
    assert required_storms(0.5) == 32
    table = power_table((30, 150, 200), sd_loss_difference=0.1)
    assert list(table["n_storms"]) == [30.0, 150.0, 200.0]
    assert table["detectable_loss_difference"].iloc[0] == pytest.approx(0.0511, abs=0.0002)


def test_fast_config_is_a_variation_of_defaults():
    assert replace(FAST, name="x").name == "x"
