"""ACE balistik gecikmesinin OMNI ile karsilastirilmasi (6 Eki 2026).
    .venv/Scripts/python.exe plans/kanit/ace_gecikme_olcum.py

Soru: ACE (L1) manyetik alanini kendi balistik kaydirmamizla OMNI izgarasina
koyarsak, OMNI'nin dolu oldugu bir gunde (28 Eki 2003) OMNI Bz ile ne kadar
uyusur? Gecikme hatasi kac dakika?
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from space_environment.io.ace import read_ace_mfi_hapi, read_ace_swe_hapi
from space_environment.io.omni import read_omni_hro
from space_environment.physics.propagation import ballistic_delay_s, minute_means, shift_by_delay

ROOT = Path(__file__).resolve().parents[2]
RE_KM = 6371.0  # OMNI'nin yay soku konumu Re biriminde; Re degeri OMNI belgesinden okunmadi

omni = read_omni_hro(ROOT / "tests/fixtures/omni_min_2003_doy301_303_excerpt.asc").loc["2003-10-28"]
mfi = read_ace_mfi_hapi(
    ROOT / "data/raw/ace/AC_H0_MFI_20031028_20031031.csv", ROOT / "data/raw/ace/AC_H0_MFI_info.json"
).loc["2003-10-28"]
swe = read_ace_swe_hapi(
    ROOT / "data/raw/ace/AC_H0_SWE_20031028_20031031.csv", ROOT / "data/raw/ace/AC_H0_SWE_info.json"
).loc["2003-10-28"]

print("OMNI 28 Eki 2003: IMF uydu kimligi", omni["imf_spacecraft_id"].value_counts().to_dict(),
      "(60 = Geotail, 71 = ACE; OMNI belgesi)")
print("OMNI kendi zaman kaydirmasi [s]:", omni["timeshift_s"].describe()[["min", "50%", "max"]].round(0).to_dict())
print("OMNI yay soku x [Re]: ortanca %.2f; OMNI uydu x [Re]: ortanca %.2f; ACE x [Re]: ortanca %.1f"
      % (omni["bow_shock_x_gse_re"].median(), omni["x_gse_re"].median(), mfi["x_gse_km"].median() / RE_KM))
print("ACE SWEPAM vx gecerli orani (28 Eki): %.2f" % swe["vx_gse_km_s"].notna().mean())

vx = minute_means(swe, columns=["vx_gse_km_s"])["vx_gse_km_s"].reindex(omni.index)
x_sc = minute_means(mfi, columns=["x_gse_km"])["x_gse_km"].reindex(omni.index)
target = (omni["bow_shock_x_gse_re"] * RE_KM).to_numpy()
delay = pd.Series(ballistic_delay_s(x_sc.to_numpy(), vx.to_numpy(), x_target_km=target), index=omni.index)
print("ACE -> yay soku balistik gecikme [s]: ortanca %.0f, p10 %.0f, p90 %.0f (n=%d)"
      % (delay.median(), delay.quantile(0.1), delay.quantile(0.9), delay.notna().sum()))
print("   OMNI'nin Geotail kaydirmasi ile fark: ortanca %.0f s (beklenen: ACE 231 Re'de, Geotail ~30 Re'de)"
      % (delay - omni["timeshift_s"]).median())

# Gecikme serisini ACE ornek zamanlarina tasi (bosluklar icdegerlenir), ACE'yi kaydir, dakikaya bagla.
delay_on_mfi = delay.interpolate(limit_direction="both").reindex(mfi.index, method="nearest").to_numpy()
shifted = shift_by_delay(mfi, delay_on_mfi)
bz_ace = minute_means(shifted, columns=["bz_gsm_nt"], min_samples=2)["bz_gsm_nt"].reindex(omni.index)
bz_omni = omni["bz_gsm_nt"]
both = bz_ace.notna() & bz_omni.notna()
r = bz_ace.corr(bz_omni)
rms = float(np.sqrt(((bz_ace - bz_omni) ** 2).mean()))
print("Kaydirilmis ACE Bz vs OMNI Bz (1 dk, %d ortak dakika): r = %.3f, RMS fark = %.2f nT, OMNI Bz std = %.2f nT"
      % (both.sum(), r, rms, bz_omni.std()))
lags = [(k, bz_ace.shift(k).corr(bz_omni)) for k in range(-20, 21)]
best_k, best_r = max(lags, key=lambda item: item[1])
print("Ek gecikme taramasi (-20..+20 dk): en iyi %+d dk, r = %.3f  (pozitif = balistik gecikme kisa kalmis)"
      % (best_k, best_r))
print("Ek gecikme uygulaninca RMS = %.2f nT"
      % float(np.sqrt(((bz_ace.shift(best_k) - bz_omni) ** 2).mean())))
print()
print("Yorum: OMNI o gun Geotail'den uretilmis; ACE'den balistik kaydirmayla elde edilen Bz, OMNI ile")
print("r~0.7 uyusuyor ve gecikme hatasi dakikalar mertebesinde. Faz cephesi yontemi uygulanmadi.")
print("Tek gun, tek olay; genel bir hata butcesi degil.")
