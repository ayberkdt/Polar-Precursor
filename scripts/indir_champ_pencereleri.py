"""Fırtına pencerelerini kapsayan günlük CHAMP yoğunluk dosyalarını indir (ESA Swarm DISS).

    PYTHONPATH=src .venv/Scripts/python.exe scripts/indir_champ_pencereleri.py 2001 2005
        [--satellite CHAMP|GRACE-A|GRACE-B] [--dry-run]

Adımlar: data/raw/omni/yearly_min/omni_min<YYYY>.asc dosyalarından (önce
scripts/indir_omni_yillik.py) ve Richardson-Cane listesinden fırtına tablosu
kurulur (space_environment.analysis.catalog.build_storm_catalog); her satır için
[rahatsızlık − 6 sa, pencere sonu] aralığındaki günler listelenir; eksik olan
günlük dosyalar ESA'dan girişsiz indirilir (plans/01 satır 146'da doğrulanan adres
biçimi). Hedef: data/raw/density/<uydu>/<YYYY>/<önek><gün>T000000_<gün>T235959_0001.cdf.
GRACE-A adı ve yolu 6 Eki 2026 akşam ESA'da doğrulandı (Sat_1/<YYYY>/ alt dizini zorunlu).
Fırtına tablosu data/derived/firtina_tablosu_<ilk>_<son>.csv olarak, her indirmenin
SHA-256'sı plans/kanit/indirme_kaydi_<tarih>.txt dosyasına yazılır. HTTP 404 = o gün
için ürün yok (CHAMP veri boşluğu); kayda "yok" yazılır, hata sayılmaz.
"""

from __future__ import annotations

import hashlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from space_environment.analysis.catalog import build_storm_catalog, read_richardson_cane
from space_environment.io.omni import read_omni_hro

ROOT = Path(__file__).resolve().parents[1]
OMNI_DIR = ROOT / "data/raw/omni/yearly_min"
RC = ROOT / "data/raw/catalog/icmetable2.xlsx"
DENSITY = ROOT / "data/raw/density"
SATELLITES: dict[str, tuple[str, str]] = {  # uydu -> (dosya öneki, uzak dizin; {year} yıl)
    "CHAMP": ("CH_OPER_DNS_ACC_2__", "swarm/Multimission/CHAMP/DNS/"),
    "GRACE-A": ("GR_OPER_DNS1ACC_2__", "swarm/Multimission/GRACE/DNS/Sat_1/{year}/"),
    "GRACE-B": ("GR_OPER_DNS2ACC_2__", "swarm/Multimission/GRACE/DNS/Sat_2/{year}/"),
}
DERIVED = ROOT / "data/derived"
LOG = ROOT / "plans/kanit" / f"indirme_kaydi_{datetime.now():%Y-%m-%d}.txt"
ESA = "https://swarm-diss.eo.esa.int/?do=download&file="
PRE_HOURS = 6.0
EXPECTED_BYTES = 563_686  # 29 Eki 2003 dosyası (plans/01); diğer günler farklı olabilir


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def log(line: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def file_name(satellite: str, day: pd.Timestamp) -> str:
    stamp = day.strftime("%Y%m%d")
    return f"{SATELLITES[satellite][0]}{stamp}T000000_{stamp}T235959_0001.cdf"


def existing(satellite: str, day: pd.Timestamp) -> Path | None:
    stamp = day.strftime("%Y%m%d")
    prefix = SATELLITES[satellite][0]
    out = DENSITY / satellite
    matches = sorted(out.rglob(f"{prefix}{stamp}T000000_{stamp}T235959_*.cdf"))
    return matches[-1] if matches else None


def download_day(satellite: str, day: pd.Timestamp) -> tuple[str, Path | None]:
    name = file_name(satellite, day)
    remote_dir = SATELLITES[satellite][1].format(year=day.year)
    url = ESA + urllib.parse.quote(remote_dir + name, safe="")
    target = DENSITY / satellite / f"{day.year}" / name
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(".part")
    try:
        with urllib.request.urlopen(url, timeout=180) as response, partial.open("wb") as handle:
            while True:
                chunk = response.read(1 << 20)
                if not chunk:
                    break
                handle.write(chunk)
    except urllib.error.HTTPError as error:
        partial.unlink(missing_ok=True)
        return f"HTTP {error.code}", None
    partial.replace(target)
    return "ok", target


def main(argv: list[str]) -> int:
    dry_run = "--dry-run" in argv
    satellite = "CHAMP"
    if "--satellite" in argv:
        satellite = argv[argv.index("--satellite") + 1]
        argv = [a for a in argv if a != satellite]
    if satellite not in SATELLITES:
        print(f"bilinmeyen uydu {satellite!r}; {list(SATELLITES)}")
        return 2
    years = [int(a) for a in argv if not a.startswith("--")]
    if len(years) != 2:
        print(__doc__)
        return 2
    first, last = years
    missing_omni = [
        y for y in range(first, last + 1) if not (OMNI_DIR / f"omni_min{y}.asc").exists()
    ]
    if missing_omni:
        print(f"OMNI yıllık dosyaları eksik: {missing_omni}; önce scripts/indir_omni_yillik.py")
        return 1
    started = time.perf_counter()
    omni = pd.concat(
        [
            read_omni_hro(OMNI_DIR / f"omni_min{y}.asc", cadence="1min")
            for y in range(first, last + 1)
        ]
    )
    print(f"OMNI {first}-{last}: {len(omni)} dakika, {time.perf_counter() - started:.0f} s")
    icmes = read_richardson_cane(RC).between(first, last)
    storms = build_storm_catalog(icmes, omni, cluster_gap_h=57.0)  # = ÇD tamponu (configs)
    DERIVED.mkdir(parents=True, exist_ok=True)
    table_path = DERIVED / f"firtina_tablosu_{first}_{last}.csv"
    storms.to_csv(table_path, index=True)
    classified = storms[storms["intensity"].notna()]
    print(
        f"fırtına tablosu: {len(storms)} ICME, sınıflı {len(classified)}; "
        f"sınıflar {classified['intensity'].value_counts().to_dict()}; yazıldı {table_path.name}"
    )

    days: set[pd.Timestamp] = set()
    for _, storm in storms.iterrows():
        start = pd.Timestamp(storm["disturbance_utc"]) - pd.Timedelta(PRE_HOURS, unit="h")
        end = pd.Timestamp(storm["window_end_utc"])
        days.update(pd.date_range(start.floor("D"), end.floor("D"), freq="D"))
    ordered = sorted(days)
    have = [d for d in ordered if existing(satellite, d) is not None]
    todo = [d for d in ordered if existing(satellite, d) is None]
    print(
        f"{satellite} pencere günleri: {len(ordered)} "
        f"({ordered[0]:%Y-%m-%d} .. {ordered[-1]:%Y-%m-%d}); "
        f"diskte {len(have)}, indirilecek {len(todo)} (~{len(todo) * EXPECTED_BYTES / 1e6:.0f} MB)"
    )
    if dry_run:
        return 0
    log(
        f"# {satellite} pencere günleri {first}-{last}, "
        f"{datetime.now(timezone.utc).isoformat(timespec='seconds')}; {len(todo)} gün"
    )
    ok = absent = failed = 0
    for i, day in enumerate(todo, start=1):
        status, path = download_day(satellite, day)
        if path is not None:
            ok += 1
            log(f"{path.name}: {path.stat().st_size} bayt, sha256={sha256(path)}")
        elif status == "HTTP 404":
            absent += 1
            log(f"{file_name(satellite, day)}: yok (HTTP 404)")
        else:
            failed += 1
            log(f"{file_name(satellite, day)}: HATA {status}")
        if i % 25 == 0:
            print(f"  {i}/{len(todo)} ... ok {ok}, yok {absent}, hata {failed}", flush=True)
    elapsed = time.perf_counter() - started
    log(f"# bitti: indirildi {ok}, yok {absent}, hata {failed}, {elapsed:.0f} s")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
