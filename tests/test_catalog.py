"""Richardson-Cane reader and the storm catalogue builder on real data.

The xlsx fixture is the Dataverse file (doi:10.7910/DVN/C2MHTH, CC0) as
downloaded on 2026-10-06; the OMNI fixture covers 28-30 October 2003.
"""

from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from space_environment.analysis.catalog import build_storm_catalog, read_richardson_cane
from space_environment.io.omni import read_omni_hro

FIXTURES = Path(__file__).parent / "fixtures"
XLSX = FIXTURES / "richardson_cane_icmetable2.xlsx"


@pytest.fixture(scope="module")
def catalogue():
    pytest.importorskip("openpyxl")
    return read_richardson_cane(XLSX)


def test_event_count_and_the_halloween_rows(catalogue):
    assert len(catalogue.records) == 644
    assert len(catalogue.between(2001, 2015)) == 334
    by_row = {record.row: record for record in catalogue.records}
    halloween = by_row[241]
    assert halloween.disturbance_utc == datetime(2003, 10, 29, 6, 11, tzinfo=timezone.utc)
    assert halloween.icme_start_utc == datetime(2003, 10, 29, 11, 0, tzinfo=timezone.utc)
    assert halloween.icme_end_utc == datetime(2003, 10, 30, 3, 0, tzinfo=timezone.utc)
    assert halloween.quality == 2
    assert halloween.dv_km_s == 900.0 and halloween.dv_note == "S"
    assert halloween.v_icme_km_s == 1300.0 and halloween.v_max_km_s == 1900.0
    assert halloween.b_nt == 32.0
    assert halloween.mc == 2.0 and halloween.mc_note == "H"
    assert halloween.dst_nt == -353.0 and halloween.dst_note is None
    assert halloween.v_transit_km_s == 2185.0
    following = by_row[242]
    assert following.disturbance_note == "A"
    assert following.dst_nt == -383.0


def test_annotations_are_kept_not_dropped(catalogue):
    dst_notes = [record.dst_note for record in catalogue.records if record.dst_note]
    assert dst_notes.count("P") == 112
    quality_weak = [record for record in catalogue.records if record.quality_note == "W"]
    assert len(quality_weak) == 49 and all(record.quality is not None for record in quality_weak)
    # Row 309 (2007-01-14): disturbance 12:48 after the ICME start 12:00; accepted.
    row_309 = next(record for record in catalogue.records if record.row == 309)
    assert row_309.disturbance_utc > row_309.icme_start_utc


def test_catalogue_rows_for_28_to_30_october_2003(catalogue, omni_path):
    omni = read_omni_hro(omni_path)
    events = [
        record
        for record in catalogue.records
        if datetime(2003, 10, 28, tzinfo=timezone.utc)
        <= record.disturbance_utc
        < datetime(2003, 10, 31, tzinfo=timezone.utc)
    ]
    table = build_storm_catalog(events, omni)
    assert list(table["rc_row"]) == [240, 241, 242]
    first, second, third = (table.iloc[i] for i in range(3))

    # Windows stop at the next disturbance, so each minimum is the event's own.
    assert first["window_end_utc"] == second["disturbance_utc"]
    assert first["symh_coverage"] == 1.0
    assert first["min_symh_nt"] == -58.0 and first["intensity"] == "moderate"
    assert first["onset_status"] == "found"
    assert first["onset_minus_disturbance_min"] == 18.0
    assert first["bz_coverage"] == 1.0

    assert second["min_symh_nt"] == -391.0 and second["intensity"] == "extreme"
    assert second["min_symh_utc"] == pd.Timestamp("2003-10-30 01:48", tz="UTC")
    assert second["onset_status"] == "insufficient_data"  # OMNI gap from 05:50 UT
    assert second["bz_coverage"] < 0.25

    # The excerpt ends on 30 October: not enough SYM-H for the third event.
    assert third["symh_coverage"] < 0.2
    assert np.isnan(third["min_symh_nt"]) and third["intensity"] is None
    assert (table["cluster"] == 1).all()
    assert table.attrs["omni_source"].startswith("omni_min_2003_doy301_303_excerpt.asc")


def test_distant_events_get_separate_clusters(catalogue, omni_path):
    omni = read_omni_hro(omni_path)
    by_row = {record.row: record for record in catalogue.records}
    table = build_storm_catalog([by_row[240], by_row[241], by_row[243]], omni, cluster_gap_h=24.0)
    assert list(table["cluster"]) == [1, 1, 2]  # row 243 is 20 November 2003
