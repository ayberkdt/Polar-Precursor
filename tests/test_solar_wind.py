"""OMNI reader, coupling functions and memory features."""

import numpy as np
import pandas as pd
import pytest

from space_environment.io.omni import coverage, hro_column_names, read_omni_hro
from space_environment.physics.coupling import (
    clock_angle_rad,
    merging_electric_field_mv_m,
    newell_coupling,
    saturated_merging_field_mv_m,
    transverse_field_nt,
)
from space_environment.physics.memory import exponential_memory, lagged_window_means


def test_hro_record_has_46_fields():
    assert len(hro_column_names("1min")) == 46
    assert len(hro_column_names("5min")) == 49


def test_omni_values_of_a_known_record(omni_path):
    frame = read_omni_hro(omni_path)
    assert len(frame) == 3 * 1440
    assert frame.index[0] == pd.Timestamp("2003-10-28 00:00", tz="UTC")
    assert frame.index[-1] == pd.Timestamp("2003-10-30 23:59", tz="UTC")
    # Values read off the record for 2003 day 301 12:00 in the fixture.
    row = frame.loc[pd.Timestamp("2003-10-28 12:00", tz="UTC")]
    assert row["b_magnitude_nt"] == 12.10
    assert row["by_gsm_nt"] == 6.90
    assert row["bz_gsm_nt"] == 7.16
    assert row["flow_speed_km_s"] == 753.6
    assert row["vx_gse_km_s"] == -751.8
    # SYM-H at 06:00 UT on 29 October; the Kyoto web service gave the same value.
    assert frame.loc[pd.Timestamp("2003-10-29 06:00", tz="UTC"), "sym_h_nt"] == -34.0
    assert "sha256=" in frame.attrs["source"]


def test_omni_has_no_solar_wind_during_the_halloween_main_phase(omni_path):
    """The gap this project has to plan around: indices present, drivers absent."""
    frame = read_omni_hro(omni_path)
    storm = frame.loc["2003-10-29 05:50":"2003-10-29 18:42"]
    assert storm["bz_gsm_nt"].isna().all()
    assert storm["flow_speed_km_s"].isna().all()
    assert storm["sym_h_nt"].notna().all()
    assert frame.loc["2003-10-30", "bz_gsm_nt"].isna().all()
    daily = frame["bz_gsm_nt"].notna().groupby(frame.index.day).mean()
    assert daily[28] == 1.0
    assert daily[29] == pytest.approx(0.455, abs=0.001)
    assert daily[30] == 0.0
    assert coverage(frame, ("sym_h_nt",))["sym_h_nt"] == 1.0


def test_omni_rejects_wrong_cadence(omni_path):
    with pytest.raises(ValueError, match="46"):
        read_omni_hro(omni_path, cadence="5min")


def test_clock_angle_and_transverse_field():
    assert clock_angle_rad(0.0, 5.0) == pytest.approx(0.0)
    assert abs(clock_angle_rad(0.0, -5.0)) == pytest.approx(np.pi)
    assert clock_angle_rad(5.0, 0.0) == pytest.approx(np.pi / 2)
    assert transverse_field_nt(3.0, -4.0) == pytest.approx(5.0)


def test_merging_field_limits_and_units():
    # Purely southward: sin^2(theta/2) = 1, Em = v * |Bz| * 1e-3 mV/m.
    assert merging_electric_field_mv_m(500.0, 0.0, -10.0) == pytest.approx(5.0)
    # Purely northward: no merging.
    assert merging_electric_field_mv_m(500.0, 0.0, 10.0) == pytest.approx(0.0)
    # Purely dawn-dusk: sin^2(45 deg) = 1/2.
    assert merging_electric_field_mv_m(400.0, 10.0, 0.0) == pytest.approx(2.0)
    # Southward limit equals OMNI's own electric field -V*Bz*1e-3.
    assert merging_electric_field_mv_m(753.6, 0.0, -7.16) == pytest.approx(753.6 * 7.16e-3)
    assert merging_electric_field_mv_m(500.0, 0.0, 0.0) == pytest.approx(0.0)


def test_merging_field_matches_angle_form_and_propagates_nan():
    rng = np.random.default_rng(7)
    v = rng.uniform(300, 900, 200)
    by = rng.normal(0, 8, 200)
    bz = rng.normal(0, 8, 200)
    theta = np.arctan2(by, bz)
    expected = 1e-3 * v * np.hypot(by, bz) * np.sin(theta / 2) ** 2
    # The implementation uses sin^2(theta/2) = (1 - Bz/B_T)/2, which cancels for
    # nearly northward IMF: relative error ~ eps / sin^2(theta/2). The smallest
    # sin^2 in this sample is 1.6e-5, giving ~1.4e-11 (5.7e-12 was observed);
    # 1e-9 leaves margin, and the affected values are themselves negligible
    # (absolute error below 1e-15 mV/m).
    np.testing.assert_allclose(merging_electric_field_mv_m(v, by, bz), expected, rtol=1e-9)
    expected_newell = (
        v ** (4 / 3) * np.hypot(by, bz) ** (2 / 3) * np.abs(np.sin(theta / 2)) ** (8 / 3)
    )
    np.testing.assert_allclose(newell_coupling(v, by, bz), expected_newell, rtol=1e-9)
    assert np.isnan(merging_electric_field_mv_m(500.0, np.nan, -5.0))
    assert np.isnan(newell_coupling(np.nan, 1.0, -5.0))


def test_saturated_field_limits():
    assert saturated_merging_field_mv_m(0.5) == pytest.approx(0.5, rel=3e-3)
    assert saturated_merging_field_mv_m(1e6) == pytest.approx(8.0, rel=1e-6)
    assert saturated_merging_field_mv_m(8.0) == pytest.approx(8.0 / np.sqrt(2.0))


def test_exponential_memory_is_causal_and_converges():
    step, tau = 60.0, 3 * 3600.0
    constant = np.full(3000, 2.5)
    out = exponential_memory(constant, step_s=step, tau_s=tau, min_weight_fraction=0.0)
    np.testing.assert_allclose(out, 2.5)

    # Step response of a first-order filter: 1 - exp(-t/tau), with t counted
    # from one step before the first unit sample.
    signal = np.concatenate([np.zeros(600), np.ones(1200)])
    out = exponential_memory(signal, step_s=step, tau_s=tau, min_weight_fraction=0.0)
    elapsed = (np.arange(1200) + 1) * step
    decay = np.exp(-step / tau)
    weight = (1 - decay ** (np.arange(1200) + 601)) / (1 - decay)
    expected = (1 - np.exp(-elapsed / tau)) / (1 - decay) / weight
    np.testing.assert_allclose(out[600:], expected, rtol=1e-10)

    # Causality: changing the future must not change the past.
    changed = signal.copy()
    changed[900:] = 50.0
    again = exponential_memory(changed, step_s=step, tau_s=tau, min_weight_fraction=0.0)
    np.testing.assert_array_equal(again[:900], out[:900])


def test_exponential_memory_withholds_output_without_enough_data():
    step, tau = 60.0, 3600.0
    series = np.ones(600)
    out = exponential_memory(series, step_s=step, tau_s=tau, min_weight_fraction=0.5)
    # Half of the full weight is reached after tau*ln(2) = 41.6 min.
    first = int(np.argmax(~np.isnan(out)))
    assert first in (41, 42)
    series[100:400] = np.nan
    gapped = exponential_memory(series, step_s=step, tau_s=tau, min_weight_fraction=0.5)
    assert np.isnan(gapped[399]) and not np.isnan(gapped[99])
    assert gapped[599] == pytest.approx(1.0)


def test_lagged_window_means_never_read_the_future():
    index = pd.date_range("2003-10-28 00:00", periods=24 * 60, freq="1min", tz="UTC")
    series = pd.Series(np.arange(len(index), dtype=float), index=index)
    at = pd.Timestamp("2003-10-28 12:00", tz="UTC")
    means = lagged_window_means(series, at)
    # Window (11:00, 12:00] holds minutes 661..720 -> mean 690.5.
    assert means[0] == pytest.approx(690.5)
    # Window (07:30, 09:00] holds minutes 451..540 -> mean 495.5.
    assert means[3] == pytest.approx(495.5)
    future = series.copy()
    future.loc[future.index > at] = -1e9
    np.testing.assert_array_equal(lagged_window_means(future, at), means)
    holed = series.copy()
    holed.loc["2003-10-28 11:01":"2003-10-28 11:45"] = np.nan
    assert np.isnan(lagged_window_means(holed, at)[0])
