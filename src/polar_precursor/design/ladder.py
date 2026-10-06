"""Column convention and the model ladder B0 … M (main plan, "Model merdiveni").

A design frame has one row per forecast sample and these column families:

``target_value``            log density ratio of the target low-latitude pass
``persistence``             last low-latitude pass of the target's sector (B1)
``low_lag1 … low_lagN``     last N low-latitude passes, most recent first
``low_same_lag1 …``         last passes of the target's own sector (lag1 = persistence)
``low_other_lag1 …``        last passes of the other sector
``polar_north_lag1 … N``    last N northern polar passes, most recent first
``polar_south_lag1 … N``    last N southern polar passes
``mid_same``                mid-latitude (40-55°) mean from the pass ending at t0
``drv_*``                   driver features known at t0 (layer A, causal)
``drv_oracle_*``            driver features up to the target time (B3k only)
``geo_*``                   geometry: lead time, target local time, day of year, altitude
``group``                   storm cluster id (the independent unit)
``intensity``               storm class label; ``lead_bin`` lead-time bin label
``t0_utc``, ``target_mid_utc``, ``satellite``  bookkeeping

Each ladder step is a set of column families; the builder resolves them to the
columns present in a frame. B0 and B1 are not fitted: B0 predicts 0, B1 returns
the ``persistence`` column.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import pandas as pd

TARGET = "target_value"
PERSISTENCE = "persistence"
GROUP = "group"
INTENSITY = "intensity"
LEAD_BIN = "lead_bin"
META_COLUMNS: tuple[str, ...] = (
    GROUP,
    INTENSITY,
    LEAD_BIN,
    "t0_utc",
    "target_mid_utc",
    "satellite",
    "lead_time_min",
)


class Family(str, Enum):
    LOW = "low"
    POLAR = "polar"
    MID = "mid"
    DRIVERS = "drivers"
    ORACLE = "oracle"
    GEOMETRY = "geometry"


_PREFIX: dict[Family, tuple[str, ...]] = {
    Family.LOW: ("low_lag",),
    Family.POLAR: ("polar_north_lag", "polar_south_lag"),
    Family.MID: ("mid_same",),
    Family.DRIVERS: ("drv_",),
    Family.ORACLE: ("drv_oracle_",),
    Family.GEOMETRY: ("geo_",),
}


@dataclass(frozen=True, slots=True)
class ModelSpec:
    name: str
    families: tuple[Family, ...]
    fitted: bool = True
    question: str = ""

    def columns(self, frame: pd.DataFrame) -> list[str]:
        """Feature columns of this step present in ``frame``, in frame order."""
        wanted: list[str] = []
        for column in frame.columns:
            for family in self.families:
                if _belongs(column, family):
                    wanted.append(column)
                    break
        if self.fitted and not wanted:
            raise ValueError(f"{self.name}: none of {self.families} present in the frame.")
        return wanted


def _belongs(column: str, family: Family) -> bool:
    if family == Family.DRIVERS:
        return column.startswith("drv_") and not column.startswith("drv_oracle_")
    return any(column.startswith(prefix) for prefix in _PREFIX[family])


LADDER: dict[str, ModelSpec] = {
    "B0": ModelSpec("B0", (), fitted=False, question="reference model only, y = 0"),
    "B1": ModelSpec("B1", (), fitted=False, question="persistence of the target sector"),
    "B2": ModelSpec("B2", (Family.LOW, Family.GEOMETRY), question="own low-latitude history"),
    "D": ModelSpec("D", (Family.DRIVERS, Family.GEOMETRY), question="drivers only"),
    "B3": ModelSpec("B3", (Family.LOW, Family.DRIVERS, Family.GEOMETRY), question="main baseline"),
    "B3k": ModelSpec(
        "B3k",
        (Family.LOW, Family.DRIVERS, Family.ORACLE, Family.GEOMETRY),
        question="oracle drivers up to the target time",
    ),
    "B3t": ModelSpec(
        "B3t",
        (Family.LOW, Family.DRIVERS, Family.MID, Family.GEOMETRY),
        question="freshness control: mid-latitude from the same pass",
    ),
    "M": ModelSpec(
        "M",
        (Family.LOW, Family.DRIVERS, Family.POLAR, Family.GEOMETRY),
        question="main hypothesis: polar passes added",
    ),
}


def ladder(names: tuple[str, ...] | list[str]) -> list[ModelSpec]:
    unknown = [name for name in names if name not in LADDER]
    if unknown:
        raise ValueError(f"unknown ladder steps {unknown}; known: {list(LADDER)}.")
    return [LADDER[name] for name in names]


def polar_columns(frame: pd.DataFrame) -> list[str]:
    return [column for column in frame.columns if _belongs(column, Family.POLAR)]


__all__ = [
    "GROUP",
    "INTENSITY",
    "LADDER",
    "LEAD_BIN",
    "META_COLUMNS",
    "PERSISTENCE",
    "TARGET",
    "Family",
    "ModelSpec",
    "ladder",
    "polar_columns",
]
