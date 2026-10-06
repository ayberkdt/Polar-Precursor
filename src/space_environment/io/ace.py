"""ACE magnetic field and plasma readers (CDAWeb HAPI CSV), the OMNI fallback.

OMNI's 1-minute product is empty exactly where it matters most: in the
2003 file the IMF and plasma columns are fill from 2003-10-29 05:50 to
18:42 UT and for all of 2003-10-30. ACE itself kept measuring the field:
the CDAWeb ``AC_H0_MFI`` dataset (16 s) is complete on both days, while the
plasma dataset ``AC_H0_SWE`` (64 s) is entirely fill on 29 and 30 October
(measured 2026-10-06 on data saved from the CDAWeb HAPI server; see
``plans/kanit``). So the fallback restores the magnetic field, not the speed
or density; a density-free driver is what remains on such days.

The readers take HAPI CSV files saved from CDAWeb with their ``info`` JSON
(see ``space_environment.io.hapi``) and name the columns as the OMNI reader
does, so the same driver code runs on either source. ACE data are at L1, not
at the bow-shock nose like OMNI; the propagation delay lives in
``space_environment.physics.propagation``.

Sidera destination: ``sidera.io.space_weather.ace``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from space_environment.io.hapi import HapiInfo, read_hapi_csv

#: HAPI columns of ``AC_H0_MFI`` (parameters Time, Magnitude, BGSM, SC_pos_GSE).
MFI_COLUMNS: dict[str, str] = {
    "Magnitude": "b_magnitude_nt",
    "BGSM_0": "bx_gsm_nt",
    "BGSM_1": "by_gsm_nt",
    "BGSM_2": "bz_gsm_nt",
    "SC_pos_GSE_0": "x_gse_km",
    "SC_pos_GSE_1": "y_gse_km",
    "SC_pos_GSE_2": "z_gse_km",
}

#: HAPI columns of ``AC_H0_SWE`` (parameters Time, Np, Vp, V_GSE).
SWE_COLUMNS: dict[str, str] = {
    "Np": "proton_density_cm3",
    "Vp": "flow_speed_km_s",
    "V_GSE_0": "vx_gse_km_s",
    "V_GSE_1": "vy_gse_km_s",
    "V_GSE_2": "vz_gse_km_s",
}


def read_ace_mfi_hapi(csv_path: str | Path, info: HapiInfo | str | Path) -> pd.DataFrame:
    """ACE MAG 16-second field in GSM with the spacecraft GSE position, km."""
    return read_hapi_csv(csv_path, info, rename=MFI_COLUMNS)


def read_ace_swe_hapi(csv_path: str | Path, info: HapiInfo | str | Path) -> pd.DataFrame:
    """ACE SWEPAM 64-second proton density, bulk speed and GSE velocity."""
    return read_hapi_csv(csv_path, info, rename=SWE_COLUMNS)


__all__ = ["MFI_COLUMNS", "SWE_COLUMNS", "read_ace_mfi_hapi", "read_ace_swe_hapi"]
