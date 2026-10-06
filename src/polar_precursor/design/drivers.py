"""One driver function for ``build_design`` from the space_environment feature builders.

``build_design(drivers=...)`` wants a callable ``t0 -> {name: value}``. The
solar-wind builder (``DriverFeatureBuilder``, 1-minute OMNI) raises when ``t0``
lies outside its frame; the index builder (``IndexFeatureBuilder``, GFZ daily,
Hp30, Dst) answers everywhere its tables reach. ``CombinedDrivers`` joins them,
keeps the feature names unique, and turns a missing solar-wind epoch into NaN
features plus a ``solar_wind_available`` flag, so that samples without L1
coverage stay in the design and the pre-registration decides what to do with
them (plan 07: proposal is a separate secondary analysis).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

import pandas as pd

from space_environment.analysis.features import DriverFeatureBuilder
from space_environment.analysis.index_features import IndexFeatureBuilder

AVAILABILITY_FLAG = "solar_wind_available"


@dataclass(frozen=True)
class CombinedDrivers:
    solar_wind: DriverFeatureBuilder | None = None
    indices: IndexFeatureBuilder | None = None
    names: tuple[str, ...] = field(init=False)

    def __post_init__(self) -> None:
        if self.solar_wind is None and self.indices is None:
            raise ValueError("at least one builder is needed.")
        names: list[str] = []
        if self.solar_wind is not None:
            names.extend(self.solar_wind.feature_names)
            names.append(AVAILABILITY_FLAG)
        if self.indices is not None:
            clash = set(names) & set(self.indices.feature_names)
            if clash:
                raise ValueError(f"feature names clash between builders: {sorted(clash)}.")
            names.extend(self.indices.feature_names)
        object.__setattr__(self, "names", tuple(names))

    def __call__(self, t0: pd.Timestamp) -> Mapping[str, float]:
        features: dict[str, float] = {}
        if self.solar_wind is not None:
            try:
                features.update(self.solar_wind.features_at(t0))
                features[AVAILABILITY_FLAG] = 1.0
            except ValueError:
                features.update({name: float("nan") for name in self.solar_wind.feature_names})
                features[AVAILABILITY_FLAG] = 0.0
        if self.indices is not None:
            features.update(self.indices.features_at(t0))
        return features


__all__ = ["AVAILABILITY_FLAG", "CombinedDrivers"]
