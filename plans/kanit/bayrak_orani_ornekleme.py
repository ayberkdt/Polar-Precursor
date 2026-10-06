"""Her ayin 15'inde bir gun: gecerli (bayrak 0) kayit orani. ESA V2, VirES HAPI. 5 Eki 2026."""

import io
import time
import urllib.request

import pandas as pd


def one(ds, day):
    nxt = (pd.Timestamp(day) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    u = (
        "https://vires.services/hapi/data?dataset=%s&parameters=validity_flag&start=%sT00:00:00Z&stop=%sT00:00:00Z"
        % (ds, day, nxt)
    )
    for k in range(3):
        try:
            txt = urllib.request.urlopen(u, timeout=90).read().decode()
            break
        except Exception:
            txt = None
            time.sleep(3)
    if not txt:
        return (0, float("nan"))
    f = pd.read_csv(io.StringIO(txt), header=None)[1]
    return (len(f), (f == 0).mean())


for ds, y0, y1 in [("CH_OPER_DNS_ACC_2_", 2001, 2010), ("GR_OPER_DNS1ACC_2_", 2002, 2015)]:
    print("\n" + ds + "  (satir: yil; sutun: ay 1-12; deger: bayrak-0 orani %, '--' veri yok)")
    for y in range(y0, y1 + 1):
        row = []
        for m in range(1, 13):
            n, r = one(ds, "%d-%02d-15" % (y, m))
            row.append(" --" if n == 0 else "%3.0f" % (100 * r))
            time.sleep(0.2)
        print(y, " ".join(row), flush=True)
