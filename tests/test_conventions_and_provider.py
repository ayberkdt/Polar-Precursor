"""Index conventions and the GFZ-backed provider.

The Ap-history expectation is derived by hand from the 3-hourly ap rows of
26-29 October 2003 in the fixture:

    26 Oct:  9  7  6  7  4  4 18 22
    27 Oct: 22 18 18  7  7  9  5  4
    28 Oct: 15 39 22 39 12 27 18 27
    29 Oct: 39 27 400 ...

At 07:04 UT on the 29th the current interval is 06-09 UT (ap 400); the three
earlier intervals hold 27, 39, 27; the 12-33 h mean is
(18+27+12+39+22+39+15+4)/8 = 22.0 and the 36-57 h mean is
(5+9+7+7+18+18+22+22)/8 = 13.5.
"""

from datetime import datetime, timedelta, timezone

import pytest

from space_environment.io.gfz import read_gfz_daily
from space_environment.physics.index_conventions import (
    centred_mean_f107,
    nrlmsis_ap_history,
    three_hourly_ap,
)
from space_environment.physics.space_weather import QUIET_AP, GfzIndexProvider

UTC = timezone.utc
ONSET = datetime(2003, 10, 29, 7, 4, tzinfo=UTC)


def test_ap_history_hand_derived(gfz_daily_path):
    series = three_hourly_ap(read_gfz_daily(gfz_daily_path))
    assert nrlmsis_ap_history(series, ONSET) == (400.0, 27.0, 39.0, 27.0, 22.0, 13.5)


def test_ap_history_changes_at_interval_boundary(gfz_daily_path):
    series = three_hourly_ap(read_gfz_daily(gfz_daily_path))
    before = nrlmsis_ap_history(series, datetime(2003, 10, 29, 5, 59, 59, tzinfo=UTC))
    after = nrlmsis_ap_history(series, datetime(2003, 10, 29, 6, 0, 0, tzinfo=UTC))
    assert before[0] == 27.0 and after[0] == 400.0
    assert after[1] == before[0]


def test_ap_history_refuses_missing_slot(gfz_daily_path):
    series = dict(three_hourly_ap(read_gfz_daily(gfz_daily_path)))
    series[datetime(2003, 10, 28, 21, tzinfo=UTC)] = None
    with pytest.raises(ValueError, match="missing"):
        nrlmsis_ap_history(series, ONSET)


def test_centred_mean_is_symmetric_window():
    day0 = datetime(2003, 1, 1, tzinfo=UTC)
    ramp = {day0 + timedelta(days=i): float(i) for i in range(200)}
    # A linear ramp averaged over a symmetric window returns its centre value.
    assert centred_mean_f107(ramp, day0 + timedelta(days=100)) == pytest.approx(100.0)
    with pytest.raises(ValueError, match="centred mean is not defined"):
        centred_mean_f107(ramp, day0 + timedelta(days=5))


def test_provider_applies_nrlmsis_conventions(gfz_daily_path):
    raw = GfzIndexProvider.from_file(gfz_daily_path, f107_burst_screen=False)
    state = raw.get(ONSET)
    assert state.f107 == 274.4  # observed flux of 28 October, not the 29th (291.7)
    table = read_gfz_daily(gfz_daily_path).by_day()
    centre = datetime(2003, 10, 29, tzinfo=UTC)
    window = [table[centre + timedelta(days=d)].f107_obs_sfu for d in range(-40, 41)]
    assert state.f107a == pytest.approx(sum(window) / 81.0)
    assert 146.0 < state.f107a < 148.0
    # With the burst screen (default) the 560.9 sfu burst of 2003-11-04 leaves the
    # 81-day window: the centred mean drops by about 5 sfu (measured 141.57).
    screened = GfzIndexProvider.from_file(gfz_daily_path).get(ONSET)
    assert screened.f107 == 274.4
    assert 141.0 < screened.f107a < 142.0
    state = screened
    assert state.ap_daily == 204.0
    assert state.kp == 9.0
    assert state.nrlmsis_ap_array(storm_mode=True) == (204.0, 400.0, 27.0, 39.0, 27.0, 22.0, 13.5)
    assert state.nrlmsis_ap_array(storm_mode=False) == (204.0,) * 7


def test_quiet_mode_keeps_solar_flux_and_prescribes_ap(gfz_daily_path):
    measured = GfzIndexProvider.from_file(gfz_daily_path).get(ONSET)
    quiet = GfzIndexProvider.from_file(gfz_daily_path, geomagnetic="quiet").get(ONSET)
    assert (quiet.f107, quiet.f107a) == (measured.f107, measured.f107a)
    assert quiet.nrlmsis_ap_array(storm_mode=True) == (QUIET_AP,) * 7
    assert "prescribed quiet" in quiet.source


def test_provider_rejects_naive_and_uncovered_epochs(gfz_daily_path):
    provider = GfzIndexProvider.from_file(gfz_daily_path)
    with pytest.raises(ValueError, match="timezone-aware"):
        provider.get(datetime(2003, 10, 29, 7, 4))
    with pytest.raises(ValueError, match="No GFZ record"):
        provider.get(datetime(2004, 3, 1, tzinfo=UTC))
    # Inside the table but too close to its edge for a centred 81-day mean.
    with pytest.raises(ValueError, match="centred mean is not defined"):
        provider.get(datetime(2003, 7, 10, tzinfo=UTC))


def test_f107_burst_screen_replaces_radio_burst_days(gfz_daily_path):
    from datetime import datetime, timedelta, timezone

    from space_environment.physics.index_conventions import screen_f107_bursts
    from space_environment.physics.space_weather import GfzIndexProvider

    base = datetime(2003, 11, 1, tzinfo=timezone.utc)
    series = {base + timedelta(days=i): 120.0 + i for i in range(9)}
    series[base + timedelta(days=3)] = 560.9  # 2003-11-04 in the real GFZ file
    cleaned, replaced = screen_f107_bursts(series)
    assert replaced == (base + timedelta(days=3),)
    assert cleaned[base + timedelta(days=3)] == pytest.approx((122.0 + 124.0) / 2)
    assert all(cleaned[d] == series[d] for d in series if d not in replaced)

    screened = GfzIndexProvider.from_file(gfz_daily_path, geomagnetic="measured")
    raw = GfzIndexProvider.from_file(
        gfz_daily_path, geomagnetic="measured", f107_burst_screen=False
    )
    burst_day = datetime(2003, 11, 4, tzinfo=timezone.utc)
    assert burst_day in screened.f107_replaced_days
    next_day = datetime(2003, 11, 5, 12, tzinfo=timezone.utc)
    assert raw.get(next_day).f107 == pytest.approx(560.9)
    assert 100.0 < screened.get(next_day).f107 < 200.0
    assert "replaced" in screened.f107_source
