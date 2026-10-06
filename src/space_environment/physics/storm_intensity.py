"""Storm intensity classes by minimum SYM-H.

Class limits are those of Oliveira and Zesta (2019), Space Weather
(arXiv:1910.09622, Table 1), which states the boundary operators explicitly;
the companion paper Zesta and Oliveira (2019), doi:10.1029/2019GL085120, uses
the same limits with strict inequalities on both sides. The authors note that
"this definition of storm intensity intervals is arbitrary".
"""

from __future__ import annotations

import math
from enum import Enum


class StormIntensity(str, Enum):
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    SEVERE = "severe"
    EXTREME = "extreme"


# Upper-exclusive lower bounds in nT: a storm is in the first class whose
# threshold its minimum SYM-H reaches or exceeds.
_THRESHOLDS_NT: tuple[tuple[float, StormIntensity], ...] = (
    (-50.0, StormIntensity.WEAK),
    (-100.0, StormIntensity.MODERATE),
    (-150.0, StormIntensity.STRONG),
    (-250.0, StormIntensity.SEVERE),
)


def classify_by_min_symh(min_symh_nt: float) -> StormIntensity:
    """Weak: >= -50; moderate: [-100, -50); strong: [-150, -100); severe: [-250, -150);
    extreme: < -250 (all in nT)."""
    if not math.isfinite(min_symh_nt):
        raise ValueError("min_symh_nt must be finite.")
    for threshold, intensity in _THRESHOLDS_NT:
        if min_symh_nt >= threshold:
            return intensity
    return StormIntensity.EXTREME


__all__ = ["StormIntensity", "classify_by_min_symh"]
