"""Quiet-geomagnetic wrapper, index features and geometry features on real excerpts."""

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from space_environment.analysis.index_features import (
    GEOMETRY_FEATURE_NAMES,
    IndexFeatureBuilder,
    geometry_features,
)
from space_environment.io.gfz import read_gfz_hpo
from space_environment.io.kyoto import read_kyoto_dst_hapi
from space_environment.physics.space_weather import GfzIndexProvider, QuietGeomagneticProvider

FIXTURES = Path(__file__).parent / "fixtures"
DST_CSV = FIXTURES / "hour_dst_final_20031001_20031201.csv"
DST_INFO = FIXTURES / "hour_dst_final_info.json"

T0 = pd.Timestamp("2003-10-29 07:04", tz="UTC")


@pytest.fixture(scope="module")
def measured(gfz_daily_path):
    return GfzIndexProvider.from_file(gfz_daily_path)


def test_quiet_wrapper_matches_the_quiet_flag(gfz_daily_path, measured):
    flagged = GfzIndexProvider.from_file(gfz_daily_path, geomagnetic="quiet").get(T0)
    wrapped = QuietGeomagneticProvider(measured).get(T0)
    assert wrapped == flagged
    assert wrapped.f107 == measured.get(T0).f107
    assert wrapped.ap_history == (4.0,) * 6 and wrapped.kp is None
    assert "Ap prescribed quiet = 4" in wrapped.source
    with pytest.raises(ValueError, match="Ap range"):
        QuietGeomagneticProvider(measured, quiet_ap=500.0)


def test_index_features_at_the_halloween_epoch(measured, gfz_hpo_path):
    hpo = read_gfz_hpo(gfz_hpo_path)
    dst = read_kyoto_dst_hapi(DST_CSV, DST_INFO)
    builder = IndexFeatureBuilder(measured, hpo=hpo, dst=dst)
    features = builder.features_at(T0)
    state = measured.get(T0)
    assert features["f107_prev_day_sfu"] == state.f107
    assert features["f107a_centred_sfu"] == state.f107a
    assert features["ap_daily"] == 204.0
    assert features["kp_current_3h"] == 9.0  # 06-09 UT slot of 2003-10-29
    # The latest complete half hour at 07:04 is 06:30-07:00.
    by_start = {record.start: record for record in hpo}
    assert (
        features["ap30_latest"] == by_start[datetime(2003, 10, 29, 6, 30, tzinfo=timezone.utc)].ap30
    )
    assert (
        features["dst_latest_hour_nt"]
        == dst.at[pd.Timestamp("2003-10-29 06:00", tz="UTC"), "dst_nt"]
    )
    assert features["ap30_lag_0_3h"] > features["ap30_lag_3_6h"]  # storm onset in the last 3 h
    assert set(features) == set(builder.feature_names)


def test_half_hour_index_is_not_used_before_its_interval_ends(measured, gfz_hpo_path):
    hpo = read_gfz_hpo(gfz_hpo_path)
    builder = IndexFeatureBuilder(measured, hpo=hpo)
    by_start = {record.start: record for record in hpo}
    just_before = builder.features_at(pd.Timestamp("2003-10-29 06:59", tz="UTC"))
    at_end = builder.features_at(pd.Timestamp("2003-10-29 07:00", tz="UTC"))
    assert (
        just_before["ap30_latest"]
        == by_start[datetime(2003, 10, 29, 6, 0, tzinfo=timezone.utc)].ap30
    )
    assert (
        at_end["ap30_latest"] == by_start[datetime(2003, 10, 29, 6, 30, tzinfo=timezone.utc)].ap30
    )


def test_missing_optional_sources_give_nan_not_errors(measured):
    builder = IndexFeatureBuilder(measured)
    features = builder.features_at(T0)
    assert np.isnan(features["ap30_latest"]) and np.isnan(features["dst_latest_hour_nt"])
    table = builder.table([T0, T0 + pd.Timedelta(1, "h")])
    assert list(table.columns) == builder.feature_names and len(table) == 2


def test_geometry_features_are_periodic_encodings():
    features = geometry_features(
        datetime(2003, 10, 29, 7, 4, tzinfo=timezone.utc),
        lead_time_h=2.0,
        target_local_solar_time_h=6.0,
        altitude_m=400_000.0,
    )
    assert set(features) == set(GEOMETRY_FEATURE_NAMES)
    assert features["target_lst_sin"] == pytest.approx(1.0)  # 06 LT is a quarter turn
    assert features["target_lst_cos"] == pytest.approx(0.0, abs=1e-12)
    assert features["altitude_km"] == 400.0 and features["lead_time_h"] == 2.0
    assert features["doy_sin"] ** 2 + features["doy_cos"] ** 2 == pytest.approx(1.0)
    with pytest.raises(ValueError, match="24"):
        geometry_features(
            datetime(2003, 10, 29, tzinfo=timezone.utc),
            lead_time_h=1.0,
            target_local_solar_time_h=24.0,
            altitude_m=4e5,
        )
