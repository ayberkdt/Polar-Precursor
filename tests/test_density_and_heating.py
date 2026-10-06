"""Readers for the large raw files (ESA CDF density, Weimer heating HDF5).

These need the files under ``data/raw`` and are skipped when they are absent,
like Sidera's ``requires_data`` tests.
"""

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
CDF = ROOT / "data/raw/density/CHAMP/CH_OPER_DNS_ACC_2__20031029T000000_20031029T235959_0001.cdf"
HEATING = ROOT / "data/raw/heating/Heating_DeltaT.h5"


@pytest.mark.requires_data
def test_champ_density_file_of_29_october_2003():
    if not CDF.exists():
        pytest.skip(f"{CDF.name} not downloaded")
    pytest.importorskip("cdflib")
    from space_environment.io.toleos import read_dns_acc_cdf, validity_summary

    frame = read_dns_acc_cdf(CDF)
    assert len(frame) == 8640  # one record every 10 s
    assert frame.index[0] == pd.Timestamp("2003-10-29 00:00:00", tz="UTC")
    assert frame.index[-1] == pd.Timestamp("2003-10-29 23:59:50", tz="UTC")
    assert frame.attrs["satellite"] == "CHAMP"
    assert frame.attrs["source"].startswith(CDF.name + " | sha256=")
    assert str(frame["validity_flag"].dtype) == "Int8"
    first = frame.iloc[0]
    assert first["altitude_m"] == pytest.approx(417_923.84, abs=0.01)
    assert first["latitude_deg"] == pytest.approx(-76.536, abs=1e-3)
    assert first["density_kg_m3"] == pytest.approx(5.322e-12, rel=1e-3)
    summary = validity_summary(frame)
    assert summary["nominal_fraction"] == 1.0 and summary["density_present_fraction"] == 1.0
    assert 1.5e-12 < frame["density_kg_m3"].min() < frame["density_kg_m3"].max() < 2.0e-11


@pytest.mark.requires_data
def test_heating_series_is_four_minute_and_contiguous():
    if not HEATING.exists():
        pytest.skip(f"{HEATING.name} not downloaded")
    pytest.importorskip("h5py")
    from space_environment.io.weimer_heating import mjd_to_utc, read_heating_deltat

    assert mjd_to_utc(np.array([51544.0]))[0] == pd.Timestamp("2000-01-01", tz="UTC")
    frame = read_heating_deltat(
        HEATING,
        start=datetime(2003, 10, 28, tzinfo=timezone.utc),
        stop=datetime(2003, 10, 31, tzinfo=timezone.utc),
    )
    assert frame.index[0] == pd.Timestamp("2003-10-28 00:00", tz="UTC")
    assert frame.index[-1] == pd.Timestamp("2003-10-31 00:00", tz="UTC")
    steps = np.diff(frame.index.to_numpy()).astype("timedelta64[s]").astype(int)
    assert (steps == 240).all()
    assert frame["imf_ok"].all()
    # Halloween heating: hemispheric Poynting flux above 1 TW at the peak.
    assert frame[["jh_north_gw", "jh_south_gw"]].max().max() > 1000.0
    assert frame["delta_t_k"].max() > 500.0
