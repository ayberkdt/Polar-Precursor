"""JB2008 girdi kuralinin pyatmos ile capraz kontrolu (6 Eki 2026).
    .venv/Scripts/python.exe plans/kanit/jb2008_pyatmos_capraz_kontrol.py

pyatmos 1.2.7 (bagimsiz uygulama) ayni SET dosyalarini okuyor (SOLFSMY sutun 2-11,
DTCFILE sutun 3-27). Sorular: (1) gecikmeli F10/S10/M10/Y10 degerlerimiz ayni mi?
(2) DTCFILE'daki 24 degeri pyatmos nasil yorumluyor (saat eslemesi)?
(3) pyatmos bir JB2008 adaptoru icin kullanilabilir mi (ag erisimi)?
Not: pyatmos paketi ice aktarilirken IERS dosyalarini indirmeye calisiyor; bu betik
bu yuzden ag gerektirir. Kanit icin tek sefer kosuldu.
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SOLFSMY = ROOT / "data/raw/set/SOLFSMY.TXT"
DTCFILE = ROOT / "data/raw/set/DTCFILE.TXT"

import pyatmos  # noqa: E402  (ice aktarma sirasinda IERS indirmesi yapar)
from pyatmos.jb2008 import spaceweather as sw  # noqa: E402
from pyatmos.jb2008.JB2008_subfunc import JB2008  # noqa: E402
from pyatmos.utils import Const  # noqa: E402

from space_environment.io.set_jb2008 import read_dtcfile, read_solfsmy  # noqa: E402
from space_environment.physics.space_weather import dtc_at, jb2008_solar_inputs  # noqa: E402

print("pyatmos dosyasi:", Path(pyatmos.__file__).parent)
data = sw.read_sw_jb2008((str(SOLFSMY), str(DTCFILE)))
table = read_solfsmy(SOLFSMY)
dtc = read_dtcfile(DTCFILE)

print("\n(1) Gecikmeli gunes indeksleri, uc epok:")
mismatch = 0
for when in (
    datetime(2003, 10, 30, 7, 4, tzinfo=timezone.utc),
    datetime(2005, 5, 15, 2, 38, tzinfo=timezone.utc),
    datetime(2015, 6, 1, 12, 0, tzinfo=timezone.utc),
):
    mjd = 51544.0 + (when - datetime(2000, 1, 1, tzinfo=timezone.utc)).total_seconds() / 86400.0
    theirs = [float(v) for v in sw.get_sw(data, mjd)]
    ours = jb2008_solar_inputs(table, when)
    mine = [ours.f10, ours.f10b, ours.s10, ours.s10b, ours.m10, ours.m10b, ours.y10, ours.y10b]
    same = np.allclose(theirs[:8], mine)
    mismatch += 0 if same else 1
    print(f"  {when.isoformat()}  pyatmos {theirs[:8]}  bizim {mine}  ayni: {same}")
print("  eslesmeyen epok sayisi:", mismatch)

print("\n(2) DTCFILE saat eslemesi:")
x = np.asarray(Const.x)
print(
    "  pyatmos Const.x ilk degerler (gun kesri):",
    x[:3],
    "... adim",
    x[1] - x[0],
    "=> k. deger k:30 UT'de gecerli, aralar dogrusal",
)
when = datetime(2003, 10, 30, 7, 4, tzinfo=timezone.utc)
mjd = 51544.0 + (when - datetime(2000, 1, 1, tzinfo=timezone.utc)).total_seconds() / 86400.0
theirs_dtc = float(sw.get_sw(data, mjd)[8])
print(
    f"  07:04 UT: pyatmos (icdegerlenmis) {theirs_dtc:.2f}; bizim saat degeri (07:00-08:00) {dtc_at(dtc, when):.1f}; "
    f"bizim icdegerlenmis {dtc_at(dtc, when, interpolate=True):.2f}"
)
print("  Kernel imzasi:", inspect.signature(JB2008))
doc = inspect.getsource(JB2008)
i = doc.find("DSTDTC")
print("  Kernel belgesinde DSTDTC:", " ".join(doc[i : i + 160].split()))

print("\n(3) Adaptor icin uygunluk:")
head = Path(pyatmos.__file__).read_text(encoding="utf-8")
print("  pyatmos/__init__.py IERS verisini ice aktarma sirasinda yukluyor:", "data_prepare" in head)
print(
    "  Sonuc: kernel (JB2008_subfunc.JB2008, numba) dogrudan cagrilabilir; ama paket ice aktarmasi ag istiyor."
)
print(
    "  Sidera ilkesi (ag yok) icin kernel ayri paketlenmeli ya da pyatmos cevrimdisi kipte dogrulanmali."
)
