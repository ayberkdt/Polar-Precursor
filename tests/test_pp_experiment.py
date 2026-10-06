"""polar_precursor: end-to-end pipeline, small skeleton test, manifest."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from polar_precursor.config import CrossValidation, ExperimentConfig, PrimaryTest, RidgeSettings
from polar_precursor.experiment import build_manifest, run_experiment, write_manifest
from polar_precursor.experiment.skeleton import repeat_skeleton, skeleton_passes
from polar_precursor.synthetic import SyntheticConfig, synthetic_design

ROOT = Path(__file__).resolve().parents[1]
FAST = ExperimentConfig(
    name="fast",
    cv=CrossValidation(outer_folds=5, inner_folds=3),
    ridge=RidgeSettings(alphas=(0.1, 10.0)),
    test=PrimaryTest(bootstrap_resamples=500, permutation_resamples=10),
)


def test_run_experiment_refuses_buffer_violation_and_returns_all_tables():
    close = synthetic_design(
        SyntheticConfig(n_storms=8, samples_per_storm=8, storm_spacing_h=10.0), seed=1
    )
    with pytest.raises(ValueError, match="closer than"):
        run_experiment(close, FAST, with_permutation=False)
    design = synthetic_design(
        SyntheticConfig(n_storms=8, samples_per_storm=8, polar_gain=0.5), seed=1
    )
    result = run_experiment(design, FAST, with_permutation=True)
    assert result.buffer_violations == ()
    assert list(result.cv.predictions.columns) == list(FAST.ladder)
    assert len(result.per_storm) == 8
    assert {"model", "lead_bin", "intensity", "rmse", "skill_vs_reference"} <= set(
        result.scores.columns
    )
    assert result.permutation is not None and result.permutation.null.shape == (10,)
    assert "M vs B3" in result.primary_line() and "p =" in result.primary_line()


def test_oracle_and_polar_steps_use_their_columns():
    design = synthetic_design(
        SyntheticConfig(n_storms=8, samples_per_storm=10, polar_gain=0.8), seed=2
    )
    result = run_experiment(design, FAST, with_permutation=False)
    pooled = result.scores[result.scores["lead_bin"] == "all"].set_index("model")
    # with a strong, lagged polar contribution M must beat B3 clearly on synthetic data
    assert pooled.loc["M", "rmse"] < pooled.loc["B3", "rmse"]
    assert result.bootstrap.relative_rmse_reduction > 0.0


def test_small_skeleton_passes():
    config = replace(FAST, test=PrimaryTest(bootstrap_resamples=300))
    base = SyntheticConfig(n_storms=12, samples_per_storm=12)
    null = repeat_skeleton(
        config, replace(base, polar_gain=0.0), n_repeats=12, seed=100, bootstrap_resamples=300
    )
    signal = repeat_skeleton(
        config, replace(base, polar_gain=0.8), n_repeats=12, seed=100, bootstrap_resamples=300
    )
    assert null.point_estimates.shape == (12,)
    # loose bounds for a 12-storm, 12-repeat smoke test; the 30-storm, 200-repeat run is the
    # evidence (plans/kanit/iskelet_testi_cikti_2026-10-06.txt)
    assert null.fraction_positive_significant <= 0.25
    assert (signal.point_estimates > 0.0).all()
    assert signal.fraction_positive_significant > null.fraction_positive_significant
    verdict, report = skeleton_passes(null, signal, max_false_positive=0.25, min_recovery=0.5)
    assert verdict, report
    assert "PASS" in report


def test_manifest_records_config_and_hashes(tmp_path: Path):
    data_file = tmp_path / "x.bin"
    data_file.write_bytes(b"abc")
    manifest = build_manifest(FAST, root=ROOT, data_files=[data_file], extra={"note": "test"})
    assert manifest["config_digest"] == FAST.digest()
    assert manifest["data_files_sha256"][str(data_file)].startswith("ba7816bf")
    assert manifest["note"] == "test" and manifest["environment"]["numpy"] == np.__version__
    out = tmp_path / "r" / "manifest.json"
    write_manifest(out, manifest)
    assert json.loads(out.read_text(encoding="utf-8"))["config_name"] == "fast"
