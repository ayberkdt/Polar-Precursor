"""Gercek CHAMP izinde (ESA V2, VirES HAPI) kontrol. 5 Eki 2026.
1) ESA dizin listesinden CHAMP 2005 eksik gunleri
2) ap=4 ile anahtar kapali MSIS 2.1 ozdes mi (firtina ve gunes minimumu)
3) 29 Eki 2003 firtinasinda kutup / alcak enlem log-oran onizlemesi (COGRAFI enlem, QD degil)
"""

import io
import json
import sys
import urllib.request

import numpy as np
import pandas as pd
import pymsis


def get(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return r.read().decode()


# --- 1) CHAMP 2005 bosluklari
lst = json.load(open(sys.argv[1], encoding="utf-8"))["results"]
days = sorted(
    pd.to_datetime([f["name"].split("__")[1][:8] for f in lst if f["name"].endswith(".cdf")])
)
print("ESA CHAMP dosya sayisi:", len(days), "| ilk", days[0].date(), "son", days[-1].date())
s = pd.Series(1, index=pd.DatetimeIndex(days))
full = pd.date_range("2001-01-01", "2010-09-04")
miss = full.difference(s.index)
grp = (pd.Series(miss).diff().dt.days != 1).cumsum()
print("2001-2010 eksik gun:", len(miss))
for _, g in pd.Series(miss).groupby(grp.values):
    if len(g) >= 3:
        print("   bosluk %s .. %s (%d gun)" % (g.iloc[0].date(), g.iloc[-1].date(), len(g)))


# --- veri
def champ(start, stop):
    u = (
        "https://vires.services/hapi/data?dataset=CH_OPER_DNS_ACC_2_&start=%sT00:00:00Z&stop=%sT00:00:00Z"
        % (start, stop)
    )
    df = pd.read_csv(
        io.StringIO(get(u)),
        header=None,
        names=["t", "lat", "lon", "h", "lst", "rho", "rho_orb", "flag", "flag_orb"],
    )
    df["t"] = pd.to_datetime(df["t"].str.replace("Z", ""))
    return df


def gfz(index, start, stop):
    j = json.loads(
        get(
            "https://kp.gfz.de/app/json/?start=%sT00:00:00Z&end=%sT23:59:59Z&index=%s"
            % (start, stop, index)
        )
    )
    return pd.Series(j[index], index=pd.to_datetime([x.replace("Z", "") for x in j["datetime"]]))


def ref(df, fobs, **kw):
    day = df["t"].dt.floor("D")
    f_prev = (day - pd.Timedelta(days=1)).map(fobs).to_numpy(float)
    f81 = fobs.rolling(81, center=True).mean()
    fa = day.map(f81).to_numpy(float)
    n = len(df)
    out = pymsis.calculate(
        df["t"].to_numpy("datetime64[s]"),
        df["lon"].to_numpy(),
        df["lat"].to_numpy(),
        df["h"].to_numpy() / 1000.0,
        f_prev,
        fa,
        np.full((n, 7), 4.0),
        version=2.1,
        **kw,
    )
    return out[:, pymsis.Variable.MASS_DENSITY], f_prev, fa


for name, a, b, fa_, fb_ in [
    ("firtina 2003-10-27..11-01", "2003-10-27", "2003-11-01", "2003-08-01", "2003-12-31"),
    ("gunes minimumu 2008-07-01", "2008-07-01", "2008-07-02", "2008-04-01", "2008-10-01"),
]:
    df = champ(a, b)
    fobs = gfz("Fobs", fa_, fb_)
    fobs.index = fobs.index.floor("D")
    print(
        "\n==",
        name,
        "| kayit",
        len(df),
        "| bayrak0 orani %.4f" % (df.flag == 0).mean(),
        "| irtifa km %.1f-%.1f" % (df.h.min() / 1e3, df.h.max() / 1e3),
        "| dt medyan s",
        df.t.diff().dt.total_seconds().median(),
    )
    print("   sutun ornegi:", df.iloc[0].to_dict())
    r4, fp, fa = ref(df, fobs)
    roff, _, _ = ref(df, fobs, geomagnetic_activity=0, mixed_ap_ut_long=0)
    d = np.log(roff / r4)
    print(
        "   F10.7 onceki gun %.1f-%.1f, 81g %.1f-%.1f"
        % (np.nanmin(fp), np.nanmax(fp), np.nanmin(fa), np.nanmax(fa))
    )
    print("   ln(anahtar kapali / ap=4): ort %+.2e, maks|.| %.2e" % (d.mean(), np.abs(d).max()))
    ok = (df.flag == 0) & (df.rho > 0)
    y = np.log(df.rho[ok] / r4[ok.to_numpy()])
    print(
        "   ln(gozlem / MSIS2.1 ap=4): ort %+.3f, std %.3f, %%1-%%99 [%+.2f, %+.2f]"
        % (y.mean(), y.std(), y.quantile(0.01), y.quantile(0.99))
    )
    if name.startswith("firtina"):
        df = df[ok].assign(y=y)
        onset = pd.Timestamp("2003-10-29 07:04")  # Zesta ve Oliveira 2019 Tablo 2
        pre = df[(df.t >= onset - pd.Timedelta(hours=24)) & (df.t < onset)]
        band = lambda d_: np.where(
            d_.lat > 63,
            "kutupK",
            np.where(d_.lat < -63, "kutupG", np.where(d_.lat.abs() < 30, "alcak", "")),
        )
        df["band"] = band(df)
        pre = pre.assign(band=band(pre))
        b_s = pre[pre.band != ""].groupby("band").y.mean()
        print("   firtina oncesi 24 sa yanlilik b_s:", b_s.round(3).to_dict())
        df = df[df.band != ""].copy()
        df["ya"] = df.y - df.band.map(b_s)
        df["seg"] = ((df.band != df.band.shift()) | (df.t.diff().dt.total_seconds() > 300)).cumsum()
        seg = df.groupby("seg").agg(
            t=("t", "mean"),
            band=("band", "first"),
            ya=("ya", "mean"),
            ymax=("ya", "max"),
            n=("ya", "size"),
            lst=("lst", "median"),
        )
        seg["epok_sa"] = (seg.t - onset).dt.total_seconds() / 3600
        w = seg[(seg.epok_sa > -5) & (seg.epok_sa < 14) & (seg.n > 20)]
        print("   epok(sa)  bant    ort_y  maks_y  yerel_saat   (y = ln oran - b_s; cografi enlem)")
        for _, r in w.iterrows():
            print(
                "   %+6.2f   %-6s %+6.2f  %+6.2f   %5.1f" % (r.epok_sa, r.band, r.ya, r.ymax, r.lst)
            )
