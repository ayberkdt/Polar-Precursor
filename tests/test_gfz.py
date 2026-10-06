"""GFZ readers against a real excerpt.

Expected values are read off the file rows themselves and, for 2003-10-29,
cross-checked against the GFZ JSON web service on 2026-10-05 (Kp and observed
F10.7 for 27-31 October 2003).
"""

from datetime import datetime, timedelta, timezone

import pytest

from space_environment.io.gfz import read_gfz_daily, read_gfz_hpo

UTC = timezone.utc


def test_daily_row_of_halloween_storm(gfz_daily_path):
    table = read_gfz_daily(gfz_daily_path)
    assert len(table.records) == 184
    assert table.first_day == datetime(2003, 7, 1, tzinfo=UTC)
    assert table.last_day == datetime(2003, 12, 31, tzinfo=UTC)
    record = table.by_day()[datetime(2003, 10, 29, tzinfo=UTC)]
    assert record.kp == (4.667, 4.0, 9.0, 8.0, 7.667, 7.667, 8.667, 8.667)
    assert record.ap == (39, 27, 400, 207, 179, 179, 300, 300)
    assert record.ap_daily == 204
    assert record.sunspot_number == 250
    assert record.f107_obs_sfu == 291.7
    assert record.f107_adj_sfu == 287.7
    assert record.definitive == 2
    assert "sha256=" in table.source


def test_observed_flux_matches_web_service(gfz_daily_path):
    by_day = read_gfz_daily(gfz_daily_path).by_day()
    observed = [by_day[datetime(2003, 10, d, tzinfo=UTC)].f107_obs_sfu for d in range(27, 32)]
    assert observed == [257.2, 274.4, 291.7, 271.4, 248.9]


def test_missing_values_become_none(tmp_path):
    row = (
        "1932 01 01     0     0.5 1352 10  3.333  2.667  2.333  2.667  3.333  2.667  3.333"
        "  3.333   18   12    9   12   18   12   18   18    15  22     -1.0     -1.0 2\n"
    )
    path = tmp_path / "early.txt"
    path.write_text("# header\n" + row, encoding="utf-8")
    record = read_gfz_daily(path).records[0]
    assert record.f107_obs_sfu is None and record.f107_adj_sfu is None
    assert record.ap_daily == 15


def test_malformed_row_reports_line_number(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_text("# header\n2003 10 29 1 2 3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="line 2"):
        read_gfz_daily(path)


def test_hp30_half_hour_series(gfz_hpo_path):
    records = read_gfz_hpo(gfz_hpo_path)
    assert len(records) == 6 * 48
    by_start = {record.start: record for record in records}
    peak = by_start[datetime(2003, 10, 29, 6, 30, tzinfo=UTC)]
    assert peak.hp30 == 12.0 and peak.ap30 == 617
    assert records[1].start - records[0].start == timedelta(minutes=30)
