"""Storm-window dataset builder on the one real CHAMP day available locally."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from polar_precursor.config import load_config
from polar_precursor.experiment.dataset import (
    FILE_PREFIX,
    build_dataset,
    build_storm_design,
    daily_file,
    storm_days,
)
from space_environment.analysis.reference_density import pymsis_available
from space_environment.physics.space_weather import GfzIndexProvider

ROOT = Path(__file__).resolve().parents[1]
CDF_DIR = ROOT / "data/raw/density/CHAMP"
CDF = CDF_DIR / "CH_OPER_DNS_ACC_2__20031029T000000_20031029T235959_0001.cdf"
GFZ = ROOT / "tests/fixtures/gfz_kp_ap_f107_2003H2_excerpt.txt"

requires = pytest.mark.skipif(
    not (CDF.exists() and pymsis_available()), reason="needs the local CHAMP CDF and pymsis"
)


def _storms() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "disturbance_utc": [
                pd.Timestamp("2003-10-29T06:11:00Z"),
                pd.Timestamp("2003-11-20T08:00:00Z"),
            ],
            "window_end_utc": [
                pd.Timestamp("2003-10-30T16:19:00Z"),
                pd.Timestamp("2003-11-21T20:00:00Z"),
            ],
            "cluster": [11, 12],
            "intensity": ["extreme", "severe"],
        },
        index=[19, 23],
    )


def test_daily_file_and_storm_days(tmp_path: Path):
    for name in ("CHAMP", "GRACE-A", "GRACE-B"):
        assert FILE_PREFIX[name].endswith("ACC_2__")
    (tmp_path / "CH_OPER_DNS_ACC_2__20050101T000000_20050101T235959_0001.cdf").write_bytes(b"")
    (tmp_path / "CH_OPER_DNS_ACC_2__20050101T000000_20050101T235959_0002.cdf").write_bytes(b"")
    found = daily_file(tmp_path, "CHAMP", pd.Timestamp("2005-01-01T00:00:00Z"))
    assert found is not None and found.name.endswith("_0002.cdf")  # latest version wins
    assert daily_file(tmp_path, "CHAMP", pd.Timestamp("2005-01-02T00:00:00Z")) is None
    with pytest.raises(ValueError):
        daily_file(tmp_path, "SWARM", pd.Timestamp("2005-01-02T00:00:00Z"))
    days = storm_days(pd.Timestamp("2003-10-29T00:11:00Z"), pd.Timestamp("2003-10-30T16:19:00Z"))
    assert [d.strftime("%m-%d") for d in days] == ["10-29", "10-30"]


@requires
@pytest.mark.requires_data
def test_build_dataset_on_real_day_with_cache(tmp_path: Path):
    from space_environment.analysis.reference_density import QuietNrlmsisReference

    config = load_config(ROOT / "configs/pilot.toml")
    provider = GfzIndexProvider.from_file(GFZ, geomagnetic="measured")
    model = QuietNrlmsisReference(provider)
    storms = _storms()

    def drivers(t0: pd.Timestamp) -> dict[str, float]:
        return {"hour": float(t0.hour)}

    dataset, coverage = build_dataset(
        storms,
        cdf_dir=CDF_DIR,
        satellite="CHAMP",
        reference_model=model,
        drivers=drivers,
        config=config,
        cache_dir=tmp_path,
    )
    assert list(coverage["storm_row"]) == [19, 23]
    first = coverage.iloc[0]
    on_disk = sum(
        daily_file(CDF_DIR, "CHAMP", day) is not None
        for day in storm_days(
            pd.Timestamp("2003-10-29T00:11:00Z"), pd.Timestamp("2003-10-30T16:19:00Z")
        )
    )
    assert first["days_needed"] == 2 and first["days_found"] == on_disk >= 1
    assert first["track_records"] > 8000
    rows_by_group = dataset.groupby("group").size().to_dict()
    for _, record in coverage.iterrows():
        assert record["design_rows"] == rows_by_group.get(record["group"], 0)
    assert set(dataset["group"]) <= {11, 12}
    first_storm = dataset[dataset["group"] == 11]
    assert len(first_storm) > 0
    assert (first_storm["t0_utc"] >= pd.Timestamp("2003-10-29T06:11:00Z")).all()
    assert (first_storm["t0_utc"] <= pd.Timestamp("2003-10-30T16:19:00Z")).all()
    assert np.isfinite(dataset["target_value"]).all()
    assert "drv_hour" in dataset.columns

    again, coverage_again = build_dataset(
        storms,
        cdf_dir=CDF_DIR,
        satellite="CHAMP",
        reference_model=model,
        drivers=drivers,
        config=config,
        cache_dir=tmp_path,
        storm_rows=[19],
    )
    assert coverage_again.iloc[0]["cached"]
    pd.testing.assert_frame_equal(again, first_storm.reset_index(drop=True))

    design, record = build_storm_design(
        storms.loc[19],
        storms,
        cdf_dir=CDF_DIR,
        satellite="CHAMP",
        reference_model=model,
        drivers=None,
        config=config,
    )
    assert record.cached is False and len(design) == len(first_storm)
    assert not any(c.startswith("drv_") for c in design.columns)
