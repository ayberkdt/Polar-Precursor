"""SILSO readers and the cycle-phase rule on excerpts of files read 2026-10-06."""

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from space_environment.analysis.solar_cycle import cycle_context, smoothed_sunspot_number
from space_environment.io.silso import read_silso_cycle_table, read_silso_monthly

FIXTURES = Path(__file__).parent / "fixtures"
MONTHLY = FIXTURES / "silso_sn_m_1995_2021_excerpt.txt"
SMOOTHED = FIXTURES / "silso_sn_ms_1995_2021_excerpt.txt"
CYCLES = FIXTURES / "silso_table_cycles_mima.txt"


def test_monthly_and_smoothed_values_of_october_2003():
    monthly = read_silso_monthly(MONTHLY)
    smoothed = read_silso_monthly(SMOOTHED)
    month = pd.Timestamp("2003-10-01", tz="UTC")
    # SN_m_tot_V2.0.txt: 2003 10 2003.790 97.8 8.8 570 ; SN_ms_tot: 89.1 6.6 570
    assert monthly.at[month, "sunspot_number"] == 97.8
    assert monthly.at[month, "standard_deviation"] == 8.8
    assert monthly.at[month, "observations"] == 570
    assert not monthly.at[month, "provisional"]
    assert smoothed.at[month, "sunspot_number"] == 89.1
    assert len(monthly) == 27 * 12


def test_missing_smoothed_months_are_nan(tmp_path):
    path = tmp_path / "sn.txt"
    path.write_text("2026 08 2026.623   -1.0  -1.0  1248 *\n")
    table = read_silso_monthly(path)
    assert np.isnan(table.iloc[0]["sunspot_number"]) and table.iloc[0]["provisional"]


def test_cycle_table_rows_23_to_25():
    cycles = read_silso_cycle_table(CYCLES)
    assert [cycle.number for cycle in cycles] == list(range(1, 26))
    cycle23 = cycles[22]
    assert cycle23.minimum == datetime(1996, 8, 1, tzinfo=timezone.utc)
    assert cycle23.minimum_sn == 11.2
    assert cycle23.maximum == datetime(2001, 11, 1, tzinfo=timezone.utc)
    assert cycle23.maximum_sn == 180.3
    assert cycles[23].minimum == datetime(2008, 12, 1, tzinfo=timezone.utc)
    assert cycles[23].maximum == datetime(2014, 4, 1, tzinfo=timezone.utc)
    assert cycles[24].minimum == datetime(2019, 12, 1, tzinfo=timezone.utc)
    assert cycles[24].maximum is None


def test_cycle_phase_fractions_count_months():
    cycles = read_silso_cycle_table(CYCLES)
    rising = cycle_context(cycles, datetime(2001, 3, 15, tzinfo=timezone.utc))
    assert rising.cycle == 23 and rising.phase == "rising"
    assert rising.months_since_minimum == 55
    assert rising.phase_fraction == pytest.approx(55 / 63)  # 1996-08 to 2001-11 is 63 months
    declining = cycle_context(cycles, datetime(2003, 10, 29, tzinfo=timezone.utc))
    assert declining.cycle == 23 and declining.phase == "declining"
    assert declining.phase_fraction == pytest.approx(23 / 85)  # 2001-11 to 2008-12 is 85 months
    assert cycle_context(cycles, datetime(2015, 6, 1, tzinfo=timezone.utc)).cycle == 24
    with pytest.raises(ValueError, match="no tabulated maximum"):
        cycle_context(cycles, datetime(2022, 1, 1, tzinfo=timezone.utc))


def test_smoothed_number_lookup():
    smoothed = read_silso_monthly(SMOOTHED)
    assert smoothed_sunspot_number(smoothed, datetime(2003, 10, 29, tzinfo=timezone.utc)) == 89.1
    assert np.isnan(smoothed_sunspot_number(smoothed, datetime(1990, 1, 1, tzinfo=timezone.utc)))
