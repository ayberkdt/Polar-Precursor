"""Pilot koşusu: fırtına tablosu → tabakalı 30 küme → veri seti → deney → kapı raporu.

    PYTHONPATH=src .venv/Scripts/python.exe scripts/pilot_kos.py 2001 2005
        [--all] [--no-permutation]

Girdiler (hepsi yerel; indirme betikleri önce koşmuş olmalı):
  data/raw/omni/yearly_min/omni_min<YYYY>.asc        OMNI 1 dk (scripts/indir_omni_yillik.py)
  data/raw/density/CHAMP/**/CH_OPER_DNS_ACC_2__*.cdf  pencere günleri
                                                      (scripts/indir_champ_pencereleri.py)
  data/raw/gfz/Kp_ap_Ap_SN_F107_since_1932.txt, Hp30_ap30_complete_series.txt
  data/raw/kyoto/hour_dst_final_20010101_20060101.csv + hour_dst_final_info.json
  data/raw/catalog/icmetable2.xlsx
Çıktı: results/pilot_<YYYYMMDD>/ (report.md, primary.txt, design.parquet, predictions.parquet,
per_storm.csv, scores.csv, peaks.csv, coverage.csv, storms.csv, manifest.json).

Tabakalı seçim plan 07 önerisi: zayıf 6, orta 10, güçlü 8, şiddetli 4, aşırı 2 (küme
bazında; kümenin sınıfı en şiddetli üyesinin sınıfı), tohum PILOT_SEED. Bir sınıfta
yeterli küme yoksa hepsi alınır ve rapora yazılır. Küme aralığı yapılandırmadaki
ÇD tamponuna (57 sa) eşit alınır ki tampon denetimi katalogla tutarlı olsun.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from polar_precursor.config import load_config
from polar_precursor.design.drivers import CombinedDrivers
from polar_precursor.experiment.dataset import build_dataset
from polar_precursor.experiment.manifest import build_manifest, write_manifest
from polar_precursor.experiment.pipeline import run_experiment
from polar_precursor.experiment.report import gate_report
from space_environment.analysis.catalog import build_storm_catalog, read_richardson_cane
from space_environment.analysis.features import DriverFeatureBuilder
from space_environment.analysis.index_features import IndexFeatureBuilder
from space_environment.analysis.reference_density import QuietNrlmsisReference
from space_environment.io.gfz import read_gfz_hpo
from space_environment.io.kyoto import read_kyoto_dst_hapi
from space_environment.io.omni import read_omni_hro
from space_environment.physics.shock import detect_shocks
from space_environment.physics.space_weather import GfzIndexProvider

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
CONFIG = ROOT / "configs/pilot.toml"
GFZ = RAW / "gfz/Kp_ap_Ap_SN_F107_since_1932.txt"
HPO = RAW / "gfz/Hp30_ap30_complete_series.txt"
DST_CSV = RAW / "kyoto/hour_dst_final_20010101_20060101.csv"
DST_INFO = RAW / "kyoto/hour_dst_final_info.json"
RC = RAW / "catalog/icmetable2.xlsx"
CDF_DIR = RAW / "density/CHAMP"
CACHE = ROOT / "data/derived/design_cache/CHAMP"
PILOT_SEED = 20270207
STRATA = {"weak": 6, "moderate": 10, "strong": 8, "severe": 4, "extreme": 2}
ORDER = ["weak", "moderate", "strong", "severe", "extreme"]

clock = time.perf_counter()


def lap(label: str) -> None:
    global clock
    now = time.perf_counter()
    print(f"  [{now - clock:6.1f} s] {label}", flush=True)
    clock = now


def select_clusters(storms: pd.DataFrame, *, take_all: bool) -> pd.DataFrame:
    """Clusters with a class, their class = most intense member; stratified draw."""
    classified = storms[storms["intensity"].notna()].copy()
    classified["rank"] = classified["intensity"].map({c: i for i, c in enumerate(ORDER)})
    cluster_class = classified.groupby("cluster")["rank"].max().map(lambda r: ORDER[int(r)])
    table = cluster_class.rename("cluster_intensity").reset_index()
    if take_all:
        return table
    rng = np.random.default_rng(PILOT_SEED)
    chosen = []
    for name, count in STRATA.items():
        pool = table[table["cluster_intensity"] == name]
        if len(pool) <= count:
            chosen.append(pool)
        else:
            chosen.append(pool.iloc[rng.choice(len(pool), size=count, replace=False)])
    return pd.concat(chosen).sort_values("cluster").reset_index(drop=True)


def main(argv: list[str]) -> int:
    take_all = "--all" in argv
    with_permutation = "--no-permutation" not in argv
    years = [int(a) for a in argv if not a.startswith("--")]
    if len(years) != 2:
        print(__doc__)
        return 2
    first, last = years
    config = load_config(CONFIG)
    out = ROOT / "results" / f"pilot_{datetime.now():%Y%m%d}"
    out.mkdir(parents=True, exist_ok=True)
    print(f"pilot {first}-{last}, yapılandırma {config.name} {config.digest()[:12]}, çıktı {out}")

    omni = pd.concat(
        [
            read_omni_hro(RAW / f"omni/yearly_min/omni_min{y}.asc", cadence="1min")
            for y in range(first, last + 1)
        ]
    )
    lap(f"OMNI {len(omni)} dakika")
    icmes = read_richardson_cane(RC).between(first, last)
    storms = build_storm_catalog(
        icmes,
        omni,
        cluster_gap_h=config.cv.buffer_h,
        min_symh_coverage=config.storms.min_symh_coverage,
    )
    storms = storms[storms["disturbance_utc"] >= pd.Timestamp(config.storms.period_start, tz="UTC")]
    storms = storms[storms["disturbance_utc"] <= pd.Timestamp(config.storms.period_end, tz="UTC")]
    lap(f"katalog: {len(storms)} ICME, sınıflı {int(storms['intensity'].notna().sum())}")
    clusters = select_clusters(storms, take_all=take_all)
    selected = storms[storms["cluster"].isin(clusters["cluster"])]
    counts = clusters["cluster_intensity"].value_counts().reindex(ORDER).fillna(0)
    class_counts = counts.astype(int).to_dict()
    print(
        f"  seçilen kümeler: {len(clusters)} "
        f"({class_counts}), "
        f"{len(selected)} ICME satırı; tohum {PILOT_SEED}"
    )
    storms.to_csv(out / "storms.csv")
    clusters.to_csv(out / "clusters.csv", index=False)

    provider = GfzIndexProvider.from_file(GFZ, geomagnetic="measured")
    drivers = CombinedDrivers(
        solar_wind=DriverFeatureBuilder(omni, shocks=detect_shocks(omni)),
        indices=IndexFeatureBuilder(
            provider, hpo=read_gfz_hpo(HPO), dst=read_kyoto_dst_hapi(DST_CSV, DST_INFO)
        ),
    )
    lap("sürücü kurucular hazır")
    reference = QuietNrlmsisReference(provider)
    design, coverage = build_dataset(
        storms,
        cdf_dir=CDF_DIR,
        satellite="CHAMP",
        reference_model=reference,
        drivers=drivers,
        oracle_drivers=drivers,
        config=config,
        storm_rows=list(selected.index),
        cache_dir=CACHE,
    )
    coverage.to_csv(out / "coverage.csv", index=False)
    n_groups = design["group"].nunique() if not design.empty else 0
    lap(
        f"veri seti: {len(design)} satır, {n_groups} küme; "
        f"gün bulunan/gereken {int(coverage['days_found'].sum())}"
        f"/{int(coverage['days_needed'].sum())}"
    )
    if design.empty or design["group"].nunique() < config.cv.outer_folds:
        print("yetersiz veri: küme sayısı dış kat sayısından az; pilot koşulmadı")
        return 1
    design.to_parquet(out / "design.parquet", index=False)

    result = run_experiment(design, config, with_permutation=with_permutation)
    lap("deney (ÇD + bootstrap" + (" + permütasyon)" if with_permutation else ")"))
    result.cv.predictions.assign(fold=result.cv.fold).to_parquet(
        out / "predictions.parquet", index=False
    )
    result.per_storm.to_csv(out / "per_storm.csv")
    result.scores.to_csv(out / "scores.csv", index=False)
    result.peaks.to_csv(out / "peaks.csv")
    (out / "primary.txt").write_text(result.primary_line() + "\n", encoding="utf-8")
    report = gate_report(result, design, title=f"Pilot gate report ({first}-{last}, CHAMP)")
    (out / "report.md").write_text(report, encoding="utf-8")
    data_files = [GFZ, HPO, DST_CSV, DST_INFO, RC] + [
        RAW / f"omni/yearly_min/omni_min{y}.asc" for y in range(first, last + 1)
    ]
    manifest = build_manifest(
        config,
        root=ROOT,
        data_files=data_files,
        extra={
            "pilot_seed": PILOT_SEED,
            "strata": STRATA,
            "take_all": take_all,
            "clusters": clusters["cluster"].tolist(),
            "rows": int(len(design)),
            "reference_model": reference.label,
        },
    )
    write_manifest(out / "manifest.json", manifest)
    print()
    print(result.primary_line())
    print(f"rapor: {out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
