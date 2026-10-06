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


__all__ = ["SideraSpaceWeatherAdapter"]
