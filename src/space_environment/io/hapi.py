"""Reader for HAPI CSV responses saved to disk together with their ``info`` JSON.

The Heliophysics Application Programmer's Interface (HAPI) serves time series
as header-less CSV whose column order and fill values are given by a separate
``info`` document. Both must be kept: the CSV alone does not say what its
columns are. Servers used in this project: WDC Kyoto (``hapi/info?id=...``,
HAPI 3.3) and NASA CDAWeb (HAPI 2.0, ACE data).

A vector parameter with ``size: [n]`` occupies ``n`` consecutive columns and
is expanded to ``<name>_0 .. <name>_<n-1>``. The first parameter must be the
``isotime`` column; it becomes the UTC index ``time_utc``. Fill values are
replaced by NaN. Nothing is fetched from the network.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from space_environment.common.provenance import source_label


@dataclass(frozen=True, slots=True)
class HapiParameter:
    """One parameter of a HAPI ``info`` response."""

    name: str
    type: str
    units: str | None
    fill: str | None
    size: tuple[int, ...]

    @property
    def width(self) -> int:
        width = 1
        for extent in self.size:
            width *= extent
        return width

    def column_names(self) -> list[str]:
        if self.width == 1:
            return [self.name]
        return [f"{self.name}_{index}" for index in range(self.width)]


@dataclass(frozen=True, slots=True)
class HapiInfo:
    """The parts of a HAPI ``info`` response the reader needs."""

    parameters: tuple[HapiParameter, ...]
    cadence: str | None
    time_stamp_location: str | None
    dataset_id: str | None
    source: str

    @property
    def column_names(self) -> list[str]:
        names: list[str] = []
        for parameter in self.parameters[1:]:
            names.extend(parameter.column_names())
        return names


def read_hapi_info(path: str | Path) -> HapiInfo:
    """Parse a saved ``info`` JSON document."""
    file_path = Path(path)
    with file_path.open(encoding="utf-8") as handle:
        document: dict[str, Any] = json.load(handle)
    raw_parameters = document.get("parameters")
    if not raw_parameters:
        raise ValueError(f"{file_path.name}: no 'parameters' list in the HAPI info document.")
    parameters = tuple(
        HapiParameter(
            name=str(item["name"]),
            type=str(item["type"]),
            units=item.get("units"),
            fill=None if item.get("fill") is None else str(item["fill"]),
            size=tuple(int(extent) for extent in item.get("size", ())),
        )
        for item in raw_parameters
    )
    if parameters[0].type != "isotime":
        raise ValueError(
            f"{file_path.name}: the first HAPI parameter must be the isotime column, "
            f"got {parameters[0].name!r} of type {parameters[0].type!r}."
        )
    return HapiInfo(
        parameters=parameters,
        cadence=document.get("cadence"),
        time_stamp_location=document.get("timeStampLocation"),
        dataset_id=document.get("x_dataset") or document.get("id"),
        source=source_label(file_path),
    )


def read_hapi_csv(
    csv_path: str | Path,
    info: HapiInfo | str | Path,
    *,
    rename: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    """Read a HAPI CSV data file into a UTC-indexed DataFrame.

    ``rename`` maps expanded column names (for example ``BGSM_2``) to the
    names the caller wants (``bz_gsm_nt``); unmapped columns keep the HAPI
    name. Every column of ``rename`` must exist, so a typo cannot silently
    leave a column unnamed.
    """
    file_path = Path(csv_path)
    if not isinstance(info, HapiInfo):
        info = read_hapi_info(info)
    names = ["time_utc", *info.column_names]
    frame = pd.read_csv(file_path, header=None, names=names, dtype=str, na_filter=False)
    if frame.empty:
        raise ValueError(f"{file_path.name}: the HAPI CSV file holds no records.")
    index = pd.to_datetime(frame.pop("time_utc"), utc=True, format="ISO8601")
    frame.index = pd.DatetimeIndex(index, name="time_utc")
    if not frame.index.is_monotonic_increasing:
        raise ValueError(f"{file_path.name}: records are not in increasing time order.")

    for parameter in info.parameters[1:]:
        for column in parameter.column_names():
            if parameter.type in ("double", "integer"):
                values = pd.to_numeric(frame[column], errors="raise").astype(np.float64)
                if parameter.fill is not None:
                    values = values.mask(values == float(parameter.fill))
                frame[column] = values
    if rename:
        missing = sorted(set(rename) - set(frame.columns))
        if missing:
            raise ValueError(f"{file_path.name}: columns to rename are not present: {missing}.")
        frame = frame.rename(columns=dict(rename))
    frame.attrs["source"] = source_label(file_path)
    frame.attrs["info_source"] = info.source
    frame.attrs["cadence"] = info.cadence
    frame.attrs["time_stamp_location"] = info.time_stamp_location
    return frame


__all__ = ["HapiInfo", "HapiParameter", "read_hapi_csv", "read_hapi_info"]
