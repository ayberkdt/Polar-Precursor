"""Reader for OMNI high-resolution (HRO) ASCII files.

Files: ``omni_minYYYY.asc`` (1 minute) and ``omni_5minYYYY.asc`` (5 minutes)
from NASA SPDF. Records are blank-separated with no header; every minute of the
year is present and gaps are written as fill values. Field order and fill
values follow ``hroformat.txt`` and ``hro_modified_format.txt`` in the SPDF
``high_res_omni`` directory.

The solar-wind fields are already time-shifted by OMNI to the bow-shock nose;
the record time stamp is the time at the nose, not at the L1 spacecraft.

Fill values are replaced by NaN. Large storms are exactly where the fills
cluster: in the 2003 file the IMF and plasma columns are entirely fill from
2003-10-29 05:50 UT to 18:42 UT and for all of 2003-10-30, while the
geomagnetic index columns stay populated. Always inspect coverage before
building driver features for an event.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from space_environment.common.provenance import source_label

Cadence = Literal["1min", "5min"]

# (column name, fill value) in file order. Names carry their unit and frame.
_HRO_FIELDS: tuple[tuple[str, float | None], ...] = (
    ("year", None),
    ("day_of_year", None),
    ("hour", None),
    ("minute", None),
    ("imf_spacecraft_id", 99),
    ("plasma_spacecraft_id", 99),
    ("imf_points", 999),
    ("plasma_points", 999),
    ("percent_interpolated", 999),
    ("timeshift_s", 999999),
    ("timeshift_rms_s", 999999),
    ("phase_front_normal_rms", 99.99),
    ("time_between_observations_s", 999999),
    ("b_magnitude_nt", 9999.99),
    ("bx_gse_nt", 9999.99),
    ("by_gse_nt", 9999.99),
    ("bz_gse_nt", 9999.99),
    ("by_gsm_nt", 9999.99),
    ("bz_gsm_nt", 9999.99),
    ("b_scalar_rms_nt", 9999.99),
    ("b_vector_rms_nt", 9999.99),
    ("flow_speed_km_s", 99999.9),
    ("vx_gse_km_s", 99999.9),
    ("vy_gse_km_s", 99999.9),
    ("vz_gse_km_s", 99999.9),
    ("proton_density_cm3", 999.99),
    ("temperature_k", 9999999.0),
    ("flow_pressure_npa", 99.99),
    ("electric_field_mv_m", 999.99),
    ("plasma_beta", 999.99),
    ("alfven_mach", 999.9),
    ("x_gse_re", 9999.99),
    ("y_gse_re", 9999.99),
    ("z_gse_re", 9999.99),
    ("bow_shock_x_gse_re", 9999.99),
    ("bow_shock_y_gse_re", 9999.99),
    ("bow_shock_z_gse_re", 9999.99),
    ("ae_nt", 99999),
    ("al_nt", 99999),
    ("au_nt", 99999),
    ("sym_d_nt", 99999),
    ("sym_h_nt", 99999),
    ("asy_d_nt", 99999),
    ("asy_h_nt", 99999),
    ("pc_n", 999.99),
    ("magnetosonic_mach", 99.9),
)
_PROTON_FLUX_FIELDS: tuple[tuple[str, float | None], ...] = (
    ("proton_flux_gt10mev", 99999.99),
    ("proton_flux_gt30mev", 99999.99),
    ("proton_flux_gt60mev", 99999.99),
)
# ``time_between_observations_s`` is documented as I7 with fill 9999999 but the
# distributed 1-minute files write 999999; both are treated as fill.
_EXTRA_FILLS: dict[str, tuple[float, ...]] = {"time_between_observations_s": (9999999.0,)}


def hro_column_names(cadence: Cadence = "1min") -> tuple[str, ...]:
    """Column names of an HRO record, in file order."""
    fields = _HRO_FIELDS + (_PROTON_FLUX_FIELDS if cadence == "5min" else ())
    return tuple(name for name, _ in fields)


def read_omni_hro(path: str | Path, *, cadence: Cadence = "1min") -> pd.DataFrame:
    """Read an HRO ASCII file (or a contiguous excerpt) into a UTC-indexed frame.

    The index is the start of each averaging interval. Fill values become NaN.
    ``frame.attrs["source"]`` records the file name and SHA-256.
    """
    if cadence not in ("1min", "5min"):
        raise ValueError("cadence must be '1min' or '5min'.")
    file_path = Path(path).expanduser()
    if not file_path.is_file():
        raise ValueError(f"OMNI file not found: {file_path}")
    fields = _HRO_FIELDS + (_PROTON_FLUX_FIELDS if cadence == "5min" else ())
    names = [name for name, _ in fields]
    frame = pd.read_csv(file_path, sep=r"\s+", header=None, dtype=np.float64)
    if frame.shape[1] != len(names):
        raise ValueError(
            f"{file_path} has {frame.shape[1]} fields per record; an HRO {cadence} "
            f"record has {len(names)}. Check the cadence."
        )
    frame.columns = pd.Index(names)

    for name, fill in fields:
        if fill is None:
            continue
        fills = (float(fill), *_EXTRA_FILLS.get(name, ()))
        frame[name] = frame[name].mask(frame[name].isin(fills))

    year = frame["year"].astype(int).astype(str)
    start = pd.to_datetime(year + "-01-01", utc=True)
    frame.index = pd.DatetimeIndex(
        start
        + pd.to_timedelta(frame["day_of_year"] - 1, unit="D")
        + pd.to_timedelta(frame["hour"], unit="h")
        + pd.to_timedelta(frame["minute"], unit="m"),
        name="time_utc",
    )
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError(f"{file_path}: record times are not strictly increasing.")
    frame = frame.drop(columns=["year", "day_of_year", "hour", "minute"])
    frame.attrs["source"] = source_label(file_path)
    frame.attrs["cadence"] = cadence
    return frame


def coverage(frame: pd.DataFrame, columns: tuple[str, ...]) -> pd.Series:
    """Fraction of records in which each of ``columns`` holds a measurement."""
    return frame[list(columns)].notna().mean()


__all__ = ["Cadence", "coverage", "hro_column_names", "read_omni_hro"]
