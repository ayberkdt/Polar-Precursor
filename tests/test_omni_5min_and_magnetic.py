"""OMNI 5-minute format on a real excerpt; quasi-dipole coordinates when apexpy is built."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from space_environment.io.omni import read_omni_hro

FIXTURES = Path(__file__).parent / "fixtures"


def test_omni_5min_excerpt_of_the_halloween_days():
    frame = read_omni_hro(FIXTURES / "omni_5min_2003_doy301_303_excerpt.asc", cadence="5min")
    assert len(frame) == 3 * 288
    assert frame.index[0] == pd.Timestamp("2003-10-28 00:00", tz="UTC")
    assert list(frame.columns[-3:]) == [
        "proton_flux_gt10mev",
        "proton_flux_gt30mev",
        "proton_flux_gt60mev",
    ]
    # Record 2003-10-28 12:00 of the yearly 5-minute file (read 2026-10-06).
    at = frame.loc[pd.Timestamp("2003-10-28 12:00", tz="UTC")]
    assert at["b_magnitude_nt"] == pytest.approx(12.21)
    assert at["bz_gsm_nt"] == pytest.approx(7.67)
    assert at["flow_speed_km_s"] == pytest.approx(761.3)
    assert at["sym_h_nt"] == -31.0
    coverage = frame["bz_gsm_nt"].groupby(frame.index.date).apply(lambda s: s.notna().mean())
    assert coverage.iloc[0] == 1.0 and coverage.iloc[2] == 0.0  # the same gap as at 1 min


def test_quasi_dipole_coordinates_on_the_champ_track():
    pytest.importorskip("apexpy")
    from space_environment.physics.magnetic_coordinates import add_quasi_dipole, decimal_year

    assert decimal_year(pd.Timestamp("2003-10-01", tz="UTC")) == pytest.approx(2003.748, abs=1e-3)
    track = pd.read_csv(
        FIXTURES / "champ_track_20031029_60s.csv", index_col="time_utc", parse_dates=True
    )
    track.index = pd.DatetimeIndex(track.index, name="time_utc")
    out = add_quasi_dipole(track.iloc[:200])
    assert {"qd_latitude_deg", "qd_longitude_deg", "mlt_h"} <= set(out.columns)
    assert out["qd_latitude_deg"].notna().all()
    assert out["mlt_h"].between(0.0, 24.0).all()
    # QD and geographic latitude agree in sign and differ by less than the dipole tilt margin.
    assert np.abs(out["qd_latitude_deg"] - out["latitude_deg"]).max() < 25.0
    assert np.corrcoef(out["qd_latitude_deg"], out["latitude_deg"])[0, 1] > 0.99
