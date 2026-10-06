"""Uctan uca gercek veri hatti, tek gun: CHAMP 29 Eki 2003 (6 Eki 2026).
    PYTHONPATH=src .venv/Scripts/python.exe plans/kanit/uctan_uca_2003_10_29.py

Adimlar: ESA CDF (10 s) -> QD enlem/MLT (apexpy) -> sakin NRLMSIS 2.1 referansi (pymsis,
Ap = 4, adim 6 = 60 s) -> bant parcalari (hedef ln rho/rho_ref) -> ornekler -> Richardson-Cane
+ OMNI kesiti ile firtina tablosu -> CombinedDrivers (OMNI 1 dk + GFZ + Hp30 + Dst)
-> tasarim matrisi -> results/<kosu>/ (design.parquet, manifest.json).
Tek firtina oldugu icin capraz dogrulama kosulmaz; hattin her adimi gercek veride calisir mi,
sutunlar ve bosluk oranlari nedir, referans adim hatasi 10 s urunde ne kadar: bunlar olculur.
"""

from __future__ import annotations

import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from space_environment.analysis.catalog import build_storm_catalog, read_richardson_cane
from space_environment.analysis.features import DriverFeatureBuilder
from space_environment.analysis.index_features import IndexFeatureBuilder
from space_environment.analysis.passes import build_samples, segment_track
from space_environment.analysis.reference_density import (
    REFERENCE_COLUMN,
    QuietNrlmsisReference,
    add_reference_density,
)
from space_environment.io.gfz import read_gfz_hpo
from space_environment.io.kyoto import read_kyoto_dst_hapi
from space_environment.io.omni import read_omni_hro
from space_environment.io.toleos import read_dns_acc_cdf
from space_environment.physics.magnetic_coordinates import add_quasi_dipole
from space_environment.physics.shock import detect_shocks
from space_environment.physics.space_weather import GfzIndexProvider

from polar_precursor.config import load_config
from polar_precursor.design import build_design
from polar_precursor.design.drivers import CombinedDrivers
from polar_precursor.experiment.manifest import build_manifest, write_manifest

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests/fixtures"
CDF = ROOT / "data/raw/density/CHAMP/CH_OPER_DNS_ACC_2__20031029T000000_20031029T235959_0001.cdf"
GFZ = ROOT / "data/raw/gfz/Kp_ap_Ap_SN_F107_since_1932.txt"
HPO = FIX / "gfz_hp30_20031027_1101_excerpt.txt"
OMNI = FIX / "omni_min_2003_doy301_303_excerpt.asc"
DST_CSV = ROOT / "data/raw/kyoto/hour_dst_final_20031001_20031201.csv"
DST_INFO = ROOT / "data/raw/kyoto/hour_dst_final_info.json"
RC = ROOT / "data/raw/catalog/icmetable2.xlsx"
CONFIG = ROOT / "configs/pilot.toml"
OUT = ROOT / "results" / f"uctan_uca_20031029_{datetime.now():%Y%m%d}"
pd.set_option("display.width", 220)

clock = time.perf_counter()


def lap(label: str) -> None:
    global clock
    now = time.perf_counter()
    print(f"  [{now - clock:6.1f} s] {label}")
    clock = now


config = load_config(CONFIG)
print("yapilandirma:", config.name, config.digest()[:12])

track = read_dns_acc_cdf(CDF)
lap(f"CDF okundu: {len(track)} kayit, {track.attrs['source']}")
track = add_quasi_dipole(track)
lap("QD enlem ve MLT eklendi")

provider = GfzIndexProvider.from_file(GFZ, geomagnetic="measured")
model = QuietNrlmsisReference(provider)
full = add_reference_density(track, model, stride=1)
lap("referans, adim 1 (her 10 s)")
track = add_reference_density(track, model, stride=6)
lap("referans, adim 6 (60 s dugum)")
delta = np.abs(np.log(track[REFERENCE_COLUMN]) - np.log(full[REFERENCE_COLUMN]))
print(
    f"  10 s urunde adim 6 hatasi: en buyuk |delta ln rho| {delta.max():.5f}, "
    f"p99 {np.quantile(delta, 0.99):.5f}, ortanca {np.median(delta):.6f}"
)
log_ratio = np.log(track["density_kg_m3"] / track[REFERENCE_COLUMN])
ok = (track["validity_flag"] == 0) & np.isfinite(log_ratio)
hourly = log_ratio[ok].groupby(track.index[ok].floor("3h")).mean()
print("  ln(rho/rho_ref) 3 saatlik ortalamalar:", " ".join(f"{t:%H}h:{v:+.2f}" for t, v in hourly.items()))

segments = segment_track(track, band_latitude="qd_latitude_deg", mlt="mlt_h", reference=REFERENCE_COLUMN)
counts = segments.groupby(["band", "hemisphere"]).size().to_dict()
lap(f"parcalar: {len(segments)} ({counts}); tam: {int(segments['complete'].sum())}")
samples = build_samples(segments)
lap(f"ornekler: {len(samples)} (kutup gecisi, hedef) cifti; sizinti denetimi gecti")

omni = read_omni_hro(OMNI, cadence="1min")
icmes = read_richardson_cane(RC).between(2003, 2003)
storms = build_storm_catalog(icmes, omni)
storms = storms[np.isfinite(storms["min_symh_nt"])]
lap(f"firtina tablosu (OMNI kesiti 28-30 Eki): {len(storms)} satir")
print(storms[["disturbance_utc", "window_end_utc", "min_symh_nt", "intensity", "cluster"]].to_string())

drivers = CombinedDrivers(
    solar_wind=DriverFeatureBuilder(omni, shocks=detect_shocks(omni)),
    indices=IndexFeatureBuilder(provider, hpo=read_gfz_hpo(HPO), dst=read_kyoto_dst_hapi(DST_CSV, DST_INFO)),
)
design = build_design(
    samples,
    segments,
    storms=storms,
    satellite="CHAMP",
    lead_bin_edges_min=config.samples.lead_bin_edges_min,
    drivers=drivers,
    oracle_drivers=drivers,
    inputs_low=config.samples.inputs_low,
    inputs_polar=config.samples.inputs_polar,
)
lap(f"tasarim matrisi: {design.shape[0]} satir x {design.shape[1]} sutun")
print("  gruplar:", design["group"].value_counts().to_dict(), "| siniflar:", design["intensity"].unique().tolist())
print("  ongoru kutulari:", design["lead_bin"].value_counts().sort_index().to_dict())
families = {
    "low": [c for c in design.columns if c.startswith("low_lag")],
    "polar": [c for c in design.columns if c.startswith("polar_")],
    "mid": ["mid_same"],
    "drv": [c for c in design.columns if c.startswith("drv_") and not c.startswith("drv_oracle_")],
    "oracle": [c for c in design.columns if c.startswith("drv_oracle_")],
    "geo": [c for c in design.columns if c.startswith("geo_")],
}
for name, cols in families.items():
    nan = design[cols].isna().mean().mean() if cols else float("nan")
    print(f"  aile {name:6s}: {len(cols):3d} sutun, NaN orani {100 * nan:5.1f}%")
print(
    f"  hedef: ortalama {design['target_value'].mean():+.3f}, SD {design['target_value'].std():.3f}; "
    f"persistence NaN {100 * design['persistence'].isna().mean():.0f}%; "
    f"solar_wind_available=1 orani {100 * design['drv_solar_wind_available'].mean():.0f}%"
)
print(design[["t0_utc", "lead_time_min", "target_value", "persistence", "low_lag1", "polar_north_lag1", "polar_south_lag1", "mid_same", "drv_em_mv_m", "drv_dst_latest_hour_nt"]].head(6).to_string())

OUT.mkdir(parents=True, exist_ok=True)
design.to_parquet(OUT / "design.parquet", index=False)
segments.to_parquet(OUT / "segments.parquet", index=False)
manifest = build_manifest(
    config,
    root=ROOT,
    data_files=[CDF, GFZ, HPO, OMNI, DST_CSV, DST_INFO, RC],
    extra={
        "reference_model": track.attrs["reference_model"],
        "reference_stride": track.attrs["reference_stride"],
        "magnetic_coordinates": track.attrs.get("magnetic_coordinates"),
        "rows": int(len(design)),
        "columns": list(design.columns),
    },
)
write_manifest(OUT / "manifest.json", manifest)
lap(f"yazildi: {OUT.relative_to(ROOT)} (design.parquet, segments.parquet, manifest.json); commit {manifest['git_commit']}")
