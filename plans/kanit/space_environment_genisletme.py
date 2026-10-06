"""space_environment genisletme kaniti (6 Eki 2026). Proje ortaminda calistirilir:
    .venv/Scripts/python.exe plans/kanit/space_environment_genisletme.py

Yeni okuyucular ve kuruculari gercek veri uzerinde kosturur, ciktiyi dosyaya
yazar. Her sayi bu dosyadan okunabilir; planlardaki iddialarin kaynagi budur.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from space_environment.analysis.catalog import build_storm_catalog, read_richardson_cane
from space_environment.analysis.features import DriverFeatureBuilder
from space_environment.analysis.solar_cycle import cycle_context
from space_environment.io.ace import read_ace_mfi_hapi, read_ace_swe_hapi
from space_environment.io.kyoto import read_kyoto_dst_hapi
from space_environment.io.omni import read_omni_hro
from space_environment.io.set_jb2008 import read_dtcfile, read_solfsmy
from space_environment.io.silso import read_silso_cycle_table, read_silso_monthly
from space_environment.io.weimer_heating import read_heating_deltat
from space_environment.physics.shock import detect_shocks
from space_environment.physics.space_weather import jb2008_solar_inputs

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> None:
    print("space_environment genisletme kaniti,", datetime.now(timezone.utc).isoformat())

    section("ACE yedek: OMNI boslugunda kapsam (29-30 Eki 2003)")
    mfi = read_ace_mfi_hapi(
        RAW / "ace/AC_H0_MFI_20031028_20031031.csv", RAW / "ace/AC_H0_MFI_info.json"
    )
    swe = read_ace_swe_hapi(
        RAW / "ace/AC_H0_SWE_20031028_20031031.csv", RAW / "ace/AC_H0_SWE_info.json"
    )
    for name, frame, column in (("MFI bz", mfi, "bz_gsm_nt"), ("SWE hiz", swe, "flow_speed_km_s")):
        by_day = frame[column].groupby(frame.index.date).apply(lambda s: s.notna().mean())
        gap = frame.loc["2003-10-29 05:50":"2003-10-29 18:42", column]
        print(
            f"{name}: gunluk gecerli oran {by_day.round(3).to_dict()}; OMNI boslugunda {gap.notna().mean():.3f} ({len(gap)} kayit)"
        )

    section("Kyoto Dst (final) Ekim-Kasim 2003")
    dst = read_kyoto_dst_hapi(
        RAW / "kyoto/hour_dst_final_20031001_20031201.csv", RAW / "kyoto/hour_dst_final_info.json"
    )
    print(
        "kayit",
        len(dst),
        "min",
        dst["dst_nt"].min(),
        "@",
        dst["dst_nt"].idxmin(),
        "| 30 Eki 22:00 =",
        dst.at[pd.Timestamp("2003-10-30 22:00", tz="UTC"), "dst_nt"],
    )

    section("SET JB2008 indeksleri")
    solfsmy = read_solfsmy(RAW / "set/SOLFSMY.TXT")
    dtc = read_dtcfile(RAW / "set/DTCFILE.TXT")
    print(
        "SOLFSMY",
        len(solfsmy),
        "gun",
        solfsmy.index[0].date(),
        "-",
        solfsmy.index[-1].date(),
        "| spline/eksik (0 bayragi) sayilari:",
        {n: int((solfsmy["source_flags"].str[i] == "0").sum()) for i, n in enumerate("FSMY")},
    )
    print(
        "JB2008 girdileri 30 Eki 2003 07:04:",
        jb2008_solar_inputs(solfsmy, datetime(2003, 10, 30, 7, 4, tzinfo=timezone.utc)),
    )
    print(
        "DTCFILE",
        len(dtc),
        "saat",
        dtc.index[0],
        "-",
        dtc.index[-1],
        "| min",
        dtc.min(),
        "max",
        dtc.max(),
        "@",
        dtc.idxmax(),
    )
    print("dTc 29 Eki 2003 saatlik:", dtc.loc["2003-10-29"].astype(int).tolist())

    section("Weimer 2023 isitma serisi (Zenodo 7667515)")
    t0 = time.perf_counter()
    heating = read_heating_deltat(RAW / "heating/Heating_DeltaT.h5")
    print(
        f"tam dosya {len(heating)} kayit, okuma {time.perf_counter() - t0:.1f} s, {heating.index[0]} - {heating.index[-1]}, IMF-ok orani {heating['imf_ok'].mean():.4f}"
    )
    halloween = heating.loc["2003-10-28":"2003-10-31"]
    print(
        "28-31 Eki 2003: deltaT max %.0f K @ %s; JH kuzey max %.0f GW, guney max %.0f GW"
        % (
            halloween["delta_t_k"].max(),
            halloween["delta_t_k"].idxmax(),
            halloween["jh_north_gw"].max(),
            halloween["jh_south_gw"].max(),
        )
    )

    section("SILSO gunes cevrimi")
    smoothed = read_silso_monthly(RAW / "silso/SN_ms_tot_V2.0.txt")
    cycles = read_silso_cycle_table(RAW / "silso/TableCyclesMiMa.txt")
    for when in (
        datetime(2001, 3, 1, tzinfo=timezone.utc),
        datetime(2003, 10, 29, tzinfo=timezone.utc),
        datetime(2015, 6, 1, tzinfo=timezone.utc),
    ):
        print(
            when.date(),
            cycle_context(cycles, when),
            "duzgun SN",
            smoothed.at[pd.Timestamp(when.replace(day=1)), "sunspot_number"],
        )

    section("Richardson-Cane katalogu ve firtina tablosu (28-30 Eki 2003, OMNI kesiti)")
    catalogue = read_richardson_cane(RAW / "catalog/icmetable2.xlsx")
    print("toplam", len(catalogue.records), "olay; 2001-2015:", len(catalogue.between(2001, 2015)))
    omni = read_omni_hro(ROOT / "tests/fixtures/omni_min_2003_doy301_303_excerpt.asc")
    events = [
        r
        for r in catalogue.records
        if datetime(2003, 10, 28, tzinfo=timezone.utc)
        <= r.disturbance_utc
        < datetime(2003, 10, 31, tzinfo=timezone.utc)
    ]
    print(build_storm_catalog(events, omni).T.to_string())

    section("Sok bayragi: R&C rahatsizlik zamanlariyla karsilastirma")
    monthly = {
        "200111": RAW / "omni/monthly_1min/omni_min200111.asc",
        "200311": None,
        "200411": RAW / "omni/monthly_1min/omni_min200411.asc",
        "200505": RAW / "omni/monthly_1min/omni_min200505.asc",
        "200508": RAW / "omni/monthly_1min/omni_min200508.asc",
    }
    frames = {"2003-10 (kesit)": omni}
    for key, path in monthly.items():
        if path is not None and path.exists():
            frames[key] = read_omni_hro(path)
    rc_times = sorted(r.disturbance_utc for r in catalogue.records)
    for label, frame in frames.items():
        shocks = detect_shocks(frame)
        rows = []
        for shock in shocks:
            nearest = min(rc_times, key=lambda t: abs(pd.Timestamp(t) - shock.time))
            delta = (shock.time - pd.Timestamp(nearest)) / pd.Timedelta(1, unit="m")
            rows.append(
                (
                    shock.time.strftime("%Y-%m-%d %H:%M"),
                    round(shock.speed_jump_km_s),
                    round(shock.b_ratio, 2),
                    round(shock.density_ratio, 2),
                    pd.Timestamp(nearest).strftime("%m-%d %H:%M"),
                    round(delta),
                )
            )
        print(label, f"{len(shocks)} aday: (zaman, dV, |B| orani, n orani, en yakin R&C, fark dk)")
        for row in rows:
            print("   ", row)
        in_range = [t for t in rc_times if frame.index[0] <= pd.Timestamp(t) <= frame.index[-1]]
        missed = [
            pd.Timestamp(t).strftime("%m-%d %H:%M")
            for t in in_range
            if not any(abs(s.time - pd.Timestamp(t)) <= pd.Timedelta(60, unit="m") for s in shocks)
        ]
        print(
            "    R&C rahatsizliklari bu aralikta:",
            len(in_range),
            "| 60 dk icinde adayi olmayan:",
            missed,
        )

    section("Oznitelik kurucu: hiz ve sizinti sinamasi")
    t0 = time.perf_counter()
    builder = DriverFeatureBuilder(omni, shocks=detect_shocks(omni))
    build_s = time.perf_counter() - t0
    epochs = pd.date_range("2003-10-28 06:00", "2003-10-30 23:00", freq="10min", tz="UTC")
    t0 = time.perf_counter()
    table = builder.table(epochs)
    print(
        f"kurulum {build_s:.2f} s; {len(table)} t0 icin tablo {time.perf_counter() - t0:.2f} s ({len(table) / (time.perf_counter() - t0):.0f} satir/s); {len(builder.feature_names)} oznitelik"
    )
    at = pd.Timestamp("2003-10-28 12:00", tz="UTC")
    corrupted = omni.copy()
    corrupted.loc[corrupted.index > at, list(corrupted.columns)] = 1.0e5
    clean = builder.features_at(at)
    dirty = DriverFeatureBuilder(corrupted, shocks=detect_shocks(omni)).features_at(at)
    leaks = [
        k for k in clean if not (np.isnan(clean[k]) and np.isnan(dirty[k])) and clean[k] != dirty[k]
    ]
    print("t0 sonrasi bozulunca degisen oznitelik:", leaks or "yok")
    print(
        "em_valid_6h boyunca (29 Eki):",
        table.loc["2003-10-29", "em_valid_6h"].iloc[::18].round(2).tolist(),
    )


if __name__ == "__main__":
    main()
