"""Hourly Dst from the WDC Kyoto HAPI server, saved to disk.

Dataset ids: ``hour_dst_final`` (definitive, through 2020 at the time of
writing), ``hour_dst_provisional``, ``hour_dst_realtime`` and the merged
``hour_dst``. The ``info`` document states ``timeStampLocation: center``: each
record is the hourly mean stamped at HH:29:30. The reader restamps records at
the start of the hour and records that it did so.

Each record carries a ``versionCode`` ``Mm`` (M: 0 real-time, 1 provisional,
2 final; m: reconversion generation). The code is kept so a catalogue can say
which processing level each value had.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from space_environment.io.hapi import HapiInfo, read_hapi_csv, read_hapi_info

_COLUMNS = {"dstValue": "dst_nt", "versionCode": "version_code"}


def read_kyoto_dst_hapi(csv_path: str | Path, info: HapiInfo | str | Path) -> pd.DataFrame:
    """Hourly Dst (nT) with its version code, indexed by the start of each hour."""
    if not isinstance(info, HapiInfo):
        info = read_hapi_info(info)
    if info.time_stamp_location != "center":
        raise ValueError(
            "Expected Kyoto hourly records stamped at bin centres "
            f"(timeStampLocation='center'), got {info.time_stamp_location!r}."
        )
    frame = read_hapi_csv(csv_path, info, rename=_COLUMNS)
    index = pd.DatetimeIndex(frame.index)
    if not ((index.minute == 29) & (index.second == 30)).all():
        raise ValueError("Kyoto hourly records should be stamped at HH:29:30 (bin centre).")
    frame.index = pd.DatetimeIndex(index.floor("h"), name="time_utc")
    frame.attrs["time_stamp_location"] = "start (restamped from centre by the reader)"
    return frame


def latest_complete_hour(frame: pd.DataFrame, at: pd.Timestamp, column: str = "dst_nt") -> float:
    """The last hourly value whose averaging interval ended at or before ``at``.

    An hourly mean is only known once the hour is over, so a forecast issued
    at 07:04 UT may use the 06:00-07:00 value and not the 07:00-08:00 one.
    Returns NaN when no complete hour is available.
    """
    cutoff = at - pd.Timedelta(1, unit="h")
    position = frame.index.searchsorted(cutoff, side="right")
    if position == 0:
        return float("nan")
    return float(frame[column].iloc[position - 1])


__all__ = ["latest_complete_hour", "read_kyoto_dst_hapi"]
