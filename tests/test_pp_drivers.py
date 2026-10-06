"""CombinedDrivers: one callable for build_design from real OMNI and GFZ excerpts."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from polar_precursor.design.drivers import AVAILABILITY_FLAG, CombinedDrivers
from space_environment.analysis.features import DriverFeatureBuilder
from space_environment.analysis.index_features import IndexFeatureBuilder
from space_environment.io.omni import read_omni_hro
from space_environment.physics.space_weather import GfzIndexProvider


def test_combined_drivers_merge_and_flag_missing_solar_wind(omni_path: Path, gfz_daily_path: Path):
    omni = read_omni_hro(omni_path, cadence="1min")
    solar_wind = DriverFeatureBuilder(omni)
    indices = IndexFeatureBuilder(
        GfzIndexProvider.from_file(gfz_daily_path, geomagnetic="measured")
    )
    drivers = CombinedDrivers(solar_wind=solar_wind, indices=indices)
    assert AVAILABILITY_FLAG in drivers.names
    assert len(set(drivers.names)) == len(drivers.names)

    inside = pd.Timestamp("2003-10-28T12:00:00Z")  # before the Halloween OMNI gap (plan 02)
    features = drivers(inside)
    assert set(features) == set(drivers.names)
    assert features[AVAILABILITY_FLAG] == 1.0
    assert np.isfinite(features["f107_prev_day_sfu"])
    assert np.isfinite(features["em_mv_m"])
    assert features["em_mv_m"] == solar_wind.features_at(inside)["em_mv_m"]
    gap = pd.Timestamp("2003-10-29T12:00:00Z")  # inside the frame, solar wind missing
    assert drivers(gap)[AVAILABILITY_FLAG] == 1.0 and np.isnan(drivers(gap)["em_mv_m"])

    outside = pd.Timestamp("2003-11-15T12:00:00Z")  # OMNI excerpt ends 30 Oct; GFZ reaches Dec
    features = drivers(outside)
    assert features[AVAILABILITY_FLAG] == 0.0
    assert all(np.isnan(features[name]) for name in solar_wind.feature_names)
    assert np.isfinite(features["ap_daily"])

    with pytest.raises(ValueError):
        CombinedDrivers()
