"""Kapsam raporu: her fırtına kümesi için uydu başına gün/kayıt/parça/örnek sayıları.

    PYTHONPATH=src .venv/Scripts/python.exe scripts/kapsam_raporu.py [--block 2006-2010]

Bellek: OMNI blok çerçevesi ≈1 GB; makinede boş bellek azsa blokları ayrı süreçlerde
koşmak için ``--block`` verilir (her blok coverage_<uydu>_<blok>.csv yazar; özet, klasördeki
bütün blok dosyalarından her seferinde yeniden kurulur).

Ön kayıt taslağı bölüm D'nin istediği tablo: ana analizden önce, hangi fırtına
kümesinin hangi uyduda yeterli veriye sahip olduğu. Katalog ve veri seti kurucu
üç beş yıllık blokta koşar (2001-2005, 2006-2010, 2011-2015; indirme de aynı
bloklarla yapıldı), sürücüler eklenmez (yalnız iz, QD, referans, parçalar,
örnekler; sürücüsüz tasarım önbelleği ayrı anahtarla saklanır). Çıktı:
results/kapsam_<YYYYMMDD>/ içinde coverage_<uydu>.csv, storms_<blok>.csv ve
ozet.md; ozet.md kanıt olarak plans/kanit altına kopyalanır.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

from polar_precursor.config import load_config
from polar_precursor.design.matrix import cluster_classes
from polar_precursor.experiment.dataset import build_dataset
from space_environment.analysis.catalog import build_storm_catalog, read_richardson_cane
from space_environment.analysis.reference_density import QuietNrlmsisReference
from space_environment.io.omni import read_omni_hro
from space_environment.physics.space_weather import GfzIndexProvider

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw"
GFZ = RAW / "gfz/Kp_ap_Ap_SN_F107_since_1932.txt"
RC = RAW / "catalog/icmetable2.xlsx"
CACHE = ROOT / "data/derived/design_cache"
BLOCKS = ((2001, 2005), (2006, 2010), (2011, 2015))
SATELLITES = {"CHAMP": (2001, 2010), "GRACE-A": (2002, 2015)}
ORDER = ["weak", "moderate", "strong", "severe", "extreme"]


def main(argv: list[str]) -> int:
    only = None
    if "--block" in argv:
        first_s, last_s = argv[argv.index("--block") + 1].split("-")
        only = (int(first_s), int(last_s))
    config = load_config(ROOT / "configs/pilot.toml")
    out = ROOT / "results" / f"kapsam_{datetime.now():%Y%m%d}"
    out.mkdir(parents=True, exist_ok=True)
    provider = GfzIndexProvider.from_file(GFZ, geomagnetic="measured")
    reference = QuietNrlmsisReference(provider)
    lines = [f"# Kapsam raporu, {datetime.now():%Y-%m-%d %H:%M}", ""]
    started = time.perf_counter()
    for first, last in BLOCKS:
        if only is not None and (first, last) != only:
            continue
        omni = pd.concat(
            [
                read_omni_hro(RAW / f"omni/yearly_min/omni_min{y}.asc", cadence="1min")
                for y in range(first, last + 1)
            ]
        )
        icmes = read_richardson_cane(RC).between(first, last)
        storms = build_storm_catalog(
            icmes,
            omni,
            cluster_gap_h=config.cv.buffer_h,
            min_symh_coverage=config.storms.min_symh_coverage,
        )
        storms.to_csv(out / f"storms_{first}_{last}.csv")
        classes = cluster_classes(storms)
        counts = pd.Series(classes).value_counts().reindex(ORDER).fillna(0).astype(int)
        lines.append(
            f"## Blok {first}-{last}: {len(storms)} ICME, {len(classes)} küme "
            f"({counts.to_dict()}); OMNI {len(omni)} dk"
        )
        print(lines[-1], flush=True)
        del omni
        for satellite, (sat_first, sat_last) in SATELLITES.items():
            if last < sat_first or first > sat_last:
                continue
            block_started = time.perf_counter()
            _, coverage = build_dataset(
                storms,
                cdf_dir=RAW / "density" / satellite,
                satellite=satellite,
                reference_model=reference,
                drivers=None,
                config=config,
                cache_dir=CACHE / satellite,
            )
            coverage["satellite"] = satellite
            coverage["block"] = f"{first}-{last}"
            coverage["cluster_intensity"] = coverage["group"].map(classes)
            coverage.to_csv(out / f"coverage_{satellite}_{first}_{last}.csv", index=False)
            usable = coverage[coverage["design_rows"] > 0]
            lines.append(
                f"- {satellite}: {len(coverage)} ICME satırı, örnekli {len(usable)}, "
                f"gün bulunan/gereken {int(coverage['days_found'].sum())}/"
                f"{int(coverage['days_needed'].sum())}, toplam tasarım satırı "
                f"{int(coverage['design_rows'].sum())}, "
                f"{time.perf_counter() - block_started:.0f} s"
            )
            print(lines[-1], flush=True)
    lines.append("")
    lines.append("## Küme başına özet (uydu × sınıf): örnekli küme sayısı / toplam")
    lines.append("")
    lines.append("| uydu | sınıf | kümeler | örnekli | gün oranı ortanca | satır toplam |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for satellite in SATELLITES:
        parts = [pd.read_csv(path) for path in sorted(out.glob(f"coverage_{satellite}_*_*.csv"))]
        if not parts:
            continue
        table = pd.concat(parts, ignore_index=True)
        table.to_csv(out / f"coverage_{satellite}.csv", index=False)
        per_cluster = table.groupby(["block", "group"]).agg(
            cluster_intensity=("cluster_intensity", "first"),
            days_found=("days_found", "sum"),
            days_needed=("days_needed", "sum"),
            design_rows=("design_rows", "sum"),
        )
        per_cluster["day_fraction"] = per_cluster["days_found"] / per_cluster["days_needed"]
        for name in ORDER:
            part = per_cluster[per_cluster["cluster_intensity"] == name]
            if part.empty:
                continue
            lines.append(
                f"| {satellite} | {name} | {len(part)} | {int((part['design_rows'] > 0).sum())} | "
                f"{part['day_fraction'].median():.2f} | {int(part['design_rows'].sum())} |"
            )
        lines.append(
            f"| {satellite} | **hepsi** | {len(per_cluster)} | "
            f"{int((per_cluster['design_rows'] > 0).sum())} | "
            f"{per_cluster['day_fraction'].median():.2f} | "
            f"{int(per_cluster['design_rows'].sum())} |"
        )
    lines.append("")
    lines.append(
        f"Toplam süre {time.perf_counter() - started:.0f} s; sürücüsüz tasarım, önbellek {CACHE}"
    )
    text = "\n".join(lines) + "\n"
    (out / "ozet.md").write_text(text, encoding="utf-8")
    (ROOT / "plans/kanit" / f"kapsam_raporu_{datetime.now():%Y-%m-%d}.md").write_text(
        text, encoding="utf-8"
    )
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
