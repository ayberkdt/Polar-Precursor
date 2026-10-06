# 12 — Sidera'ya güneş ve jeomanyetik etkinlik bölümü: karar ve tasarım

Hazırlanma: 6 Ekim 2026. Dayanak: Sidera deposu bu oturumda okundu (`CLAUDE.md`, `pyproject.toml` `[tool.importlinter]` ve `[tool.mypy]`, `docs/ARCHITECTURE.md`, `docs/ATMOSPHERE_AND_DRAG.md`, `physics/atmosphere/space_weather.py`, `physics/atmosphere/models.py`, `core/drag/aerodynamics.py`, `cli/sidera.py` ve `cli/atmosphere_options.py`, `io/models/atmosphere_tables.py`, `physics/geomagnetism/`, `examples/atmosphere/nrlmsise_leo.py`, `docs/algorithms/algorithm_registry.yaml` ve şeması, `data/README.md`, `data/data_sources.json`, `tests/conftest.py`). Uygulama: bu depodaki `space_environment` paketi 6 Ekim'de bu tasarımın katman düzenine taşındı (bkz. "Bu depoda yapılanlar").

## 1. Karar: evet, ama "bölüm" tek paket değil, üç katmana yayılan bir dilim

**Eklenmeli.** Dört gerekçe, hepsi Sidera'nın kendi kodundan:

1. **Sidera'nın kendi ilkesiyle çelişen bir boşluk var.** `space_weather.py` modül başlığı "indices are *data*, not physics" diyor; ama okuyucu (`TimeSeriesSpaceWeatherProvider.from_csv`) `physics` katmanında duruyor ve yalnız dört sütunlu bir CSV okuyor. Yayınlanan indeks dosyalarının hiçbiri o biçimde değil.
2. **Fırtına kipi gerçek veriyle sürülemiyor.** `TimeSeriesSpaceWeatherProvider` hiçbir yolda `ap_history` doldurmuyor (`_state` yalnız günlük Ap geçiriyor); `SpaceWeatherState.nrlmsis_ap_array(storm_mode=True)` o yüzden ölçülen veriyle hata veriyor. Kayıt dosyasındaki NRLMSIS girişi de bunu sınırlama olarak yazmış: "storm-time mode needs a 3-hourly Ap history the provider may not have". Bu depodaki köprüyle ölçüldü: 29 Eki 2003 CHAMP izi boyunca fırtına kipi, sakin referansın **1,56-1,63 katı** yoğunluk veriyor (`kanit/ornek_firtina_sakin_nrlmsis_cikti_2026-10-06.txt`). Sidera bugün bu farkı üretemiyor.
3. **JB2008 yolu yok.** İkinci bir ampirik model eklenecekse girdileri (F10, S10, M10, Y10, dTc, gecikme kuralı) önce veri olarak var olmalı; bu depoda yazıldı.
4. **Katman kuralı zaten uygun.** `[tool.importlinter]` yığını `io | frames` → `physics` → `core` → … → `analysis` diye kurulu. Okuyucular `io`'ya, kurallar `physics`'e, katalog ve öznitelik kurucular `analysis`'e girince **yeni sözleşme gerekmiyor**; `ARCHITECTURE.md` yalnız paragraf kazanır. Ayrıca `physics/geomagnetism/` (IGRF) zaten var; `physics/space_environment/` onun doğal komşusu.

**Karşı argümanlar ve yanıtları:**

| Karşı argüman | Yanıt |
| --- | --- |
| Sidera ay odaklı; Dünya termosferi kapsam şişmesi | Dünya atmosferi (NRLMSIS, Harris-Priester, ERA dönüşü, WGS-84) zaten var ve CLI'dan sürülüyor. Eksik olan yalnız girdi verisi. |
| `physics` katmanında pandas | Sidera'nın çekirdek bağımlılığı (`pyproject` ana listesinde); ama `physics` dosyalarının alışkanlığı numpy. Taşıma günü kararı: `memory.py` ve `shock.py` numpy'a çevrilir ya da pandas kabul edilir. `coupling.py` zaten yalnız numpy. |
| Katalog ve öznitelik kurucu tez-özel | `analysis` katmanı zaten çalışma-özel kod için (`analysis/studies/`). Oraya girer; istenmezse bu depoda kalır, Sidera `io` ve `physics` dilimini alır. |
| Doğrulanmamış kaynaklar (Newell, DTC birimi, R&C harfleri) | Kayıt sistemi bunun için `verification_status` taşıyor; `pending_verification` ile girilir, `verified_primary_source` iddia edilmez. |

## 2. Hedef yerleşim (Sidera)

```
src/sidera/
  io/space_weather/                     ← bu depodaki space_environment.io
    __init__.py
    gfz.py  omni.py  hapi.py  ace.py  kyoto.py  set_jb2008.py
    weimer_heating.py  silso.py  toleos.py
  physics/atmosphere/space_weather.py   ← physics.space_weather + physics.index_conventions
    (+ GfzSpaceWeatherProvider, quiet_geomagnetic, jb2008_solar_inputs, dtc_at,
       centred_mean_f107, nrlmsis_ap_history)
  physics/space_environment/            ← physics.{coupling,memory,shock,storm_intensity,storm_onset,propagation}
    __init__.py
    coupling.py  memory.py  shock.py  storms.py  propagation.py
  analysis/space_environment/           ← analysis.{catalog,features,solar_cycle}
    __init__.py
    catalog.py  features.py  solar_cycle.py
examples/atmosphere/storm_vs_quiet_nrlmsis.py   ← bu depodaki examples/ (çalıştırıldı)
docs/SPACE_ENVIRONMENT.md                        ← yeni belge; ATMOSPHERE_AND_DRAG.md §4 genişler
data/space_weather/                              ← data_sources.json'a yeni "space_weather" grubu
tests/io/test_space_weather_readers.py, tests/physics/test_space_environment.py,
tests/analysis/test_space_environment_catalog.py  ← bu depodaki tests/ (fixtures ile)
```

Bu depodaki paket **aynı katman adlarıyla** düzenlendi ve kendi `lint-imports` sözleşmesiyle korunuyor (`analysis | integration` → `physics` → `io` → `common`; 6 Eki: KEPT). Taşıma bir kopyalama ve ad değişikliği olur, yeniden yazım değil.

## 3. Genel yüzey (Sidera'da görünecek adlar)

**`sidera.io.space_weather`** (hepsi yerel dosya alır, `source = "<ad> | sha256=…"` döner; ağ yok)

| İşlev | Girdi | Çıktı |
| --- | --- | --- |
| `read_gfz_daily`, `read_gfz_hpo` | GFZ `Kp_ap_Ap_SN_F107_since_1932.txt`, `Hp30_ap30_*.txt` | günlük kayıt tablosu; yarım saatlik Hp30/ap30 |
| `read_omni_hro` | OMNI HRO 1/5 dk ASCII | UTC indeksli DataFrame, 46/49 adlı sütun, dolgu → NaN |
| `read_hapi_info`, `read_hapi_csv` | HAPI CSV + info JSON | DataFrame; vektör alanlar açılmış |
| `read_ace_mfi_hapi`, `read_ace_swe_hapi` | CDAWeb HAPI CSV | OMNI ile aynı sütun adları |
| `read_kyoto_dst_hapi` | Kyoto HAPI CSV | saat başına damgalı Dst + sürüm kodu |
| `read_solfsmy`, `read_dtcfile` | SET dosyaları | günlük tablo; saatlik dTc |
| `read_heating_deltat` | Zenodo 7667515 HDF5 (`h5py` isteğe bağlı) | 4 dk ΔT, kuzey/güney akı |
| `read_silso_monthly`, `read_silso_cycle_table` | SILSO dosyaları | aylık tablo; çevrim min/maks |
| `read_dns_acc_cdf` | ESA `DNSxACC_2` CDF (`cdflib` isteğe bağlı) | iz boyunca yoğunluk ve bayraklar |

**`sidera.physics.atmosphere.space_weather`** (mevcut modüle eklenir; `SpaceWeatherState` ve `SpaceWeatherProvider` **değişmez**)

- `GfzSpaceWeatherProvider(table, *, geomagnetic="measured"|"quiet")`: `get(utc) -> SpaceWeatherState`, `ap_history` dolu; önceki gün F10.7 ve ortalanmış 81 günlük ortalama ham akıdan. Bu depodaki `GfzIndexProvider` + `SideraSpaceWeatherAdapter` birleşir; `IndexState` ve köprü silinir.
- `QuietGeomagneticProvider(inner)`: herhangi bir sağlayıcının Ap'sini her dilimde 4'e çeviren sarmalayıcı, `source` dizesine "Ap prescribed quiet = 4" ekler; `TimeSeriesSpaceWeatherProvider` ile de çalışır. (Bu depoda yazıldı ve test edildi; `IndexProvider` protokolü Sidera'daki `SpaceWeatherProvider` ile aynı biçimde.)
- `centred_mean_f107`, `nrlmsis_ap_history`, `three_hourly_ap`: kurallar, test edilmiş.
- `Jb2008SolarInputs`, `jb2008_solar_inputs`, `JB2008_LAG_DAYS`, `dtc_at`: JB2008 adaptörü yazıldığında doğrudan girdi. Girdi kuralı pyatmos 1.2.7 ile çapraz kontrol edildi (birebir aynı; `02`). Adaptör için aday kernel pyatmos'un `JB2008_subfunc.JB2008` işlevi (numba, imza `(AMJD, YRDAY, SUN, SAT, F10, F10B, S10, S10B, M10, M10B, Y10, Y10B, DSTDTC)`); Güneş sağ açıklık/dik açıklık ve yıldız zamanı Sidera'nın `models.py` içindeki işlevlerinden gelir. Engel: pyatmos paketi içe aktarılırken IERS dosyası indiriyor; Sidera'nın ağ yasağı için kernel ayrı vendorlanmalı (lisansı okunmadı).

**`sidera.physics.space_environment`**

- `coupling`: `transverse_field_nt`, `clock_angle_rad`, `merging_electric_field_mv_m`, `saturated_merging_field_mv_m`, `newell_coupling`.
- `memory`: `exponential_memory`, `lagged_window_means` (nedensel).
- `shock`: `ShockCandidate`, `detect_shocks`, `hours_since_last_shock`.
- `storms`: `StormIntensity`, `classify_by_min_symh`, `OnsetResult`, `find_main_phase_onset`, `find_southward_turning`.
- `propagation`: `ballistic_delay_s`, `shift_by_delay`, `minute_means`.

**`sidera.analysis.space_environment`**

- `catalog`: `IcmeRecord`, `IcmeCatalogue`, `read_richardson_cane` (`openpyxl` isteğe bağlı), `build_storm_catalog`.
- `features`: `DriverFeatureConfig`, `DriverFeatureBuilder` (nedensellik testiyle).
- `solar_cycle`: `CycleContext`, `cycle_context`, `smoothed_sunspot_number`.

**CLI ve arayüz** (tasarım; yazılmadı)

- `sidera orbit --atmosphere-model nrlmsise --space-weather gfz:<dosya>` (`mean` ve CSV yanında üçüncü biçim), `--geomagnetic measured|quiet`, `--nrlmsis-storm-mode`. `cli/sidera.py` satır 600-611'deki seçim noktasına üç satır; `ui/core/command_builder.py` satır 901'deki `--space-weather` geçişi aynı dizeyi taşır.
- `SimConfig` değişmez: NRLMSIS bugün de çalışma zamanı nesnesi, toplu koşuda paylaşılmıyor (`atmosphere_options.py` başlığı).
- `summary.json`'a sağlayıcı `source` dizesi zaten gidiyor (`AtmosphericDrag` sağlanım kaydı); `[F10.7 measured; Ap prescribed quiet = 4]` eki orada görünür.

## 4. Veri varlıkları (`data/data_sources.json`, yeni grup `space_weather`, alt dizin `space_weather/`)

| Ad | Dosya | Kaynak, lisans | Durum |
| --- | --- | --- | --- |
| `gfz_kp_ap_f107_daily` | `Kp_ap_Ap_SN_F107_since_1932.txt` | GFZ Potsdam; CC BY 4.0, SN sütunu CC BY-NC 4.0 (dosya başlığından okundu) | indirildi, SHA-256 kayıtlı |
| `set_jb2008_solfsmy`, `set_jb2008_dtcfile` | `SOLFSMY.TXT`, `DTCFILE.TXT` | Space Environment Technologies; lisans sayfası okunmadı `[DOĞRULANMADI]` | indirildi |
| `silso_monthly`, `silso_smoothed`, `silso_cycles` | üç dosya | WDC-SILSO; lisans sayfası okunmadı (GFZ başlığı SN için CC BY-NC 4.0 diyor) | indirildi |
| `richardson_cane_icme` | `icmetable2.xlsx` | Harvard Dataverse doi:10.7910/DVN/C2MHTH; CC0 (önceki oturum notu) | indirildi |
| `kyoto_dst_final` | HAPI CSV + info | WDC Kyoto; lisans `wdc/Sec3.html` (info belgesinde) | parça indirildi |
| `weimer_heating_deltat` | `Heating_DeltaT.h5` | Zenodo 7667515; lisans okunmadı | indirildi (58 MB) |
| OMNI HRO yıllık | `omni_minYYYY.asc` | NASA SPDF | **indirilmedi** (≈1,5 GB, onay bekliyor) |

Sidera'nın kuralı: sağlanmayan dosya için `sidera-data verify` "present, no hash" der, hash uydurulmaz. Bu depodaki her indirmenin SHA-256'sı kanıt çıktılarında var.

## 5. Algoritma kaydı girişleri (taslak: `../sidera_merge/algorithm_registry_entries.yaml`)

Sidera "named algorithm, model … or scientific data product" için kayıt istiyor; şema `domain` için uzay havası alanı tanımlamıyor, en yakını `ATM` (sağlayıcı ve kurallar), `MAG` (jeomanyetik indeks türevleri) ve `DATA` (veri ürünleri). Taslak sekiz giriş ve dürüst doğrulama durumu:

| Giriş | Sınıf | Doğrulama durumu | Neden |
| --- | --- | --- | --- |
| NRLMSIS F10.7 ve Ap geçmişi kuralları | standard_implementation | verified_secondary_source | pymsis `utils.py` okundu; Emmert 2021 aslı dilim tanımı için okunmadı |
| Birleşme elektrik alanı (Kan-Lee) | standard_implementation | verified_secondary_source | Liu 2010 üzerinden; Kan ve Lee 1979 aslı okunmadı |
| Newell bağlaşım fonksiyonu | standard_implementation | identifier_verified_content_pending | yalnız ikincil kaynaklar (`06`) |
| Üstel hafıza integrali (Liu 2010 Denk. 8) | standard_implementation | pending_verification | denklem numarası önceki oturum notundan; PDF bu oturumda açılmadı |
| Fırtına şiddet sınıfları (Oliveira-Zesta 2019) | standard_implementation | verified_primary_source | arXiv Tablo 1, 5 Eki (modül başlığı) |
| Ana evre başlangıç kuralı | heuristic | — (HEUR, kaynak yok) | bu projenin tasarımı; beş olayda ayar |
| Şok adayı kuralı | heuristic | — | bu projenin tasarımı; dört olayda ayar |
| JB2008 girdi gecikmeleri | standard_implementation | verified_primary_source | SOLFSMY resmi başlığı okundu; `official_url` kimliği |

Taşıma günü `tools/algorithm_registry.py validate` koşulmadan hiçbiri "bitti" sayılmaz; bu depoda doğrulayıcı yok, taslak **şemaya göre elle** yazıldı.

## 6. Taşıma günü adımları (Sidera'nın "bitti" tanımı, sırayla)

1. Dosyaları kopyala, içe aktarma yollarını değiştir (`space_environment.io` → `sidera.io.space_weather`, vb.). `common/timeutil.py` Sidera'da `space_weather._require_utc` ile birleşir; `common/provenance.py` zaten var (`sidera.common.provenance.sha256_file`, imzası farklı: `missing_ok` seçenekleri), `source_label` oraya eklenir.
2. `GfzIndexProvider` → `GfzSpaceWeatherProvider`; `IndexState` ve `integration/sidera.py` silinir; `geomagnetic` bayrağı `quiet_geomagnetic` sarmalayıcısına döner.
3. `ruff check src tests` (0.12.0), `mypy` (`files` listesine yeni modüller eklenir), `lint-imports` (yeni sözleşme yok; mevcut yığın geçmeli).
4. Testler: `tests/fixtures` buradaki kesitlerle gelir (xlsx 82 kB, Kyoto CSV 40 kB, OMNI kesiti 1,3 MB → bir güne indirilebilir). CDF ve HDF5 testleri `requires_data` + `requires_h5py` işaretli; `conftest.py`'nin `_sidera_data_available` kuralı SPICE/çekim dosyasına bakıyor, uzay havası dosyaları için ayrı bir "var mı" kontrolü ya da modül içi `skip` gerekir.
5. `python tools/api_inventory.py --write` ve `docs/api_snapshot.json`; `docs/PUBLIC_API.md`'ye yeni modüller.
6. Kayıt: `algorithm_registry.yaml` + `references.bib` + `validate/generate/references`; docstring'lere `Reference:` satırları.
7. `docs/ARCHITECTURE.md`: `io` ve `physics` paragraflarına birer cümle; `docs/ATMOSPHERE_AND_DRAG.md` §4'e GFZ sağlayıcısı, fırtına kipi ve sakin referans; yeni `docs/SPACE_ENVIRONMENT.md`.
8. `data/data_sources.json` + `data/README.md` düzenine `space_weather/`; `sidera-data verify` ile hash kontrolü.
9. İsteğe bağlı bağımlılıklar: `openpyxl`, `cdflib` için yeni extras ya da `atmosphere` extra'sının genişletilmesi; `h5py` zaten `ml` içinde. `test_optional_dependency_boundaries.py` çıplak içe aktarmada bunların yüklenmediğini sınar: tembel içe aktarma korunmalı (bu depoda öyle).
10. Yasaklı sözcük ve terminoloji testleri (`test_terminology_hygiene.py`, `test_repo_hygiene.py`) taşınan dosyalarda koşulur; `BANNED_SUBSTRINGS` listesi bu oturumda okunmadı.
11. `CHANGELOG.md` girişi; sürüm iddiası `docs/VERSIONING.md`'ye göre.

Hata sınıfları: Sidera alan hatalarını `SideraError` + yerleşik sınıftan türetiyor (`CLAUDE.md`'de belirtilmiyor, `11`'deki önceki not); burada düz `ValueError`. Taşıma günü bakılacak.

## 7. Bu depoda yapılanlar (6 Eki 2026, ölçüldü)

- Paket Sidera katman düzenine taşındı: `common/`, `io/`, `physics/`, `analysis/`, `integration/`. Eski `indices/`, `solar_wind/`, `storms/`, `features/`, `density/`, `solar/` silindi; içe aktarma yolları kod, test ve kanıt betiklerinde yeniden yazıldı (eski yol kalmadı, grep ile).
- `[tool.importlinter]` sözleşmesi eklendi ve koşuldu: **KEPT** (29 dosya, 24 bağımlılık). `import-linter` dev bağımlılığı.
- `examples/storm_vs_quiet_nrlmsis.py`: Sidera ortamında çalıştı. 29 Eki 2003 CHAMP izi, 1440 nokta, NRLMSIS 2.1 fırtına kipi / sakin referans oranı bantlara göre 1,56-1,63; gözlem / sakin 1,21-1,28; gözlem / fırtına kipi **0,74-0,81** (NRLMSIS bu günde %20-25 fazla veriyor). İndeksler 07:04 UT: F10.7 274,4, F10.7a 146,8, Ap 204, Ap geçmişi (400, 27, 39, 27, 22, 13,5). Kaynak dosyaların SHA-256'ları çıktıda.
- Denetimler: proje ortamında 74 test geçti, 1 atlandı; Sidera ortamında 71 geçti, 5 atlandı; ruff, format, mypy, lint-imports temiz (`kanit/space_environment_testler_2026-10-06b.txt`).
- Taslaklar: `../sidera_merge/algorithm_registry_entries.yaml`, `../sidera_merge/references.bib.draft`, `../sidera_merge/data_sources_entries.json`.

## 8. Yapılmayanlar ve sınırlar

- Sidera deposuna **dokunulmadı**; bu belge ve taslaklar oradaki değişikliğin tarifidir.
- ~~`quiet_geomagnetic` sarmalayıcısı bu depoda henüz bayrak olarak duruyor.~~ 6 Eki akşam: `QuietGeomagneticProvider(inner)` yazıldı, bayrakla aynı sonucu verdiği test edildi; bayrak uyumluluk için kaldı.
- `memory.py` ve `shock.py` pandas kullanıyor; Sidera `physics` alışkanlığına uyup uymadığı taşıma günü kararı.
- CLI ve arayüz değişiklikleri yalnız tasarım.
- Kayıt taslağı Sidera'nın doğrulayıcısından geçmedi.
- Örnek sonucu tek gün ve tek uydu; NRLMSIS'in fırtına hatası hakkında genel bir iddia değil.
