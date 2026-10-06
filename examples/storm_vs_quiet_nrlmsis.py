"""Storm-time NRLMSIS 2.1 along a real CHAMP track, driven by measured GFZ indices.

This is the example that would land in Sidera's ``examples/atmosphere/`` once
the space-environment package is merged. It shows what Sidera cannot do
today: NRLMSIS storm mode fed by the real 3-hourly Ap history, against the
storm-free reference (same solar flux, Ap prescribed quiet), along the
CHAMP orbit of 29 October 2003 (the Halloween storm), compared with the
accelerometer density of that day.

Runs in the Sidera environment (needs ``pymsis`` through Sidera's optional
``atmosphere`` extra) with this package on the path:

    PYTHONPATH=src D:/sidera/.venv/Scripts/python.exe examples/storm_vs_quiet_nrlmsis.py

Inputs (local files, hashed into the output):
  data/raw/gfz/Kp_ap_Ap_SN_F107_since_1932.txt          GFZ daily Kp/ap/F10.7
  data/derived/champ_track_20031029_60s.csv              60-s subsample of the ESA
                                                          CH_OPER_DNS_ACC_2 product
"""

from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from space_environment.common.provenance import source_label
from space_environment.integration.sidera import SideraSpaceWeatherAdapter
from space_environment.physics.space_weather import GfzIndexProvider

ROOT = Path(__file__).resolve().parents[1]
GFZ = ROOT / "data/raw/gfz/Kp_ap_Ap_SN_F107_since_1932.txt"
TRACK = ROOT / "data/derived/champ_track_20031029_60s.csv"
BANDS = (
    ("polar S", -90.0, -60.0),
    ("mid S", -60.0, -30.0),
    ("low", -30.0, 30.0),
    ("mid N", 30.0, 60.0),
    ("polar N", 60.0, 90.0),
)


def main() -> int:
    from sidera.frames.geodesy import WGS84, GeodeticPosition
    from sidera.physics.atmosphere.models import (
        AtmosphereSample,
        NrlmsiseAtmosphere,
        pymsis_available,
    )

    if not pymsis_available():
        print('Sidera\'s optional NRLMSIS backend is missing: pip install -e ".[atmosphere]"')
        return 1

    measured = GfzIndexProvider.from_file(GFZ, geomagnetic="measured")
    quiet = GfzIndexProvider.from_file(GFZ, geomagnetic="quiet")
    storm_model = NrlmsiseAtmosphere(
        space_weather=SideraSpaceWeatherAdapter(measured), version="2.1", storm_mode=True
    )
    quiet_model = NrlmsiseAtmosphere(
        space_weather=SideraSpaceWeatherAdapter(quiet), version="2.1", storm_mode=True
    )

    rows: list[dict[str, str]] = []
    with TRACK.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    lat = np.array([float(r["latitude_deg"]) for r in rows])
    observed = np.array([float(r["density_kg_m3"]) for r in rows])
    storm = np.empty(len(rows))
    quiet_density = np.empty(len(rows))
    for i, row in enumerate(rows):
        utc = datetime.fromisoformat(row["time_utc"]).astimezone(timezone.utc)
        position = GeodeticPosition(
            latitude_deg=float(row["latitude_deg"]),
            longitude_deg=float(row["longitude_deg"]),
            altitude_m=float(row["altitude_m"]),
            ellipsoid=WGS84,
        )
        sample = AtmosphereSample(geodetic=position, epoch_tdb_s=0.0, utc=utc)
        storm[i] = storm_model.evaluate(sample).density_kg_m3
        quiet_density[i] = quiet_model.evaluate(sample).density_kg_m3

    state = measured.get(datetime(2003, 10, 29, 7, 4, tzinfo=timezone.utc))
    print("CHAMP, 2003-10-29, NRLMSIS 2.1 storm mode, 1440 track points (60 s)")
    print(
        f"indices at 07:04 UT: F10.7(prev day) {state.f107:.1f} sfu, F10.7a {state.f107a:.1f} sfu, "
        f"Ap {state.ap_daily:.0f}, ap history {state.ap_history}"
    )
    print(f"sources: {source_label(GFZ)}")
    print(f"         {source_label(TRACK)}")
    print()
    print(f"{'band':>8} {'n':>5} {'storm/quiet':>12} {'obs/quiet':>10} {'obs/storm':>10}")
    for name, lo, hi in BANDS:
        mask = (lat >= lo) & (lat < hi)
        ratio_model = np.exp(np.mean(np.log(storm[mask] / quiet_density[mask])))
        ratio_obs = np.exp(np.mean(np.log(observed[mask] / quiet_density[mask])))
        ratio_obs_storm = np.exp(np.mean(np.log(observed[mask] / storm[mask])))
        print(
            f"{name:>8} {mask.sum():>5} {ratio_model:>12.2f} {ratio_obs:>10.2f} "
            f"{ratio_obs_storm:>10.2f}"
        )
    print()
    print("Ratios are geometric means over the band. 'quiet' = same F10.7, Ap = 4 in every slot")
    print("(the storm-free reference). 'obs' = accelerometer density of the ESA product.")
    print("NRLMSIS is not ground truth; the last column is its storm-time error on this day.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
