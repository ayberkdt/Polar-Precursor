"""Bridge to Sidera's space-weather contract.

Sidera's NRLMSIS adapter takes any object with ``get(utc) -> SpaceWeatherState``
(``sidera.physics.atmosphere.space_weather.SpaceWeatherProvider``). The adapter
here turns a ``GfzIndexProvider`` into exactly that. Sidera is imported lazily,
so this package stays usable without it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from space_environment.physics.space_weather import GfzIndexProvider


def _sidera_space_weather() -> Any:
    try:
        from sidera.physics.atmosphere import space_weather
    except ImportError as exc:  # pragma: no cover - exercised by the skip path
        raise ImportError(
            "The Sidera bridge needs the 'sidera' package importable in this environment."
        ) from exc
    return space_weather


@dataclass(frozen=True, slots=True)
class SideraSpaceWeatherAdapter:
    """Presents a ``GfzIndexProvider`` as a Sidera ``SpaceWeatherProvider``."""

    provider: GfzIndexProvider

    def get(self, utc: datetime) -> Any:
        state = self.provider.get(utc)
        return _sidera_space_weather().SpaceWeatherState(
            f107=state.f107,
            f107a=state.f107a,
            ap_daily=state.ap_daily,
            ap_history=state.ap_history,
            kp=state.kp,
            source=state.source,
        )


@dataclass(frozen=True, slots=True)
class SideraReferenceModel:
    """Quiet NRLMSIS reference through Sidera's adapter, one sample at a time.

    Implements ``analysis.reference_density.ReferenceModel`` so it can be
    passed to ``add_reference_density``; it is the slow cross-check of the
    vectorised ``QuietNrlmsisReference`` (same model, same indices).
    """

    provider: GfzIndexProvider
    version: str = "2.1"

    @property
    def label(self) -> str:
        return f"NRLMSIS {self.version} via Sidera NrlmsiseAtmosphere, {self.provider.geomagnetic}"

    def density(
        self,
        times: pd.DatetimeIndex,
        latitude_deg: np.ndarray,
        longitude_deg: np.ndarray,
        altitude_m: np.ndarray,
    ) -> np.ndarray:
        try:
            from sidera.frames.geodesy import WGS84, GeodeticPosition
            from sidera.physics.atmosphere.models import AtmosphereSample, NrlmsiseAtmosphere
        except ImportError as exc:  # pragma: no cover - exercised by the skip path
            raise ImportError("SideraReferenceModel needs the 'sidera' package.") from exc
        model = NrlmsiseAtmosphere(
            space_weather=SideraSpaceWeatherAdapter(self.provider),
            version=self.version,
            storm_mode=True,
        )
        out = np.empty(len(times))
        for i, moment in enumerate(times):
            position = GeodeticPosition(
                latitude_deg=float(latitude_deg[i]),
                longitude_deg=float(longitude_deg[i]),
                altitude_m=float(altitude_m[i]),
                ellipsoid=WGS84,
            )
            sample = AtmosphereSample(
                geodetic=position, epoch_tdb_s=0.0, utc=moment.to_pydatetime()
            )
            out[i] = model.evaluate(sample).density_kg_m3
        return out


__all__ = ["SideraReferenceModel", "SideraSpaceWeatherAdapter"]
