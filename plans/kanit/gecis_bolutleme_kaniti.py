"""Gecis bolutleme ve QD koordinat kaniti, gercek CHAMP gunu 29 Eki 2003 (6 Eki 2026).
    .venv/Scripts/python.exe plans/kanit/gecis_bolutleme_kaniti.py

Sorular: (1) 10 s izde bant parcalari plan 04 beklentilerini tutuyor mu?
(2) QD enlemle bolutleme cografi enlemden ne kadar farkli? (3) apexpy hizi?
(4) Ornek kurucu kac (kutup gecisi, hedef) cifti uretiyor; sizinti sifir mi?
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pandas as pd

from space_environment.analysis.passes import build_samples, segment_track
from space_environment.io.toleos import read_dns_acc_cdf
from space_environment.physics.magnetic_coordinates import add_quasi_dipole

ROOT = Path(__file__).resolve().parents[2]
CDF = ROOT / "data/raw/density/CHAMP/CH_OPER_DNS_ACC_2__20031029T000000_20031029T235959_0001.cdf"
pd.set_option("display.width", 250)

track = read_dns_acc_cdf(CDF)
print("iz:", track.attrs["source"], "| kayit", len(track))

t0 = time.perf_counter()
track = add_quasi_dipole(track)
dt = time.perf_counter() - t0
print(
    f"apexpy QD + MLT: {len(track)} nokta {dt:.2f} s ({len(track) / dt:.0f} nokta/s); {track.attrs['magnetic_coordinates']}"
)
delta = (track["qd_latitude_deg"] - track["latitude_deg"]).abs()
print(
    f"|QD - cografi enlem|: ortanca {delta.median():.1f} derece, en buyuk {delta.max():.1f} derece"
)

for label, column in (("cografi", "latitude_deg"), ("QD", "qd_latitude_deg")):
    t0 = time.perf_counter()
    seg = segment_track(track, band_latitude=column, mlt="mlt_h")
    dt = time.perf_counter() - t0
    counts = seg.groupby(["band", "hemisphere"]).size().to_dict()
    low = seg[seg["band"] == "low"].sort_values("mid_utc")
    gaps = low["mid_utc"].diff().dropna().dt.total_seconds() / 60.0
    polar = seg[seg["band"] == "polar"]
    print(f"\n[{label} enlem] {len(seg)} parca, {dt:.2f} s; sayimlar {counts}")
    print(
        f"   alcak enlem orta zaman araliklari: {gaps.min():.1f}-{gaps.max():.1f} dk; "
        f"kutup parcasi suresi ortanca {(polar['end_utc'] - polar['start_utc']).dt.total_seconds().median() / 60:.1f} dk; "
        f"ulasilan en yuksek |enlem| ortanca {polar['max_abs_band_latitude_deg'].median():.1f}"
    )
    if column == "qd_latitude_deg":
        print(
            f"   kutup gecislerinde cusp (10-14 MLT) orani: ortanca {polar['cusp_fraction'].median():.2f}, "
            f"en buyuk {polar['cusp_fraction'].max():.2f}"
        )
    samples = build_samples(seg)
    print(
        f"   ornekler: {len(samples)} (kutup gecisi, hedef) cifti; ongoru suresi {samples['lead_time_min'].min():.0f}-"
        f"{samples['lead_time_min'].max():.0f} dk; sizinti denetimi gecti (build_samples icinde)"
    )

# Firtina gunu onizlemesi: kutup ve alcak enlem log-yogunluk zaman serileri (QD bantlari)
seg = segment_track(track, band_latitude="qd_latitude_deg", mlt="mlt_h")
print(
    "\nQD bantlarinda saatlik log-yogunluk ortalamalari (29 Eki 2003, firtina ana evresi 06 UT sonrasi):"
)
for band, hemi in (("polar", "north"), ("polar", "south"), ("low", "both")):
    part = seg[(seg["band"] == band) & (seg["hemisphere"] == hemi)].set_index("mid_utc")[
        "target_mean"
    ]
    hourly = part.groupby(part.index.floor("3h")).mean()
    print(
        f"  {band:5s} {hemi:5s}: "
        + " ".join(f"{t.strftime('%H')}h:{v:+.2f}" for t, v in hourly.items())
    )
