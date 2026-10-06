"""Band segmentation and forecast samples on the real CHAMP track of 2003-10-29.

The fixture is a 60-second subsample of the ESA CH_OPER_DNS_ACC_2 product (10 s)
exported by ``space_environment.io.toleos``; the orbit geometry (about 15.4
revolutions per day) is what the expected counts in plans/04 rest on.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from space_environment.analysis.passes import (
    Band,
    SampleConfig,
    SegmentationConfig,
    build_samples,
    orbit_direction,
    segment_track,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def track():
    frame = pd.read_csv(
        FIXTURES / "champ_track_20031029_60s.csv", index_col="time_utc", parse_dates=True
    )
    frame.index = pd.DatetimeIndex(frame.index, name="time_utc")
    return frame


@pytest.fixture(scope="module")
def segments(track):
    return segment_track(track)


def test_segment_counts_match_the_orbit_geometry(segments):
    counts = segments.groupby(["band", "hemisphere"]).size().to_dict()
    # plans/04: about 31 low-latitude segments and 15-16 polar passes per hemisphere per day.
    assert counts[("low", "both")] == 31
    assert counts[("polar", "north")] in (15, 16) and counts[("polar", "south")] in (15, 16)
    assert counts[("mid", "north")] == 31 and counts[("mid", "south")] == 31


def test_low_latitude_midpoints_are_half_a_period_apart(segments):
    low = segments[segments["band"] == "low"].sort_values("mid_utc")
    gaps_min = low["mid_utc"].diff().dropna().dt.total_seconds() / 60.0
    assert gaps_min.min() >= 45.0 and gaps_min.max() <= 47.0


def test_segments_of_one_band_never_overlap_and_are_complete(segments):
    for _, group in segments.groupby(["band", "hemisphere"]):
        group = group.sort_values("start_utc")
        assert (
            group["start_utc"].iloc[1:].to_numpy() > group["end_utc"].iloc[:-1].to_numpy()
        ).all()
    assert segments["complete"].all()
    assert segments["valid_fraction"].min() == 1.0


def test_polar_pass_spans_the_turning_point_and_reaches_high_latitude(segments):
    polar = segments[segments["band"] == "polar"].iloc[1:-1]  # drop day-edge passes
    assert (polar["direction"] == "mixed").all()
    assert polar["max_abs_band_latitude_deg"].min() > 85.0
    assert polar["samples"].between(12, 16).all()  # about 14 min above 63 degrees


def test_target_is_log_density_or_log_ratio(track, segments):
    low = segments[segments["band"] == "low"].iloc[0]
    window = track.loc[low["start_utc"] : low["end_utc"]]
    assert low["target_mean"] == pytest.approx(np.log(window["density_kg_m3"]).mean())
    with_reference = track.assign(reference_kg_m3=track["density_kg_m3"] * 2.0)
    ratio = segment_track(with_reference, reference="reference_kg_m3")
    assert ratio["target_mean"].to_numpy() == pytest.approx(np.full(len(ratio), -np.log(2.0)))


def test_invalid_flags_lower_the_valid_fraction(track):
    spoiled = track.copy()
    spoiled.loc[spoiled.index[:30], "validity_flag"] = 1
    segments = segment_track(spoiled, config=SegmentationConfig(min_valid_fraction=0.7))
    first = segments.iloc[0]
    assert first["valid_fraction"] < 1.0 and not first["complete"]


def test_orbit_direction_ignores_equatorial_jitter():
    lat = np.array([-80.0, -40.0, 0.0, 0.1, 0.0, 40.0, 80.0, 85.0, 80.0, 40.0])
    direction = orbit_direction(lat, min_turning_latitude_deg=45.0)
    assert direction.tolist() == [1, 1, 1, 1, 1, 1, 1, 1, -1, -1]


def test_samples_pair_polar_pass_ends_with_later_low_segments(segments):
    samples = build_samples(segments, config=SampleConfig(lead_window_min=(60.0, 270.0)))
    assert not samples.empty
    assert samples["lead_time_min"].between(60.0, 270.0).all()
    by_id = segments.set_index("segment_id")
    for _, sample in samples.iterrows():
        assert by_id.at[sample["polar_segment"], "end_utc"] == sample["t0_utc"]
        assert by_id.at[sample["target_segment"], "start_utc"] > sample["t0_utc"]
        for input_id in (*sample["input_low_segments"], *sample["input_polar_north_segments"]):
            assert by_id.at[input_id, "end_utc"] <= sample["t0_utc"]
    # Each t0 sees the low segments whose midpoints fall 1-4.5 h ahead: about five.
    per_t0 = samples.groupby("t0_utc").size()
    last_full = samples["t0_utc"].max() - pd.Timedelta(270, unit="m")
    assert per_t0[per_t0.index <= last_full].between(4, 6).all()  # day end truncates the rest


def test_custom_bands_and_missing_columns():
    with pytest.raises(ValueError, match="lower < upper"):
        Band("bad", 50.0, 40.0)
    with pytest.raises(ValueError, match="lacks columns"):
        segment_track(
            pd.DataFrame({"latitude_deg": [0.0]}, index=pd.DatetimeIndex(["2003-10-29"], tz="UTC"))
        )
