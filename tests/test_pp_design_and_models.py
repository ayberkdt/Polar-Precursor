"""polar_precursor: configuration, ladder, design builder on the real CHAMP day, ridge."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from polar_precursor.config import CrossValidation, ExperimentConfig, PrimaryTest, load_config
from polar_precursor.design import LADDER, TARGET, Family, assign_storms, build_design, ladder
from polar_precursor.design.matrix import cluster_classes, lead_bin_labels
from polar_precursor.models import fit_ridge
from polar_precursor.synthetic import SyntheticConfig, synthetic_design
from space_environment.analysis.passes import build_samples, segment_track

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"
CHAMP_TRACK = FIXTURES / "champ_track_20031029_60s.csv"


def test_pilot_config_loads_and_matches_defaults():
    config = load_config(ROOT / "configs" / "pilot.toml")
    assert config.name == "pilot"
    assert config.ladder == ("B0", "B1", "B2", "D", "B3", "B3k", "B3t", "M")
    assert config.test.reference_model == "B3" and config.test.candidate_model == "M"
    assert config.cv.buffer_h == 57.0
    assert config.storms.satellites == ("CHAMP",)
    assert len(config.digest()) == 64
    assert config.digest() != ExperimentConfig().digest()  # pilot narrows the period


def test_config_rejects_inconsistent_values():
    with pytest.raises(ValueError):
        ExperimentConfig(ladder=("B3",))  # candidate M missing
    with pytest.raises(ValueError):
        ExperimentConfig(cv=CrossValidation(outer_folds=1))
    with pytest.raises(ValueError):
        ExperimentConfig(test=PrimaryTest(storm_weight="median"))


def test_ladder_resolves_families_to_columns():
    design = synthetic_design(SyntheticConfig(n_storms=3, samples_per_storm=5), seed=1)
    assert LADDER["B3"].columns(design) == [
        c for c in design.columns if c.startswith(("low_lag", "drv_d_", "geo_"))
    ]
    assert all(c.startswith("polar_") for c in LADDER["M"].columns(design) if "polar" in c)
    assert "mid_same" in LADDER["B3t"].columns(design)
    assert any(c.startswith("drv_oracle_") for c in LADDER["B3k"].columns(design))
    assert not any(c.startswith("drv_oracle_") for c in LADDER["B3"].columns(design))
    assert LADDER["B0"].columns(design) == []
    with pytest.raises(ValueError):
        ladder(("B9",))
    assert Family.DRIVERS in LADDER["D"].families and Family.LOW not in LADDER["D"].families


def test_lead_bin_labels_cover_edges():
    labels = lead_bin_labels(np.array([60.0, 104.9, 105.0, 270.0, 300.0]), (60.0, 105.0, 270.0))
    assert list(labels) == ["60-105", "60-105", "105-270", "105-270", "out"]


def _storm_table() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "disturbance_utc": [pd.Timestamp("2003-10-29T06:00:00Z")],
            "window_end_utc": [pd.Timestamp("2003-10-30T00:00:00Z")],
            "cluster": [7],
            "intensity": ["extreme"],
        }
    )


def test_assign_storms_inside_window_only():
    t0 = pd.Series(
        [
            pd.Timestamp("2003-10-29T05:00:00Z"),
            pd.Timestamp("2003-10-29T12:00:00Z"),
            pd.Timestamp("2003-10-30T01:00:00Z"),
        ]
    )
    out = assign_storms(t0, _storm_table())
    assert list(out["group"]) == [-1, 7, -1]
    assert list(out["intensity"]) == ["none", "extreme", "none"]


def test_cluster_class_is_the_most_intense_member():
    storms = pd.DataFrame(
        {
            "disturbance_utc": pd.to_datetime(
                ["2003-10-28T02:06:00Z", "2003-10-29T06:11:00Z", "2003-11-20T08:00:00Z"]
            ),
            "window_end_utc": pd.to_datetime(
                ["2003-10-29T06:11:00Z", "2003-10-30T16:19:00Z", "2003-11-21T20:00:00Z"]
            ),
            "cluster": [11, 11, 12],
            "intensity": ["moderate", "extreme", None],
        }
    )
    assert cluster_classes(storms) == {11: "extreme", 12: "none"}
    out = assign_storms(pd.Series([pd.Timestamp("2003-10-28T12:00:00Z")]), storms)
    assert list(out["intensity"]) == ["extreme"]


def test_build_design_on_real_champ_day_is_causal_and_complete():
    track = pd.read_csv(CHAMP_TRACK, index_col=0, parse_dates=True)
    track.index = (
        pd.DatetimeIndex(track.index).tz_localize("UTC") if track.index.tz is None else track.index
    )
    segments = segment_track(track, band_latitude="latitude_deg")
    samples = build_samples(segments)
    captured: list[pd.Timestamp] = []

    def drivers(t0: pd.Timestamp) -> dict[str, float]:
        captured.append(t0)
        return {"em": float(t0.hour)}

    def oracle(t: pd.Timestamp) -> dict[str, float]:
        return {"em": float(t.hour)}

    design = build_design(
        samples,
        segments,
        storms=_storm_table(),
        satellite="CHAMP",
        lead_bin_edges_min=(60.0, 105.0, 150.0, 195.0, 240.0, 270.0),
        drivers=drivers,
        oracle_drivers=oracle,
    )
    assert not design.empty
    assert (design["group"] == 7).all() and (design["intensity"] == "extreme").all()
    assert (design["t0_utc"] >= pd.Timestamp("2003-10-29T06:00:00Z")).all()
    assert all(t.second == 0 for t in captured)
    assert all(t <= s for t, s in zip(captured, design["t0_utc"], strict=False) if True)
    assert np.allclose(
        design["low_same_lag1"].to_numpy(), design["persistence"].to_numpy(), equal_nan=True
    )
    assert "low_other_lag2" in design.columns
    for column in (
        "low_lag1",
        "polar_north_lag1",
        "polar_south_lag1",
        "geo_lead_time_h",
        "drv_em",
        "drv_oracle_em",
        "persistence",
        TARGET,
    ):
        assert column in design.columns
    assert np.isfinite(design["low_lag1"]).all()
    assert set(design["lead_bin"]) <= {"60-105", "105-150", "150-195", "195-240", "240-270"}
    # the sample for every row ends at t0: no low-latitude input comes from after t0
    by_id = segments.set_index("segment_id")
    for _, sample in samples.iterrows():
        assert all(by_id.at[i, "end_utc"] <= sample["t0_utc"] for i in sample["input_low_segments"])


def test_ridge_recovers_linear_coefficients_and_handles_nan():
    rng = np.random.default_rng(0)
    n = 500
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n) * 3.0
    y = 1.0 + 2.0 * x1 - 0.5 * x2 + rng.normal(scale=0.01, size=n)
    frame = pd.DataFrame({"a": x1, "b": x2})
    model = fit_ridge(frame, ["a", "b"], y, alpha=1e-6)
    assert abs(model.intercept - y.mean()) < 1e-9
    beta = model.coefficient_table()
    assert abs(beta["a"] - 2.0 * x1.std()) < 0.01  # standardised coefficient
    assert abs(beta["b"] + 0.5 * x2.std()) < 0.01
    frame_with_gap = frame.copy()
    frame_with_gap.loc[0, "a"] = np.nan
    prediction = model.predict(frame_with_gap)
    assert np.isfinite(prediction).all()
    assert (
        abs(prediction[0] - (model.intercept + beta["b"] * (x2[0] - x2.mean()) / x2.std())) < 1e-9
    )
    with pytest.raises(ValueError):
        fit_ridge(frame, ["a"], y, alpha=-1.0)
