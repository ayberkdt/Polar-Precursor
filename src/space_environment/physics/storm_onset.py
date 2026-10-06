"""Automatic storm zero-epoch: the sustained southward turning of IMF Bz.

The reference studies (Oliveira et al. 2017; Zesta and Oliveira 2019) define
storm onset as the time IMF Bz turns abruptly southward and pick it by visual
inspection of 1-minute OMNI data. This module replaces the visual pick with a
stated rule so a catalogue can be rebuilt and audited.

The rule is this project's design, not taken from a publication. Its default
parameters are starting values to be fixed against the published onset times
(Zesta and Oliveira 2019, Table 2) before any analysis uses them.

Rule
----
Starting from a seed time (for example the disturbance time of an ICME
catalogue), search ``[seed - search_before_h, seed + search_after_h]`` for the
first sample where Bz becomes negative and, over the next ``sustain_min``, (a) enough
samples exist, (b) at least ``negative_fraction`` of them are negative, and
(c) their mean is at or below ``-mean_below_nt``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd

OnsetStatus = Literal["found", "no_turning", "insufficient_data"]


@dataclass(frozen=True, slots=True)
class OnsetResult:
    """Outcome of an onset search.

    ``no_turning`` means the window had data and no sample met the rule (a
    northward-IMF event). ``insufficient_data`` means the window was too gappy
    to tell; the two must not be confused when building a catalogue.
    """

    status: OnsetStatus
    onset: pd.Timestamp | None
    window_valid_fraction: float
    sustained_mean_bz_nt: float | None


def find_southward_turning(
    bz_gsm_nt: pd.Series,
    seed: pd.Timestamp,
    *,
    search_before_h: float = 1.0,
    search_after_h: float = 12.0,
    sustain_min: float = 30.0,
    negative_fraction: float = 0.8,
    mean_below_nt: float = 3.0,
    min_valid_fraction: float = 0.8,
) -> OnsetResult:
    """Find the first sustained southward turning of Bz after ``seed``.

    ``bz_gsm_nt`` must be regularly sampled with an increasing DatetimeIndex
    (gaps as NaN), as OMNI HRO data are.
    """
    if not isinstance(bz_gsm_nt.index, pd.DatetimeIndex):
        raise ValueError("bz_gsm_nt must have a DatetimeIndex.")
    if not bz_gsm_nt.index.is_monotonic_increasing:
        raise ValueError("bz_gsm_nt must be in increasing time order.")
    if not 0.0 < negative_fraction <= 1.0 or not 0.0 < min_valid_fraction <= 1.0:
        raise ValueError("negative_fraction and min_valid_fraction must lie in (0, 1].")
    if mean_below_nt < 0.0:
        raise ValueError("mean_below_nt is a magnitude and must be non-negative.")

    search_before = pd.Timedelta(search_before_h, unit="h")
    search_after = pd.Timedelta(search_after_h, unit="h")
    sustain = pd.Timedelta(sustain_min, unit="m")
    window = bz_gsm_nt.loc[seed - search_before : seed + search_after + sustain]
    search = window.loc[: seed + search_after]
    if search.empty:
        return OnsetResult("insufficient_data", None, 0.0, None)
    valid_fraction = float(search.notna().mean())

    values = window.to_numpy(dtype=np.float64)
    times = window.index
    step = times[1] - times[0] if len(times) > 1 else pd.Timedelta(1, unit="m")
    span = max(int(round(sustain / step)), 1)
    negative = values < 0.0
    for i in range(len(search)):
        if not negative[i]:
            continue
        # A turning: the previous existing sample was not negative. The first
        # sample of the window counts, since nothing earlier is in view.
        if i > 0 and negative[i - 1]:
            continue
        ahead = values[i : i + span]
        present = ~np.isnan(ahead)
        if len(ahead) < span or present.mean() < min_valid_fraction:
            continue
        mean = float(ahead[present].mean())
        if (ahead[present] < 0.0).mean() >= negative_fraction and mean <= -mean_below_nt:
            return OnsetResult("found", times[i], valid_fraction, mean)

    status: OnsetStatus = (
        "no_turning" if valid_fraction >= min_valid_fraction else "insufficient_data"
    )
    return OnsetResult(status, None, valid_fraction, None)


def find_main_phase_onset(
    bz_gsm_nt: pd.Series,
    seed: pd.Timestamp,
    *,
    search_before_h: float = 1.0,
    search_after_h: float = 24.0,
    min_depth_nt: float = 5.0,
    relative_depth: float = 0.7,
    max_gap_min: float = 10.0,
    min_valid_fraction: float = 0.8,
) -> OnsetResult:
    """Onset as the sharp southward turning that leads into deep southward Bz.

    Why a second rule: on the published onsets of Zesta and Oliveira (2019),
    ``find_southward_turning`` locks onto the first weak southward excursion,
    hours before the pick the authors made. Their picks sit where Bz turns
    sharply south into an interval comparable in depth to the event's deepest
    Bz, even when a still deeper interval follows later (7 November 2004). See
    ``plans/kanit/epok_kurali_ayar_cikti_2026-10-06.txt``.

    The rule: take the first sample in the search window at which Bz reaches
    the depth threshold, ``min(-min_depth_nt, relative_depth * window
    minimum)``, and walk back through the contiguous negative samples, bridging
    data gaps up to ``max_gap_min`` but no northward sample. The first negative
    sample after the last non-negative one is the onset.
    ``sustained_mean_bz_nt`` is the mean Bz from the onset to the threshold
    crossing. The whole window must hold at least ``min_valid_fraction`` of
    its samples, otherwise the result is ``insufficient_data``.

    ``relative_depth=0`` reduces to "the first excursion below
    ``-min_depth_nt``"; ``relative_depth=1`` walks back from the minimum itself.

    The default ``relative_depth=0.7`` was chosen on the five published onsets
    for which OMNI has data (20 Nov 2003, 7 and 9 Nov 2004, 15 May 2005,
    24 Aug 2005): all five fall within 7 minutes, against 0 to 164 minutes for
    other values. Five events are a calibration, not a validation; the
    tolerance matches the 6-minute spread between the authors' own two papers
    for the same event.
    """
    if not isinstance(bz_gsm_nt.index, pd.DatetimeIndex):
        raise ValueError("bz_gsm_nt must have a DatetimeIndex.")
    if not bz_gsm_nt.index.is_monotonic_increasing:
        raise ValueError("bz_gsm_nt must be in increasing time order.")
    if min_depth_nt < 0.0 or max_gap_min < 0.0:
        raise ValueError("min_depth_nt and max_gap_min are magnitudes and must be non-negative.")
    if not 0.0 <= relative_depth <= 1.0:
        raise ValueError("relative_depth must lie in [0, 1].")

    before = pd.Timedelta(search_before_h, unit="h")
    after = pd.Timedelta(search_after_h, unit="h")
    window = bz_gsm_nt.loc[seed - before : seed + after]
    if window.empty or window.notna().sum() == 0:
        return OnsetResult("insufficient_data", None, 0.0, None)
    valid_fraction = float(window.notna().mean())
    if valid_fraction < min_valid_fraction:
        # "First deep interval" cannot be established when most of the window
        # is missing: the real one may sit inside the gap (29 October 2003).
        return OnsetResult("insufficient_data", None, valid_fraction, None)
    values = window.to_numpy(dtype=np.float64)
    times = window.index
    step = times[1] - times[0] if len(times) > 1 else pd.Timedelta(1, unit="m")
    gap_limit = max(int(round(pd.Timedelta(max_gap_min, unit="m") / step)), 0)

    overall_min = float(np.nanmin(values))
    if overall_min > -min_depth_nt:
        return OnsetResult("no_turning", None, valid_fraction, None)
    threshold = min(-min_depth_nt, relative_depth * overall_min)
    crossing = int(np.argmax(values <= threshold))  # NaN compares False

    i = crossing
    gap_run = 0
    while i > 0:
        previous = values[i - 1]
        if np.isnan(previous):
            gap_run += 1
            if gap_run > gap_limit:
                return OnsetResult("insufficient_data", None, valid_fraction, None)
            i -= 1
            continue
        gap_run = 0
        if previous >= 0.0:
            break
        i -= 1
    if i == 0:
        # The southward interval begins before the window: the turning is out of view.
        return OnsetResult("insufficient_data", None, valid_fraction, None)
    while np.isnan(values[i]):
        i += 1
    stretch = values[i : crossing + 1]
    present = ~np.isnan(stretch)
    if present.mean() < min_valid_fraction:
        return OnsetResult("insufficient_data", None, valid_fraction, None)
    return OnsetResult("found", times[i], valid_fraction, float(stretch[present].mean()))


__all__ = ["OnsetResult", "OnsetStatus", "find_main_phase_onset", "find_southward_turning"]
