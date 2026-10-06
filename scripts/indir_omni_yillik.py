"""OMNI HRO 1 dakikalık yıllık ASCII dosyalarını indir (NASA SPDF).

    .venv/Scripts/python.exe scripts/indir_omni_yillik.py 2001 2005

Hedef: data/raw/omni/yearly_min/omni_min<YYYY>.asc (yaklaşık 158 MB/yıl, plans/02).
Var olan ve boyutu sunucudakiyle aynı dosya yeniden indirilmez. Her dosyanın
SHA-256'sı ve boyutu plans/kanit/indirme_kaydi_<tarih>.txt dosyasına eklenir.
Ağ erişimi yalnız bu betikte; paket kodu hiç ağa çıkmaz.
"""

from __future__ import annotations

import hashlib
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data/raw/omni/yearly_min"
LOG = ROOT / "plans/kanit" / f"indirme_kaydi_{datetime.now():%Y-%m-%d}.txt"
BASE = "https://spdf.gsfc.nasa.gov/pub/data/omni/high_res_omni/omni_min{year}.asc"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def remote_size(url: str) -> int | None:
    request = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(request, timeout=60) as response:
        length = response.headers.get("Content-Length")
        return int(length) if length else None


def download(url: str, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    partial = target.with_suffix(target.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as response, partial.open("wb") as handle:
        while True:
            chunk = response.read(1 << 20)
            if not chunk:
                break
            handle.write(chunk)
    partial.replace(target)


def log(line: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    print(line, flush=True)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    first, last = int(argv[0]), int(argv[1])
    log(f"# OMNI yıllık 1 dk indirme, {datetime.now(timezone.utc).isoformat(timespec='seconds')}")
    for year in range(first, last + 1):
        url = BASE.format(year=year)
        target = OUT / f"omni_min{year}.asc"
        expected = remote_size(url)
        if target.exists() and expected is not None and target.stat().st_size == expected:
            log(f"{target.name}: zaten var, {expected} bayt, sha256={sha256(target)}")
            continue
        started = time.perf_counter()
        download(url, target)
        size = target.stat().st_size
        status = (
            "ok" if expected is None or size == expected else f"BOYUT FARKLI (beklenen {expected})"
        )
        log(
            f"{target.name}: {size} bayt, {time.perf_counter() - started:.0f} s, {status}, "
            f"sha256={sha256(target)}, kaynak={url}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
