"""HAPI CSV reader, ACE fallback readers and the Kyoto Dst reader on real excerpts.

Fixtures are byte-exact excerpts of files saved from the CDAWeb and WDC Kyoto
HAPI servers on 2026-10-06, with their ``info`` documents.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from space_environment.io.ace import read_ace_mfi_hapi, read_ace_swe_hapi
from space_environment.io.hapi import read_hapi_csv, read_hapi_info
from space_environment.io.kyoto import latest_complete_hour, read_kyoto_dst_hapi
from space_environment.physics.propagation import ballistic_delay_s, minute_means, shift_by_delay

FIXTURES = Path(__file__).parent / "fixtures"
MFI_CSV = FIXTURES / "ace_mfi_20031029_0530_0640_excerpt.csv"
MFI_INFO = FIXTURES / "AC_H0_MFI_info.json"
SWE_CSV = FIXTURES / "ace_swe_20031028_20031029_excerpt.csv"
SWE_INFO = FIXTURES / "AC_H0_SWE_info.json"
DST_CSV = FIXTURES / "hour_dst_final_20031001_20031201.csv"
DST_INFO = FIXTURES / "hour_dst_final_info.json"


def test_info_expands_vector_parameters_in_order():
    info = read_hapi_info(MFI_INFO)
    assert [parameter.name for parameter in info.parameters] == [
        "Time",
        "Magnitude",
        "BGSM",
        "SC_pos_GSE",
    ]
    assert info.column_names == [
        "Magnitude",
        "BGSM_0",
        "BGSM_1",
        "BGSM_2",
        "SC_pos_GSE_0",
        "SC_pos_GSE_1",
        "SC_pos_GSE_2",
    ]
    assert info.parameters[1].fill == "-1.0E31"


def test_generic_reader_keeps_hapi_names_and_records_sources():
    frame = read_hapi_csv(MFI_CSV, MFI_INFO)
    assert list(frame.columns) == read_hapi_info(MFI_INFO).column_names
    assert frame.index.name == "time_utc" and str(frame.index.tz) == "UTC"
    assert frame.attrs["source"].startswith("ace_mfi_20031029_0530_0640_excerpt.csv | sha256=")
    assert frame.attrs["info_source"].startswith("AC_H0_MFI_info.json | sha256=")


def test_rename_must_name_existing_columns():
    with pytest.raises(ValueError, match="not present"):
        read_hapi_csv(MFI_CSV, MFI_INFO, rename={"BGSM_3": "nope"})


def test_ace_mfi_values_of_the_first_record_and_full_coverage_in_the_omni_gap():
    frame = read_ace_mfi_hapi(MFI_CSV, MFI_INFO)
    first = frame.iloc[0]
    assert frame.index[0] == pd.Timestamp("2003-10-29 05:30:12", tz="UTC")
    assert first["b_magnitude_nt"] == pytest.approx(10.579)
    assert first["bx_gsm_nt"] == pytest.approx(9.142)
    assert first["by_gsm_nt"] == pytest.approx(-5.184)
    assert first["bz_gsm_nt"] == pytest.approx(1.149)
    assert first["x_gse_km"] == pytest.approx(1_476_239.0)
    # 2003-10-29T05:41:24Z,9.958,1.418e+00,-9.496e+00,-1.129e+00 (seen on the server)
    at = frame.loc[pd.Timestamp("2003-10-29 05:41:24", tz="UTC")]
    assert at["bz_gsm_nt"] == pytest.approx(-1.129)
    # OMNI has no IMF from 05:50 UT; ACE itself is complete here.
    gap = frame.loc["2003-10-29 05:50":"2003-10-29 06:40", "bz_gsm_nt"]
    assert len(gap) > 180 and gap.notna().all()
    steps = np.diff(frame.index.to_numpy()).astype("timedelta64[s]").astype(int)
    assert np.median(steps) == 16


def test_ace_swe_fill_becomes_nan_and_plasma_is_absent_on_29_october():
    frame = read_ace_swe_hapi(SWE_CSV, SWE_INFO)
    first = frame.iloc[0]
    assert frame.index[0] == pd.Timestamp("2003-10-28 00:00:20", tz="UTC")
    assert first["proton_density_cm3"] == pytest.approx(0.8993)
    assert first["flow_speed_km_s"] == pytest.approx(475.40)
    assert first["vx_gse_km_s"] == pytest.approx(-474.8)
    assert np.isnan(frame.iloc[1]["flow_speed_km_s"])  # -1.0E31 in the file
    on_29th = frame.loc["2003-10-29"]
    assert len(on_29th) > 20 and on_29th["flow_speed_km_s"].isna().all()


def test_ballistic_delay_sign_and_nan_rules():
    delay = ballistic_delay_s([1_476_239.0, 1_476_239.0], [-474.8, np.nan], x_target_km=17 * 6371.0)
    assert delay[0] == pytest.approx((1_476_239.0 - 17 * 6371.0) / 474.8)
    assert np.isnan(delay[1])
    with pytest.raises(ValueError, match="negative"):
        ballistic_delay_s([1.0e6], [300.0], x_target_km=0.0)


def test_shift_and_minute_means_align_to_omni_cadence():
    frame = read_ace_mfi_hapi(MFI_CSV, MFI_INFO)
    shifted = shift_by_delay(frame, 3000.0)
    assert shifted.index[0] == frame.index[0] + pd.Timedelta(3000, unit="s")
    dropped = shift_by_delay(frame.iloc[:3], [np.nan, 10.0, 10.0])
    assert len(dropped) == 2
    means = minute_means(frame, columns=["bz_gsm_nt"], min_samples=3)
    assert (means.index.second == 0).all()
    # The 05:30 minute holds only the 05:30:12, :28 and :44 samples: three, so kept.
    assert not np.isnan(means.iloc[0, 0])
    sparse = minute_means(frame.iloc[:2], columns=["bz_gsm_nt"], min_samples=3)
    assert np.isnan(sparse.iloc[0, 0])


def test_kyoto_dst_is_restamped_to_hour_start_and_matches_the_wdc_table():
    frame = read_kyoto_dst_hapi(DST_CSV, DST_INFO)
    assert (frame.index.minute == 0).all()
    # WDC monthly table (OCTOBER 2003, day 1, hour 1): -11 nT.
    assert frame.at[pd.Timestamp("2003-10-01 00:00", tz="UTC"), "dst_nt"] == -11
    assert frame.at[pd.Timestamp("2003-10-30 22:00", tz="UTC"), "dst_nt"] == -383
    assert frame.at[pd.Timestamp("2003-10-30 22:00", tz="UTC"), "version_code"] == 20
    assert frame["dst_nt"].min() == -422
    assert frame["dst_nt"].idxmin() == pd.Timestamp("2003-11-20 20:00", tz="UTC")
    assert "restamped" in frame.attrs["time_stamp_location"]


def test_latest_complete_hour_never_uses_the_running_hour():
    frame = read_kyoto_dst_hapi(DST_CSV, DST_INFO)
    at = pd.Timestamp("2003-10-29 07:04", tz="UTC")
    value = latest_complete_hour(frame, at)
    assert value == frame.at[pd.Timestamp("2003-10-29 06:00", tz="UTC"), "dst_nt"]
    exactly = latest_complete_hour(frame, pd.Timestamp("2003-10-29 07:00", tz="UTC"))
    assert exactly == frame.at[pd.Timestamp("2003-10-29 06:00", tz="UTC"), "dst_nt"]
    assert np.isnan(latest_complete_hour(frame, pd.Timestamp("2003-10-01 00:30", tz="UTC")))
