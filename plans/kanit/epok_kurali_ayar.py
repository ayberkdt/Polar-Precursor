"""Bz guneye donus kuralinin yayinlanmis baslangic zamanlariyla karsilastirilmasi. 6 Eki 2026.
Tohum: Richardson-Cane (a) sutunu. Hedef: Zesta ve Oliveira 2019 Tablo 2 (+ 24 Agu 2005 bildiri degeri 09:09).
Veri: OMNI HRO 1 dk aylik dosyalar (data/raw/omni/monthly_1min)."""

import itertools

import pandas as pd

from space_environment.io.omni import read_omni_hro
from space_environment.physics.storm_onset import find_southward_turning

CASES = [  # (aylik dosya, tohum, yayinlanmis baslangic)
    ("200111", "2001-11-06 01:52", "2001-11-06 02:05"),
    ("200311", "2003-11-20 08:03", "2003-11-20 11:24"),
    ("200411", "2004-11-07 18:27", "2004-11-07 20:14"),
    ("200411", "2004-11-09 18:25", "2004-11-09 19:25"),
    ("200505", "2005-05-15 02:38", "2005-05-15 06:01"),
    ("200508", "2005-08-24 06:13", "2005-08-24 09:09"),
]
frames = {
    ym: read_omni_hro(f"data/raw/omni/monthly_1min/omni_min{ym}.asc")
    for ym in {c[0] for c in CASES}
}


def run(**kw):
    out = []
    for ym, seed, pub in CASES:
        bz = frames[ym]["bz_gsm_nt"]
        seed_t, pub_t = pd.Timestamp(seed, tz="UTC"), pd.Timestamp(pub, tz="UTC")
        r = find_southward_turning(bz, seed_t, **kw)
        diff = (r.onset - pub_t).total_seconds() / 60 if r.onset is not None else None
        out.append((seed, pub, r, diff))
    return out


print(
    "== Varsayilan parametreler: sustain 30 dk, negatif orani 0.8, ortalama <= -3 nT, arama -1..+12 sa =="
)
print(
    "%-17s %-17s %-17s %-18s %7s %6s %8s"
    % ("tohum (R&C)", "yayinlanan", "kural", "durum", "fark dk", "kapsam", "ort Bz")
)
for seed, pub, r, diff in run():
    print(
        "%-17s %-17s %-17s %-18s %7s %6.2f %8s"
        % (
            seed,
            pub,
            r.onset.strftime("%Y-%m-%d %H:%M") if r.onset is not None else "-",
            r.status,
            "%+.0f" % diff if diff is not None else "-",
            r.window_valid_fraction,
            "%.1f" % r.sustained_mean_bz_nt if r.sustained_mean_bz_nt is not None else "-",
        )
    )

print("\n== Tohum cevresinde Bz (5 dk ornek), her olay icin tohum-30dk .. yayinlanan+30dk ==")
for ym, seed, pub in CASES:
    bz = frames[ym]["bz_gsm_nt"]
    s = bz.loc[
        pd.Timestamp(seed, tz="UTC") - pd.Timedelta(30, unit="m") : pd.Timestamp(pub, tz="UTC")
        + pd.Timedelta(30, unit="m")
    ]
    print(seed, "->", pub, "| gecerli %.2f" % s.notna().mean())
    print(
        "   "
        + " ".join(
            "%s:%s" % (t.strftime("%H:%M"), "nan" if pd.isna(v) else "%.0f" % v)
            for t, v in s.iloc[::10].items()
        )
    )

print(
    "\n== Parametre taramasi: yayinlanana |fark| <= 15 dk olan olay sayisi (6 olay) ve ortanca |fark| =="
)
grid = list(itertools.product([15.0, 30.0, 60.0], [0.7, 0.8, 0.9], [2.0, 3.0, 5.0, 8.0]))
rows = []
for sus, frac, mean in grid:
    res = run(sustain_min=sus, negative_fraction=frac, mean_below_nt=mean)
    diffs = [abs(d) for *_, d in res if d is not None]
    hits = sum(1 for d in diffs if d <= 15)
    found = len(diffs)
    rows.append(
        (hits, -sorted(diffs)[len(diffs) // 2] if diffs else 0, sus, frac, mean, found, diffs)
    )
rows.sort(reverse=True)
for hits, negmed, sus, frac, mean, found, diffs in rows[:12]:
    print(
        "sustain %4.0f  oran %.1f  ort<=-%.0f : bulunan %d/6, <=15dk %d, |fark| dk = %s"
        % (sus, frac, mean, found, hits, [round(d) for d in diffs])
    )

print(
    "\n== Kural 2: esik gecisinden geriye yuruyus (find_main_phase_onset), varsayilan parametreler =="
)
from space_environment.physics.storm_onset import find_main_phase_onset

print(
    "%-17s %-17s %-17s %-18s %7s %6s %8s"
    % ("tohum (R&C)", "yayinlanan", "kural", "durum", "fark dk", "kapsam", "ort Bz")
)
for ym, seed, pub in CASES:
    bz = frames[ym]["bz_gsm_nt"]
    seed_t, pub_t = pd.Timestamp(seed, tz="UTC"), pd.Timestamp(pub, tz="UTC")
    r = find_main_phase_onset(bz, seed_t)
    diff = (r.onset - pub_t).total_seconds() / 60 if r.onset is not None else None
    print(
        "%-17s %-17s %-17s %-18s %7s %6.2f %8s"
        % (
            seed,
            pub,
            r.onset.strftime("%Y-%m-%d %H:%M") if r.onset is not None else "-",
            r.status,
            "%+.0f" % diff if diff is not None else "-",
            r.window_valid_fraction,
            "%.1f" % r.sustained_mean_bz_nt if r.sustained_mean_bz_nt is not None else "-",
        )
    )
print("\n== Kural 2 duyarlilik: goreli derinlik x kopru; fark dk (6 olay; None = bulunamadi) ==")
for rel in (0.0, 0.3, 0.5, 0.7, 1.0):
    for gap in (5.0, 10.0, 30.0):
        diffs = []
        for ym, seed, pub in CASES:
            r = find_main_phase_onset(
                frames[ym]["bz_gsm_nt"],
                pd.Timestamp(seed, tz="UTC"),
                relative_depth=rel,
                max_gap_min=gap,
            )
            diffs.append(
                None
                if r.onset is None
                else round((r.onset - pd.Timestamp(pub, tz="UTC")).total_seconds() / 60)
            )
        print("goreli %.1f kopru %2.0f dk:" % (rel, gap), diffs)
