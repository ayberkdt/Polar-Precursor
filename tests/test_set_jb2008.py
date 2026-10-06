"""SET SOLFSMY and DTCFILE readers on excerpts of the files downloaded 2026-10-06."""

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from space_environment.io.set_jb2008 import read_dtcfile, read_solfsmy
from space_environment.physics.space_weather import JB2008_LAG_DAYS, dtc_at, jb2008_solar_inputs

FIXTURES = Path(__file__).parent / "fixtures"
SOLFSMY = FIXTURES / "solfsmy_2003_doy290_315_excerpt.txt"
DTCFILE = FIXTURES / "dtcfile_2003_doy290_315_excerpt.txt"


def test_solfsmy_row_of_29_october_2003():
    table = read_solfsmy(SOLFSMY)
    row = table.loc[pd.Timestamp("2003-10-29", tz="UTC")]
    # File line: 2003 302 2452942.0 279.1 140.3 155.1 126.7 182.7 132.4 185.2 140.5 1B11
    assert row["f10_sfu"] == 279.1 and row["f81c_sfu"] == 140.3
    assert row["s10_sfu"] == 155.1 and row["s81c_sfu"] == 126.7
    assert row["m10_sfu"] == 182.7 and row["m81c_sfu"] == 132.4
    assert row["y10_sfu"] == 185.2 and row["y81c_sfu"] == 140.5
    assert row["source_flags"] == "1B11"
    assert table.index[0] == pd.Timestamp("2003-10-17", tz="UTC")
    assert len(table) == 26
    assert table.attrs["source"].startswith("solfsmy_2003_doy290_315_excerpt.txt | sha256=")


def test_spline_filled_index_becomes_nan(tmp_path):
    path = tmp_path / "solfsmy.txt"
    path.write_text(
        "# header\n  2003 302   2452942.0 279.1 140.3 155.1 126.7 182.7 132.4 185.2 140.5  10B1\n"
    )
    table = read_solfsmy(path)
    row = table.iloc[0]
    assert row["f10_sfu"] == 279.1
    assert np.isnan(row["s10_sfu"]) and np.isnan(row["s81c_sfu"])
    assert row["m10_sfu"] == 182.7


def test_jb2008_lags_pick_earlier_days_per_index():
    table = read_solfsmy(SOLFSMY)
    inputs = jb2008_solar_inputs(table, datetime(2003, 10, 30, 7, 4, tzinfo=timezone.utc))
    assert JB2008_LAG_DAYS == {"f10": 1, "s10": 1, "m10": 2, "y10": 5}
    day = pd.Timestamp("2003-10-30", tz="UTC")
    assert inputs.f10 == table.at[day - pd.Timedelta(1, unit="D"), "f10_sfu"] == 279.1
    assert inputs.s10b == table.at[day - pd.Timedelta(1, unit="D"), "s81c_sfu"]
    assert inputs.m10 == table.at[day - pd.Timedelta(2, unit="D"), "m10_sfu"]
    assert inputs.y10 == table.at[day - pd.Timedelta(5, unit="D"), "y10_sfu"]
    assert inputs.y10b == table.at[day - pd.Timedelta(5, unit="D"), "y81c_sfu"]
    with pytest.raises(ValueError, match="no row"):
        jb2008_solar_inputs(table, datetime(2003, 10, 18, tzinfo=timezone.utc))


def test_dtcfile_hours_of_29_and_30_october_2003():
    series = read_dtcfile(DTCFILE)
    assert len(series) == 26 * 24
    # DTC 2003 302: 115 94 94 94 ... 465 ; DTC 2003 303: 458 414 370 ...
    assert series.at[pd.Timestamp("2003-10-29 00:00", tz="UTC")] == 115
    assert series.at[pd.Timestamp("2003-10-29 01:00", tz="UTC")] == 94
    assert series.at[pd.Timestamp("2003-10-29 23:00", tz="UTC")] == 465
    assert series.at[pd.Timestamp("2003-10-30 00:00", tz="UTC")] == 458
    assert dtc_at(series, datetime(2003, 10, 29, 23, 59, tzinfo=timezone.utc)) == 465
    with pytest.raises(ValueError, match="no value"):
        dtc_at(series, datetime(2003, 12, 1, tzinfo=timezone.utc))


def test_dtcfile_rejects_short_lines(tmp_path):
    path = tmp_path / "dtc.txt"
    path.write_text("DTC 2003 302 1 2 3\n")
    with pytest.raises(ValueError, match="24"):
        read_dtcfile(path)


def test_dtc_interpolation_follows_the_half_hour_convention():
    series = read_dtcfile(DTCFILE)
    hour_06 = series.at[pd.Timestamp("2003-10-29 06:00", tz="UTC")]
    hour_07 = series.at[pd.Timestamp("2003-10-29 07:00", tz="UTC")]
    at_half = dtc_at(series, datetime(2003, 10, 29, 7, 30, tzinfo=timezone.utc), interpolate=True)
    assert at_half == hour_07  # value k holds at k:30 UT
    on_the_hour = dtc_at(
        series, datetime(2003, 10, 29, 7, 0, tzinfo=timezone.utc), interpolate=True
    )
    assert on_the_hour == pytest.approx(0.5 * (hour_06 + hour_07))
    # pyatmos (independent implementation) gives 220.27 at 2003-10-30 07:04 on the same file.
    assert dtc_at(series, datetime(2003, 10, 30, 7, 4, tzinfo=timezone.utc), interpolate=True) == (
        pytest.approx(220.27, abs=0.01)
    )
