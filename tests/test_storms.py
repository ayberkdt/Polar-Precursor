"""Storm intensity classes and the automatic onset rule."""

import numpy as np
import pandas as pd
import pytest

from space_environment.io.omni import read_omni_hro
from space_environment.physics.storm_intensity import StormIntensity, classify_by_min_symh
from space_environment.physics.storm_onset import find_main_phase_onset, find_southward_turning


@pytest.mark.parametrize(
    ("min_symh", "expected"),
    [
        (-10.0, StormIntensity.WEAK),
        (-50.0, StormIntensity.WEAK),
        (-50.1, StormIntensity.MODERATE),
        (-100.0, StormIntensity.MODERATE),
        (-100.1, StormIntensity.STRONG),
        (-150.0, StormIntensity.STRONG),
        (-250.0, StormIntensity.SEVERE),
        (-250.1, StormIntensity.EXTREME),
        # Minimum SYM-H of the seven extreme storms in Zesta and Oliveira (2019), Table 2.
        (-320.0, StormIntensity.EXTREME),
        (-282.0, StormIntensity.EXTREME),
        (-490.0, StormIntensity.EXTREME),
    ],
)
def test_intensity_boundaries(min_symh, expected):
    assert classify_by_min_symh(min_symh) is expected


def _bz(values, start="2005-01-01 00:00"):
    index = pd.date_range(start, periods=len(values), freq="1min", tz="UTC")
    return pd.Series(np.asarray(values, dtype=float), index=index)


def test_onset_found_at_first_sustained_turning():
    values = np.full(600, 4.0)
    values[100:105] = -6.0  # a five-minute dip: not sustained
    values[200:] = -8.0  # the real turning
    series = _bz(values)
    result = find_southward_turning(series, series.index[60])
    assert result.status == "found"
    assert result.onset == series.index[200]
    assert result.sustained_mean_bz_nt == pytest.approx(-8.0)


def test_weak_southward_field_is_not_an_onset():
    values = np.full(900, 2.0)
    values[300:] = -1.0  # southward, but shallower than the 3 nT mean requirement
    series = _bz(values)
    result = find_southward_turning(series, series.index[60])
    assert result.status == "no_turning" and result.onset is None


def test_gappy_window_is_reported_as_insufficient_not_as_no_turning():
    values = np.full(900, 4.0)
    values[100:800] = np.nan
    series = _bz(values)
    result = find_southward_turning(series, series.index[60])
    assert result.status == "insufficient_data"
    assert result.window_valid_fraction < 0.8


def test_main_phase_onset_skips_shallow_lead_in_and_stops_at_first_deep_interval():
    """Shape of 20 Nov 2003 and 7 Nov 2004: a weak southward spell, a northward
    interval, a sharp dive into a deep interval, then a still deeper one later."""
    values = np.full(900, 5.0)
    values[100:200] = -12.0  # shallow lead-in, skipped
    values[300:420] = -35.0  # first deep interval: onset at 300
    values[500:700] = -50.0  # deeper, but later
    series = _bz(values)
    result = find_main_phase_onset(series, series.index[90])
    assert result.status == "found"
    assert result.onset == series.index[300]
    assert result.sustained_mean_bz_nt == pytest.approx(-35.0)
    # relative_depth = 1 walks back from the minimum instead.
    later = find_main_phase_onset(series, series.index[90], relative_depth=1.0)
    assert later.onset == series.index[500]


def test_main_phase_onset_walks_back_over_a_short_gap_but_not_a_long_one():
    values = np.full(900, 5.0)
    values[200:260] = -10.0  # the dive starts shallow ...
    values[260:] = -30.0  # ... and reaches the threshold here
    values[230:235] = np.nan  # five-minute gap on the way back: bridged
    series = _bz(values)
    assert find_main_phase_onset(series, series.index[100]).onset == series.index[200]
    values[210:235] = np.nan  # 25-minute gap: the turning cannot be placed
    series = _bz(values)
    assert find_main_phase_onset(series, series.index[100]).status == "insufficient_data"


def test_main_phase_onset_refuses_a_mostly_missing_window():
    values = np.full(900, 5.0)
    values[300:] = -30.0
    values[100:800] = np.nan
    series = _bz(values)
    result = find_main_phase_onset(series, series.index[50], search_after_h=12.0)
    assert result.status == "insufficient_data"


def test_main_phase_onset_reports_northward_events():
    series = _bz(np.full(600, 3.0))
    assert find_main_phase_onset(series, series.index[100]).status == "no_turning"


def test_halloween_onset_cannot_be_determined_from_omni(omni_path):
    """Zesta and Oliveira (2019) list 07:04 UT; OMNI HRO has no IMF there at all."""
    bz = read_omni_hro(omni_path)["bz_gsm_nt"]
    seed = pd.Timestamp("2003-10-29 06:11", tz="UTC")  # shock arrival
    result = find_southward_turning(bz, seed, search_after_h=6.0)
    assert result.status == "insufficient_data"
    assert result.onset is None
    assert find_main_phase_onset(bz, seed, search_after_h=6.0).status == "insufficient_data"
