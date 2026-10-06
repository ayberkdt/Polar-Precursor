import inspect
import time

import numpy as np
import pymsis

print("pymsis", pymsis.__version__)
print("sig:", inspect.signature(pymsis.calculate))
print("create_options sig:", inspect.signature(pymsis.msis.create_options))
print("Variable:", [(v.name, int(v)) for v in pymsis.Variable])
n = 100_000
t0 = np.datetime64("2003-10-29T00:00:00")
dates = t0 + (np.arange(n) * 10).astype("timedelta64[s]")
sec = np.arange(n) * 10.0
lat = 87.3 * np.sin(2 * np.pi * sec / 5613.0)
lon = ((-sec / 240.0) % 360.0) - 180.0
alt = np.full(n, 400.0)
f = np.full(n, 150.0)
fa = np.full(n, 140.0)


def run(ap, **kw):
    aps = np.tile(np.array(ap, float), (n, 1))
    s = time.perf_counter()
    out = pymsis.calculate(dates, lon, lat, alt, f, fa, aps, version=2.1, **kw)
    return out[:, pymsis.Variable.MASS_DENSITY], time.perf_counter() - s, out.shape


r4, dt, shp = run([4] * 7)
print("shape", shp, "sure %.2f s -> %.0f nokta/s" % (dt, n / dt))
roff, dt2, _ = run([4] * 7, geomagnetic_activity=0, mixed_ap_ut_long=0)
roff80, _, _ = run([80] * 7, geomagnetic_activity=0, mixed_ap_ut_long=0)
r80, _, _ = run([80] * 7)
r80s, _, _ = run([80] * 7, geomagnetic_activity=-1)
r00, _, _ = (
    lambda a: (
        pymsis.calculate(
            dates, lon, lat, alt, f, fa, np.tile(np.array([4.0] * 7), (n, 1)), version=0
        )[:, 0],
        0,
        0,
    )
)(0)
r20, _, _ = (
    lambda a: (
        pymsis.calculate(
            dates, lon, lat, alt, f, fa, np.tile(np.array([4.0] * 7), (n, 1)), version=2.0
        )[:, 0],
        0,
        0,
    )
)(0)


def st(a, b, name):
    d = np.log(a / b)
    print("%-42s ln-oran ort %+.5f  maks|.| %.5f" % (name, d.mean(), np.abs(d).max()))


st(roff, r4, "anahtar kapali(ap=4) / ap=4")
st(roff80, roff, "anahtar kapali(ap=80) / anahtar kapali(ap=4)")
st(r80, r4, "ap=80 gunluk / ap=4")
st(r80s, r4, "ap=80 firtina kipi / ap=4")
st(r20, r4, "MSIS2.0 / MSIS2.1 (ap=4)")
st(r00, r4, "MSISE-00 / MSIS2.1 (ap=4)")
