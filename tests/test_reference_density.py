"""Quiet NRLMSIS reference along the real CHAMP day (pymsis, no network)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from space_environment.analysis.passes import segment_track
from space_environment.analysis.reference_density import (
    REFERENCE_COLUMN,
    QuietNrlmsisReference,
    add_reference_density,
    pymsis_available,
)
from space_environment.physics.space_weather import GfzIndexProvider

FIXTURES = Path(__file__).parent / "fixtures"
TRACK = FIXTURES / "champ_track_20031029_60s.csv"

pytestmark = pytest.mark.skipif(not pymsis_available(), reason="pymsis not installed")


def _track() -> pd.DataFrame:
    track = pd.read_csv(TRACK, index_col="time_utc", parse_dates=True)
    track.index = pd.DatetimeIndex(track.index)
    return track


def test_quiet_reference_uses_provider_f107_and_is_storm_free(gfz_daily_path: Path):
    provider = GfzIndexProvider.from_file(gfz_daily_path, geomagnetic="measured")
    track = _track()
    model = QuietNrlmsisReference(provider)
    f107, f107a = model.solar_inputs(track.index)
    state = provider.get(track.index[0].to_pydatetime())
    assert np.all(f107 == state.f107) and np.all(f107a == state.f107a)
    rho = model.density(
        track.index,
        track["latitude_deg"].to_numpy(),
        track["longitude_deg"].to_numpy(),
        track["altitude_m"].to_numpy(),
    )
    assert rho.shape == (len(track),) and np.all(np.isfinite(rho)) and np.all(rho > 0.0)
    # 29 Oct 2003: main phase starts about 06 UT (plan 05). Observed over quiet reference
    # must rise after onset; the pre-onset ratio is near 1 (measured 0.91 for 00-02 UT).
    log_ratio = np.log(track["density_kg_m3"].to_numpy() / rho)
    hour = track.index.hour
    before = np.exp(log_ratio[hour < 6].mean())
    after = np.exp(log_ratio[hour >= 12].mean())
    assert after > before and after > 1.0

    # plan 03: ap = 4 in every slot equals the daily-Ap-only mode of the model
    from pymsis import msis

    dates = track.index.tz_localize(None).to_numpy()
    daily_mode = msis.calculate(
        dates,
        track["longitude_deg"].to_numpy(),
        track["latitude_deg"].to_numpy(),
        track["altitude_m"].to_numpy() / 1000.0,
        f107,
        f107a,
        np.full((len(track), 7), 4.0),
        version="2.1",
    )[:, 0]
    assert np.allclose(rho, daily_mode, rtol=1e-6)


def test_add_reference_density_stride_interpolation_is_close(gfz_daily_path: Path):
    provider = GfzIndexProvider.from_file(gfz_daily_path, geomagnetic="measured")
    model = QuietNrlmsisReference(provider)
    track = _track()
    full = add_reference_density(track, model, stride=1)
    coarse = add_reference_density(track, model, stride=2)  # 2-minute nodes on the 60-s track
    assert REFERENCE_COLUMN in full.columns and full.attrs["reference_stride"] == 1
    assert coarse.attrs["reference_model"].startswith("NRLMSIS 2.1")
    delta = np.abs(np.log(coarse[REFERENCE_COLUMN]) - np.log(full[REFERENCE_COLUMN]))
    # measured 2026-10-06 on this track: max |delta ln rho| 0.0060 (2 min), 0.0117 (3 min),
    # 0.051 (6 min), 0.13 (10 min); grows about quadratically with the node spacing
    assert delta.max() < 0.01
    six = add_reference_density(track, model, stride=6)
    delta_six = np.abs(np.log(six[REFERENCE_COLUMN]) - np.log(full[REFERENCE_COLUMN]))
    assert 0.03 < delta_six.max() < 0.08
    coarse = six
    assert np.allclose(  # exact at the evaluated nodes up to the exp(log()) round trip
        full[REFERENCE_COLUMN].to_numpy()[::6], coarse[REFERENCE_COLUMN].to_numpy()[::6], rtol=1e-12
    )

    segments = segment_track(full, reference=REFERENCE_COLUMN)
    low = segments[(segments["band"] == "low") & segments["complete"]]
    assert len(low) > 20 and np.isfinite(low["target_mean"]).all()
    assert low["target_mean"].mean() > 0.0  # storm day: observed above reference
    with pytest.raises(ValueError):
        add_reference_density(track, model, stride=0)


def test_missing_positions_are_bridged_by_interpolation(gfz_daily_path: Path):
    provider = GfzIndexProvider.from_file(gfz_daily_path, geomagnetic="measured")
    model = QuietNrlmsisReference(provider)
    track = _track().iloc[:60].copy()
    track.loc[track.index[10:13], ["latitude_deg", "longitude_deg", "altitude_m"]] = np.nan
    out = add_reference_density(track, model, stride=1)
    assert np.isfinite(out[REFERENCE_COLUMN]).all()
    full = add_reference_density(_track().iloc[:60], model, stride=1)
    delta = np.abs(np.log(out[REFERENCE_COLUMN]) - np.log(full[REFERENCE_COLUMN]))
    assert delta.iloc[10:13].max() < 0.1 and delta.drop(delta.index[10:13]).max() < 1e-12
    empty = track.copy()
    empty[["latitude_deg", "longitude_deg", "altitude_m"]] = np.nan
    assert add_reference_density(empty, model)[REFERENCE_COLUMN].isna().all()
