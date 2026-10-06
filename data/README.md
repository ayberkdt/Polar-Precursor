# data/ — ham ve türetilmiş veri (depoda yok)

Bu klasör `.gitignore` ile dışarıda tutulur; yalnız bu README depodadır. Kod
ağdan hiçbir şey indirmez: her dosya elle (ya da `plans/01`-`02` içindeki
adreslerden) indirilir, SHA-256'sı kanıt çıktısına yazılır. Testlerin gerek
duyduğu kesitler `tests/fixtures/` altında bayt-birebir saklanır; büyük dosyaya
bağlı testler `requires_data` işaretlidir ve dosya yoksa atlanır.

## Yerleşim (6 Ekim 2026'da diskte olanlar; `find data/raw` ile okundu)

| Yol | İçerik | Kaynak (`plans/`) | Okuyucu |
| --- | --- | --- | --- |
| `raw/density/CHAMP/CH_OPER_DNS_ACC_2__<YYYYMMDD>T000000_<YYYYMMDD>T235959_0001.cdf` | Günlük 10 s yoğunluk, ESA/TU Delft V2 (şimdilik tek gün: 2003-10-29) | `01` | `space_environment.io.toleos.read_dns_acc_cdf` |
| `raw/docs/SW-TN-DUT-GS-129-01_TOLEOS_Product_Definition_Document.pdf` | Ürün tanım belgesi | `01` | — |
| `raw/omni/monthly_1min/omni_min<YYYYMM>.asc` | OMNI HRO 1 dk, aylık ASCII (2001-11, 2003-11, 2004-11, 2005-05, 2005-08) | `02` | `space_environment.io.omni.read_omni_hro(path, "1min")` |
| `raw/omni/yearly_5min/omni_5min<YYYY>.asc` | OMNI HRO 5 dk, yıllık (2003) | `02` | `read_omni_hro(path, "5min")` |
| `raw/gfz/Kp_ap_Ap_SN_F107_since_1932.txt` | GFZ günlük Kp/ap/F10.7 | `02` | `space_environment.io.gfz.read_gfz_daily` |
| `raw/kyoto/hour_dst_final_<start>_<end>.csv`, `hour_dst_final_info.json` | Kyoto Dst, HAPI CSV + info | `02` | `space_environment.io.kyoto.read_kyoto_dst_hapi` |
| `raw/ace/AC_H0_MFI_<start>_<end>.csv`, `AC_H0_SWE_…csv`, `*_info.json` | ACE MFI/SWEPAM, HAPI (CDAWeb) | `02` | `space_environment.io.ace` |
| `raw/set/SOLFSMY.TXT`, `raw/set/DTCFILE.TXT` | JB2008 indeksleri (SET) | `02` | `space_environment.io.set_jb2008` |
| `raw/heating/Heating_DeltaT.h5` (+ arşivin README ve örnek betikleri) | Weimer ve ark. 2023 ısıtma/ΔT, Zenodo 7667515 | `02`, `06` | `space_environment.io.weimer_heating` |
| `raw/silso/SN_m_tot_V2.0.txt`, `SN_ms_tot_V2.0.txt`, `TableCyclesMiMa.txt` | SILSO aylık, düzgünleştirilmiş, çevrim tablosu | `02` | `space_environment.io.silso` |
| `raw/catalog/icmetable2.xlsx` | Richardson-Cane ICME listesi | `05` | `space_environment.analysis.catalog.read_richardson_cane` |
| `derived/champ_track_20031029_60s.csv` | 60 s'ye indirgenmiş iz (test kesiti de buradan) | bu depo | `pandas.read_csv(..., index_col="time_utc", parse_dates=True)` |

## Henüz indirilmeyenler (ad biçimi plandan, diskte doğrulanmadı)

- GFZ Hp30/ap30 tam serisi (`02`; yalnız 2003-10-27..11-01 kesiti `tests/fixtures/` altında).
- OMNI 1 dk yıllık dosyalar 2001-2015 (≈1,5 GB; `02`).
- CHAMP tüm görev (1,97 GB, 3496 günlük dosya) ve GRACE-A
  (`raw/density/GRACE/Sat_1/<YYYY>/GR_OPER_DNS1ACC_2__…_0001.cdf`, `01`).

Ham veri ve önbellekler C: sürücüsüne yazılmaz; proje D: üzerindedir
(`plans/00`). Türetilmiş her dosyanın üreten komutu ve kaynak dosya özetleri
`results/<kosu>/manifest.json` içinde kaydedilir (`polar_precursor.experiment.manifest`).
