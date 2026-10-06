"""Solar wind-magnetosphere coupling functions.

All functions take IMF components in GSM (nT) and bulk speed (km/s), accept
scalars or arrays, and propagate NaN.

Conventions
-----------
``B_T = sqrt(By^2 + Bz^2)`` is the IMF component transverse to the Sun-Earth
line. The clock angle is measured from GSM north, ``theta = atan2(By, Bz)``,
so ``theta = 0`` for purely northward and ``pi`` for purely southward IMF, and
``sin^2(theta/2) = (1 - Bz/B_T) / 2``.

Sources
-------
Merging electric field: Liu, Lühr, Doornbos and Ma (2010), Ann. Geophys. 28,
1633, Eq. (3), after Kan and Lee (1979). Its saturated form is their Eq. (4).
Newell coupling function: Newell et al. (2007), doi:10.1029/2006JA012015; the
form used here was confirmed from two secondary papers, not from the original.
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

FloatArray = npt.NDArray[np.float64]
ArrayLike = npt.ArrayLike

#: Truncation level of the saturated merging field in Liu et al. (2010) Eq. (4).
LIU_SATURATION_MV_M: float = 8.0


def transverse_field_nt(by_gsm_nt: ArrayLike, bz_gsm_nt: ArrayLike) -> FloatArray:
    """``B_T = sqrt(By^2 + Bz^2)`` in nT."""
    by = np.asarray(by_gsm_nt, dtype=np.float64)
    bz = np.asarray(bz_gsm_nt, dtype=np.float64)
    return np.hypot(by, bz)


def clock_angle_rad(by_gsm_nt: ArrayLike, bz_gsm_nt: ArrayLike) -> FloatArray:
    """IMF clock angle in [-pi, pi], zero for northward IMF."""
    by = np.asarray(by_gsm_nt, dtype=np.float64)
    bz = np.asarray(bz_gsm_nt, dtype=np.float64)
    return np.arctan2(by, bz)


def _sin_half_clock_squared(by: FloatArray, bz: FloatArray) -> FloatArray:
    """``sin^2(theta/2)`` without the angle; zero where the transverse field is zero."""
    b_t = np.hypot(by, bz)
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = np.where(b_t > 0.0, bz / b_t, 1.0)
    result = 0.5 * (1.0 - ratio)
    return np.where(np.isnan(by) | np.isnan(bz), np.nan, result)


def merging_electric_field_mv_m(
    speed_km_s: ArrayLike, by_gsm_nt: ArrayLike, bz_gsm_nt: ArrayLike
) -> FloatArray:
    """Kan-Lee merging electric field ``Em = v B_T sin^2(theta/2)`` in mV/m.

    With v in km/s and B in nT the product is in 1e-6 V/m, hence the 1e-3.
    """
    speed = np.asarray(speed_km_s, dtype=np.float64)
    by = np.asarray(by_gsm_nt, dtype=np.float64)
    bz = np.asarray(bz_gsm_nt, dtype=np.float64)
    return 1.0e-3 * speed * np.hypot(by, bz) * _sin_half_clock_squared(by, bz)


def saturated_merging_field_mv_m(
    merging_field_mv_m: ArrayLike, *, saturation_mv_m: float = LIU_SATURATION_MV_M
) -> FloatArray:
    """Liu et al. (2010) Eq. (4): ``Em_sat = s Em / sqrt(s^2 + Em^2)``.

    Liu et al. dropped this form for their final model; it is kept for
    sensitivity tests.
    """
    if saturation_mv_m <= 0.0:
        raise ValueError("saturation_mv_m must be positive.")
    em = np.asarray(merging_field_mv_m, dtype=np.float64)
    return saturation_mv_m * em / np.sqrt(saturation_mv_m**2 + em**2)


def newell_coupling(
    speed_km_s: ArrayLike, by_gsm_nt: ArrayLike, bz_gsm_nt: ArrayLike
) -> FloatArray:
    """Newell coupling function ``v^(4/3) B_T^(2/3) sin^(8/3)(theta/2)``.

    Returned in the mixed units that follow from v in km/s and B in nT, with no
    conversion constant. Use it as a relative driver; scale before regression.
    """
    speed = np.asarray(speed_km_s, dtype=np.float64)
    by = np.asarray(by_gsm_nt, dtype=np.float64)
    bz = np.asarray(bz_gsm_nt, dtype=np.float64)
    sin_half_sq = _sin_half_clock_squared(by, bz)
    return speed ** (4.0 / 3.0) * np.hypot(by, bz) ** (2.0 / 3.0) * sin_half_sq ** (4.0 / 3.0)


__all__ = [
    "LIU_SATURATION_MV_M",
    "clock_angle_rad",
    "merging_electric_field_mv_m",
    "newell_coupling",
    "saturated_merging_field_mv_m",
    "transverse_field_nt",
]
