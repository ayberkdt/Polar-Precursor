"""Reader for the ESA/TU Delft accelerometer density product (TOLEOS, CDF).

Files ``CH_OPER_DNS_ACC_2__<start>_<stop>_0001.cdf`` (CHAMP) and
``GR_OPER_DNS1ACC_2_...`` (GRACE) from the ESA Swarm dissemination server.
The TOLEOS Product Definition Document (SW-TN-DUT-GS-129_01 rev. 3, read
2026-10-06) lists the ``DNSxACC_2`` fields: ``time`` (CDF_EPOCH, UTC),
``altitude`` (m, GRS80 geodetic), ``latitude``/``longitude`` (deg),
``local_solar_time`` (h), ``density`` and ``density_orbitmean`` (kg/m3; the
orbit mean is a moving average), ``validity_flag`` and
``validity_flag_orbitmean`` (0 nominal, 1 anomalous). Uncertainty is given as
30 % of the variance of the orbit-averaged density or 5e-14 kg/m3, whichever
is larger. The real 2003-10-29 CHAMP file has 8640 records (10 s) and fill
values of 0.999e33 for the real fields and 127 for the flags, from the
variables' ``FILLVAL`` attributes.

Requires ``cdflib`` (optional dependency ``density``).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from space_environment.common.provenance import source_label

_REAL_COLUMNS = {
    "altitude": "altitude_m",
    "longitude": "longitude_deg",
    "latitude": "latitude_deg",
    "local_solar_time": "local_solar_time_h",
    "density": "density_kg_m3",
    "density_orbitmean": "density_orbitmean_kg_m3",
}
_FLAG_COLUMNS = {
    "validity_flag": "validity_flag",
    "validity_flag_orbitmean": "validity_flag_orbitmean",
}


def read_dns_acc_cdf(path: str | Path) -> pd.DataFrame:
    """Density product as a UTC-indexed DataFrame; fill values become NaN/<NA>."""
    import cdflib

    file_path = Path(path)
    cdf = cdflib.CDF(file_path)
    variables = set(cdf.cdf_info().zVariables)
    expected = {"time", *_REAL_COLUMNS, *_FLAG_COLUMNS}
    missing = expected - variables
    if missing:
        raise ValueError(f"{file_path.name}: variables missing: {sorted(missing)}.")
    globals_ = cdf.globalattsget()
    time_system = globals_.get("TIME SYSTEM", ["?"])[0]
    if time_system != "UTC":
        raise ValueError(f"{file_path.name}: TIME SYSTEM is {time_system!r}, expected UTC.")

    epoch = np.asarray(cdf.varget("time"), dtype=np.float64)
    stamps = pd.DatetimeIndex(cdflib.cdfepoch.to_datetime(epoch), name="time_utc").tz_localize(
        "UTC"
    )
    if not stamps.is_monotonic_increasing or stamps.has_duplicates:
        raise ValueError(f"{file_path.name}: time stamps are not strictly increasing.")

    columns: dict[str, pd.Series] = {}
    for variable, column in _REAL_COLUMNS.items():
        values = np.asarray(cdf.varget(variable), dtype=np.float64)
        fill = float(cdf.varattsget(variable).get("FILLVAL", "nan"))
        values = np.where(values == fill, np.nan, values)
        columns[column] = pd.Series(values, index=stamps)
    for variable, column in _FLAG_COLUMNS.items():
        raw = np.asarray(cdf.varget(variable)).astype(np.int64)
        fill = int(float(cdf.varattsget(variable).get("FILLVAL", "127")))
        flags = pd.Series(raw, index=stamps).astype("Int8")
        columns[column] = flags.mask(flags == fill)
    frame = pd.DataFrame(columns)
    frame.attrs["source"] = source_label(file_path)
    frame.attrs["satellite"] = globals_.get("SATELLITE", ["?"])[0]
    frame.attrs["processing_time"] = globals_.get("PROCESSING_TIME", ["?"])[0]
    frame.attrs["software_version"] = globals_.get("SOFTWARE_VERSION", ["?"])[0]
    return frame


def validity_summary(frame: pd.DataFrame) -> dict[str, float]:
    """Record count and the share of nominal (flag 0), anomalous (1) and missing rows."""
    flags = frame["validity_flag"]
    total = len(flags)
    return {
        "records": float(total),
        "nominal_fraction": float((flags == 0).sum() / total),
        "anomalous_fraction": float((flags == 1).sum() / total),
        "missing_fraction": float(flags.isna().sum() / total),
        "density_present_fraction": float(frame["density_kg_m3"].notna().sum() / total),
    }


__all__ = ["read_dns_acc_cdf", "validity_summary"]
