"""Pre-computed polar heating and delta-T series of Weimer et al. (2023).

File ``Heating_DeltaT.h5`` from Zenodo record 7667515, the data archive of
Weimer, Mehta, Licata and Tobiska, "Global Variations in the Time Delays
Between Polar Ionospheric Heating and the Neutral Density Response", Space
Weather, doi:10.1029/2022SW003410. The archive ReadMe (read 2026-10-06)
describes the file as: area-integrated Poynting flux in both hemispheres from
the W05 model (``JHNORTH``, ``JHSOUTH`` in GW), the delta-T values derived by
integration (``DELTAT`` in kelvin), ``MJTIMES`` as Modified Julian Date, at
4-minute intervals from 1 January 2000 to 1 January 2020, contiguous, with
IMF dropouts filled by interpolation and flagged ``OKFLAG = 0``.

Measured on the downloaded file: 2,629,800 records, every step exactly 240 s,
first stamp 2000-01-01 00:04 UT, last 2020-01-01 00:00 UT.

Requires ``h5py`` (optional dependency ``heating``).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from space_environment.common.provenance import source_label
from space_environment.common.timeutil import require_utc

_MJD_AT_UNIX_EPOCH = 40587.0  # 1970-01-01 00:00 UTC


def mjd_to_utc(mjd: np.ndarray) -> pd.DatetimeIndex:
    """Modified Julian Date (days) to a UTC DatetimeIndex, rounded to the second."""
    seconds = np.round((np.asarray(mjd, dtype=np.float64) - _MJD_AT_UNIX_EPOCH) * 86400.0)
    return pd.DatetimeIndex(pd.to_datetime(seconds, unit="s", utc=True), name="time_utc")


def read_heating_deltat(
    path: str | Path,
    *,
    start: datetime | None = None,
    stop: datetime | None = None,
) -> pd.DataFrame:
    """Columns ``delta_t_k``, ``jh_north_gw``, ``jh_south_gw``, ``imf_ok`` (bool).

    ``start``/``stop`` (UTC, inclusive) restrict the rows returned; the whole
    file is still read, since it is about 58 MB.
    """
    import h5py

    file_path = Path(path)
    with h5py.File(file_path, "r") as handle:
        expected = {"DELTAT", "JHNORTH", "JHSOUTH", "MJTIMES", "OKFLAG"}
        missing = expected - set(handle.keys())
        if missing:
            raise ValueError(f"{file_path.name}: datasets missing: {sorted(missing)}.")
        index = mjd_to_utc(handle["MJTIMES"][()])
        frame = pd.DataFrame(
            {
                "delta_t_k": np.asarray(handle["DELTAT"][()], dtype=np.float64),
                "jh_north_gw": np.asarray(handle["JHNORTH"][()], dtype=np.float64),
                "jh_south_gw": np.asarray(handle["JHSOUTH"][()], dtype=np.float64),
                "imf_ok": np.asarray(handle["OKFLAG"][()]) != 0,
            },
            index=index,
        )
    if not frame.index.is_monotonic_increasing or frame.index.has_duplicates:
        raise ValueError(f"{file_path.name}: time stamps are not strictly increasing.")
    if start is not None:
        frame = frame.loc[pd.Timestamp(require_utc(start)) :]
    if stop is not None:
        frame = frame.loc[: pd.Timestamp(require_utc(stop))]
    frame.attrs["source"] = source_label(file_path)
    return frame


__all__ = ["mjd_to_utc", "read_heating_deltat"]
