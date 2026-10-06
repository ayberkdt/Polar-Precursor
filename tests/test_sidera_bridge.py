"""The provider must satisfy Sidera's space-weather contract as it exists today."""

from datetime import datetime, timezone

import pytest

from space_environment.integration.sidera import SideraSpaceWeatherAdapter
from space_environment.physics.space_weather import GfzIndexProvider

sidera_space_weather = pytest.importorskip(
    "sidera.physics.atmosphere.space_weather", reason="Sidera is not importable here"
)
pytestmark = pytest.mark.requires_sidera

ONSET = datetime(2003, 10, 29, 7, 4, tzinfo=timezone.utc)


def test_adapter_is_a_sidera_provider(gfz_daily_path):
    adapter = SideraSpaceWeatherAdapter(GfzIndexProvider.from_file(gfz_daily_path))
    assert isinstance(adapter, sidera_space_weather.SpaceWeatherProvider)
    state = adapter.get(ONSET)
    assert isinstance(state, sidera_space_weather.SpaceWeatherState)
    assert state.nrlmsis_ap_array(storm_mode=True) == (204.0, 400.0, 27.0, 39.0, 27.0, 22.0, 13.5)
    assert state.f107 == 274.4


def test_storm_mode_nrlmsis_runs_on_measured_indices(gfz_daily_path):
    """End to end: GFZ file -> adapter -> Sidera NRLMSIS in storm mode -> density."""
    pytest.importorskip("pymsis")
    from sidera.frames.geodesy import WGS84, GeodeticPosition
    from sidera.physics.atmosphere.models import AtmosphereSample, NrlmsiseAtmosphere

    def density(geomagnetic: str, storm_mode: bool) -> float:
        provider = GfzIndexProvider.from_file(gfz_daily_path, geomagnetic=geomagnetic)
        model = NrlmsiseAtmosphere(
            space_weather=SideraSpaceWeatherAdapter(provider), version="2.1", storm_mode=storm_mode
        )
        sample = AtmosphereSample(
            geodetic=GeodeticPosition(
                latitude_deg=0.0, longitude_deg=0.0, altitude_m=400e3, ellipsoid=WGS84
            ),
            epoch_tdb_s=0.0,
            utc=ONSET,
        )
        return model.evaluate(sample).density_kg_m3

    storm = density("measured", True)
    quiet = density("quiet", True)
    assert quiet > 0.0
    # Ap history of 400 against a prescribed Ap of 4: the storm atmosphere is denser.
    assert storm > 1.3 * quiet
