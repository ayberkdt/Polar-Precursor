"""Shock detector and the forecast-time feature builder on real OMNI data."""

import numpy as np
import pandas as pd
import pytest

from space_environment.analysis.features import DriverFeatureBuilder, DriverFeatureConfig
from space_environment.io.omni import read_omni_hro
from space_environment.physics.shock import detect_shocks, hours_since_last_shock


@pytest.fixture(scope="module")
def omni(omni_path):
    return read_omni_hro(omni_path)


def test_shock_of_28_october_2003_is_found_near_the_richardson_cane_time(omni):
    shocks = detect_shocks(omni)
    assert len(shocks) == 1
    shock = shocks[0]
    # Richardson-Cane disturbance 2003/10/28 0206; OMNI steps at 02:03-02:04 UT.
    assert abs(shock.time - pd.Timestamp("2003-10-28 02:04", tz="UTC")) <= pd.Timedelta(5, "min")
    assert shock.confirmed_at == shock.time + pd.Timedelta(10, "min")
    assert shock.speed_jump_km_s > 60.0
    assert shock.b_ratio > 1.4 and shock.density_ratio > 2.0


def test_hours_since_shock_only_counts_confirmed_shocks(omni):
    shocks = detect_shocks(omni)
    shock = shocks[0]
    assert np.isnan(hours_since_last_shock(shocks, shock.time + pd.Timedelta(5, "min")))
    at = shock.time + pd.Timedelta(2, "h")
    assert hours_since_last_shock(shocks, at) == pytest.approx(2.0)


def test_detector_requires_regular_minutes(omni):
    with pytest.raises(ValueError, match="1 minute"):
        detect_shocks(omni.iloc[::2])


def test_features_at_a_known_epoch(omni):
    builder = DriverFeatureBuilder(omni, shocks=detect_shocks(omni))
    t0 = pd.Timestamp("2003-10-28 12:00", tz="UTC")
    features = builder.features_at(t0)
    # OMNI record 2003-10-28 12:00: By 6.90, Bz 7.16 nT GSM, speed 753.6 km/s.
    assert features["bz_gsm_nt"] == pytest.approx(7.16)
    assert features["flow_speed_km_s"] == pytest.approx(753.6)
    b_t = np.hypot(6.90, 7.16)
    theta = np.arctan2(6.90, 7.16)
    assert features["em_mv_m"] == pytest.approx(1e-3 * 753.6 * b_t * np.sin(theta / 2) ** 2)
    assert features["em_valid_6h"] == pytest.approx(1.0)
    assert features["hours_since_shock"] == pytest.approx(
        (t0 - detect_shocks(omni)[0].time) / pd.Timedelta(1, "h")
    )
    assert set(features) == set(builder.feature_names)


def test_features_do_not_depend_on_anything_after_t0(omni):
    t0 = pd.Timestamp("2003-10-28 12:00", tz="UTC")
    shocks = detect_shocks(omni)
    clean = DriverFeatureBuilder(omni, shocks=shocks).features_at(t0)
    corrupted = omni.copy()
    corrupted.loc[corrupted.index > t0, list(corrupted.columns)] = 1.0e5
    dirty = DriverFeatureBuilder(corrupted, shocks=shocks).features_at(t0)
    for name, value in clean.items():
        if np.isnan(value):
            assert np.isnan(dirty[name]), name
        else:
            assert dirty[name] == value, name


def test_feature_table_marks_the_omni_gap(omni):
    builder = DriverFeatureBuilder(omni, config=DriverFeatureConfig(memory_taus_h=(3.0,)))
    epochs = pd.date_range("2003-10-29 05:00", "2003-10-29 12:00", freq="1h", tz="UTC")
    table = builder.table(epochs)
    assert list(table.columns) == builder.feature_names
    assert table.index.name == "t0_utc"
    # Driver information decays through the gap that starts 05:50 UT.
    assert table["em_valid_6h"].iloc[0] > 0.9
    assert table["em_valid_6h"].iloc[-1] == 0.0
    assert np.isnan(table["em_mv_m"].iloc[-1])
    assert np.isnan(table["em_mem_3h"].iloc[-1])  # less than half the weight present
    assert table["sym_h_nt"].notna().all()  # indices continue through the gap


def test_t0_must_be_a_sample_time(omni):
    builder = DriverFeatureBuilder(omni)
    with pytest.raises(ValueError, match="not a sample time"):
        builder.features_at(pd.Timestamp("2003-10-28 12:00:30", tz="UTC"))
