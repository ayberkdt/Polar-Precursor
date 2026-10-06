# 11 — `space_environment`: güneş ve jeomanyetik etkinlik modülü

Hazırlanma: 5 Ekim 2026; genişletme: 6 Ekim 2026. Kod: `../src/space_environment/`, testler: `../tests/`.

Bu modül Sidera'da karşılığı olmayan bir işi yapıyor: güneş ve jeomanyetik etkinliği **veri olarak** okumak, termosfer modellerinin beklediği kurallara çevirmek, güneş rüzgarı sürücülerini hesaplamak ve fırtına kataloğu ile tahmin anı özniteliklerini kurmak. Sidera'ya paralel geliştiriliyor; Sidera'nın kod kurallarıyla yazıldı ki ileride doğrudan taşınabilsin.

## Durum (6 Eki 2026, bu oturumda çalıştırıldı)

| Denetim | Sonuç |
| --- | --- |
| `pytest`, proje ortamı (Python 3.12) | **91 geçti**, 1 atlandı (Sidera köprüsü; Sidera bu ortamda yok) — gece güncellemesi |
| `pytest`, Sidera ortamı (Python 3.10, `PYTHONPATH=src`) | **87 geçti**, 6 atlandı (openpyxl, cdflib, apexpy orada kurulu değil) |
| `lint-imports` (katman sözleşmesi, `12`) | KEPT |
| `ruff check src tests` (0.12.0, Sidera'nın sabitlediği sürüm) | temiz |
| `mypy` (`disallow_untyped_defs`) | 30 dosyada sorun yok |

Çıktı kayıtları: `kanit/space_environment_testler_2026-10-06.txt`, `kanit/space_environment_testler_sidera_2026-10-06.txt`, `kanit/space_environment_genisletme_cikti_2026-10-06.txt` (yeni parçaların gerçek veri üzerindeki sayıları; betik `kanit/space_environment_genisletme.py`).

Testler sentetik değil, **gerçek veri kesitleri** üzerinde: GFZ günlük dosyası, Hp30, OMNI 1 dakikalık (28-30 Eki 2003), ACE MFI/SWEPAM (CDAWeb HAPI), Kyoto Dst (HAPI), SET SOLFSMY/DTCFILE, SILSO, Richardson-Cane xlsx'in tamamı. Kesitler `tests/fixtures/` altında. ESA CDF ve Zenodo HDF5 büyük olduğu için `requires_data` işaretli testler `data/raw/` altındaki dosyayı kullanır, yoksa atlanır.

## Yapı

Düzen 6 Eki 2026 akşamı Sidera'nın katman yığınına göre yeniden kuruldu (`12`); her paketin Sidera'daki hedefi `__init__` başlığında yazıyor. Katmanlar `[tool.importlinter]` ile korunuyor: `analysis | integration` → `physics` → `io` → `common` (`lint-imports`: KEPT).

```
src/space_environment/
  common/                → sidera.common
    timeutil.py          UTC zorunluluğu, gün başlangıcı
    provenance.py        SHA-256, "<dosya> | sha256=..." etiketi (Sidera biçimi)
  io/                    → sidera.io.space_weather
    gfz.py               GFZ günlük dosyası ve Hp30/ap30 okuyucuları
    omni.py              OMNI HRO ASCII okuyucu (1 ve 5 dakika), dolgu → NaN
    hapi.py              HAPI CSV + info JSON okuyucu (Kyoto, CDAWeb); vektör alanları açar
    ace.py               ACE MFI/SWEPAM (HAPI) okuyucuları, OMNI sütun adlarıyla
    kyoto.py             Kyoto saatlik Dst (merkez damgası → saat başı), "son tamamlanmış saat"
    set_jb2008.py        SOLFSMY ve DTCFILE okuyucuları
    weimer_heating.py    Zenodo 7667515 Heating_DeltaT.h5 (W05 Poynting akısı, ΔT; 4 dk)
    silso.py             SILSO aylık/düzgünleştirilmiş güneş lekesi, çevrim min/maks tablosu
    toleos.py            ESA/TU Delft DNSxACC_2 CDF okuyucu, bayrak özeti
  physics/               → sidera.physics.atmosphere.space_weather ve sidera.physics.space_environment
    index_conventions.py Önceki gün F10.7, ortalanmış 81 gün ortalaması, NRLMSIS Ap geçmişi
    space_weather.py     GfzIndexProvider, QuietGeomagneticProvider (sakin sarmalayıcı), IndexState, JB2008 gecikme kuralı, dtc_at
    coupling.py          Birleşme elektrik alanı, doygun biçimi, Newell fonksiyonu
    memory.py            Üstel hafıza integrali, gecikme penceresi ortalamaları (nedensel)
    shock.py             Şok adayı tespiti ve "son şoktan beri" kuralı
    storm_intensity.py   En düşük SYM-H'ye göre beş sınıf
    storm_onset.py       Bz dönüşü kuralları (otomatik sıfır epok)
    propagation.py       L1 → yay şoku balistik gecikme, yeniden damgalama, dakika ortalaması
    magnetic_coordinates.py  apexpy ile QD enlem/boylam ve MLT (aylık epok; `magnetic` extra)
  analysis/              → sidera.analysis.space_environment
    catalog.py           Richardson-Cane xlsx okuyucu, fırtına kataloğu kurucu
    features.py          Tahmin anı için 37 sürücü özniteliği (Em, Bz, SYM-H); nedensellik garantili
    index_features.py    İndeks (F10.7, Ap, Kp, ap30, Dst) ve geometri öznitelikleri; aralık bitmeden kullanılmaz
    solar_cycle.py       Çevrim numarası, evre ve düzgünleştirilmiş güneş lekesi bağlamı
    passes.py            Bant parçaları (kutup/orta/alçak), yarım yörünge yönü, örnek kurucu, sızıntı denetimi
  integration/           → taşımada silinir (sağlayıcı doğrudan SpaceWeatherState üretir)
    sidera.py            Sidera'nın SpaceWeatherProvider sözleşmesine köprü
examples/
  storm_vs_quiet_nrlmsis.py   Sidera ortamında koşan örnek (→ sidera examples/atmosphere/)
```

İsteğe bağlı bağımlılıklar (`pyproject.toml`): `catalog` (openpyxl), `density` (cdflib), `heating` (h5py). Çekirdek yalnız numpy ve pandas.

## Tasarım ilkeleri (Sidera'dan alındı)

Sidera'nın `CLAUDE.md` dosyası ve `space_weather.py` modülü okunarak:

- **Ağdan veri çekmez.** Her okuyucu yerel dosya alır ve SHA-256'sını kayda geçirir. HAPI okuyucu CSV ile birlikte `info` JSON'unu da ister; CSV tek başına sütunlarını söylemiyor.
- **Sessiz varsayılan yok.** Eksik indeks hata verir; doldurulmaz. Eksik değerler `None`/NaN/`<NA>` olarak döner.
- **Birim ve çerçeve adın içinde:** `bz_gsm_nt`, `flow_speed_km_s`, `f107_obs_sfu`, `jh_north_gw`, `density_kg_m3`.
- Dondurulmuş, `slots` kullanan veri sınıfları; açıklayıcı `ValueError` iletileri; zaman dilimi belirtilmemiş `datetime` reddedilir.
- Aynı lint ve tip ayarları (satır 100, hedef py310, aynı kural kümesi).
- Sidera'yı ve isteğe bağlı paketleri modül yüklenirken içe aktarmaz; işlev içinde tembel içe aktarır.
- Doğrulanmamış kaynak bilgisi kodda "doğrulanmadı" diye yazılır (örnek: DTCFILE'ın birimi ve saat damgası).

## Bileşenler ve doğrulama

**GFZ okuyucuları, indeks kuralları, sağlayıcı, Sidera köprüsü** — 5 Eki; değişmedi. Özet: 29 Eki 2003 satırı (Kp 4,667 4,0 9,0 8,0 …; Ap 204; F10.7 291,7) web servisiyle aynı; Ap geçmişi (400, 27, 39, 27, 22,0, 13,5) elle türetildi; `geomagnetic="quiet"` = fırtına terimi kapalı referans; köprü Sidera `NrlmsiseAtmosphere(storm_mode=True)` ile uçtan uca çalıştı ve Sidera'nın `ap_history` doldurmama boşluğunu kapattı.

**OMNI okuyucu, bağlaşım, hafıza, fırtına sınıfı, başlangıç kuralı** — 5-6 Eki; değişmedi (kural 2: beş yayınlanmış olayda 7 dk içinde, `05`).

**HAPI okuyucu** (`io/hapi.py`, 6 Eki)

- `info` belgesinden parametre adı, tip, dolgu ve boyut; `size: [3]` olan parametre `<ad>_0..2` sütunlarına açılıyor; ilk parametre `isotime` olmak zorunda; yeniden adlandırma sözlüğündeki her ad var olmalı.
- Doğrulama: CDAWeb `AC_H0_MFI` info'su dört parametreye ve yedi sütuna açılıyor; Kyoto ve CDAWeb dolgu değerleri (`99999`, `-1.0E31`) NaN oluyor.

**ACE yedeği** (`solar_wind/ace.py`, 6 Eki)

- Sütun adları OMNI ile aynı (`bz_gsm_nt`, `flow_speed_km_s` …) ki aynı öznitelik kodu çalışsın. Balistik gecikme `(x_uydu − x_hedef)/|vx|`, hedef açık parametre; `vx ≥ 0` hata, NaN hız NaN gecikme. Dakika ortalaması OMNI'nin 1 dk ızgarasına.
- **Ölçüm:** 28-30 Eki 2003'te MFI Bz günlük %100/%100/%100, OMNI boşluğunda (29 Eki 05:50-18:42) 2898 kayıt kesintisiz. SWEPAM hız %51/%0/%0. Plazma yedeği yok; Em o günlerde hesaplanamaz.
- Doğrulama: ilk kayıt 29 Eki 05:30:12 |B| 10,579, Bz 1,149 nT, x 1 476 239 km (dosya satırından); 05:41:24 Bz −1,129 (sunucuda görülen kayıt).

**Kyoto Dst** (`indices/kyoto.py`, 6 Eki)

- `info`'da `timeStampLocation: center` (HH:29:30); okuyucu saat başına çeviriyor ve bunu `attrs` içine yazıyor. `versionCode` korunuyor (20 = final, ilk dönüşüm).
- `latest_complete_hour`: 07:04 için 06:00-07:00 değeri; saatlik ortalama saat bitmeden bilinmez.
- Doğrulama: 1 Eki 2003 00 UT −11 (WDC aylık tablosunun ilk hücresi); 30 Eki 22 UT **−383**; dosya minimumu −422 (20 Kas 2003 20 UT).

**SET JB2008 indeksleri** (`indices/set_jb2008.py`, 6 Eki)

- SOLFSMY başlığı okundu: değerler 12 UT'de sfu, gün için tek değer; gecikmeler F10/S10 1 gün, M10 2 gün, Y10 5 gün, 81 günlük ortalamalar aynı gecikmeyle. `Ssrc` bayrağı 0 olan indeks NaN (dosyada hiç yok).
- Doğrulama: 29 Eki 2003 satırı (279,1 / 140,3 / 155,1 / 126,7 / 182,7 / 132,4 / 185,2 / 140,5, `1B11`); 30 Eki 07:04 için girdiler F10 29 Eki'den, M10 28 Eki'den, Y10 25 Eki'den.
- DTCFILE: `DTC YYYY DDD` + 24 değer; 1997-2026, 259 824 saat, en büyük 579 (11 May 2024 02 UT). **Birimi (K) ve "k. değer = k:00 saati" eşlemesi doğrulanmadı**; kod bunu söylüyor.

**Isıtma serisi** (`indices/weimer_heating.py`, 6 Eki)

- Zenodo ReadMe okundu: `JHNORTH`/`JHSOUTH` GW, `DELTAT` K, `MJTIMES` MJD, 4 dk, 1 Oca 2000 - 1 Oca 2020, IMF boşlukları içdeğerlenmiş ve `OKFLAG=0`.
- Ölçüm: 2 629 800 kayıt, her adım tam 240 s, ilk damga 2000-01-01 00:04, son 2020-01-01 00:00; okuma 1,5 s; IMF-ok oranı %99,18. 28-31 Eki 2003: ΔT en çok 841 K (29 Eki 23:28), kuzey/güney akı en çok 1472/1471 GW.
- MJD → UTC: `MJD − 40587` gün (Unix epoğu), saniyeye yuvarlanıyor; 51544,0 → 2000-01-01 00:00 testte.

**Güneş çevrimi** (`solar/cycle.py`, 6 Eki)

- SILSO aylık ve 13 aylık düzgünleştirilmiş dosyalar (sürüm 2.0; −1 eksik) ve çevrim min/maks tablosu. Düzgünleştirme formülü yeniden hesaplanmıyor; SILSO'nun kendi serisi okunuyor.
- Evre kuralı (bu projenin tanımı): minimumdan maksimuma "yükselen", maksimumdan sonraki minimuma "alçalan"; kesir takvim ayıyla. 29 Eki 2003: çevrim 23, alçalan, 23/85 = 0,27; düzgün SN 89,1. Çevrim 25'in maksimumu tabloda yok; 2020 sonrası için hata.

**Fırtına kataloğu** (`storms/catalog.py`, 6 Eki)

- Okuyucu: 644 olay; 2001-2015'te 334; ek harfler `*_note` alanlarında (`S` 164, `P` 112, `W` 49, `H` 14, `(A)` 27); satır 309'da rahatsızlık ICME başlangıcından sonra, kabul.
- Kurucu: min SYM-H penceresi `[t_a, ICME bitişi + 24 sa]`, bir sonraki rahatsızlıkta kesilir; kapsam < %80 ise sınıf boş; kural 2 epoku; ilk 24 saatte Bz/hız/yoğunluk kapsamı; küme = örtüşen ya da 24 saatten yakın pencereler.
- Doğrulama (28-30 Eki 2003, OMNI kesiti): −58 nT orta (R&C Dst −32), −391 nT aşırı 30 Eki 01:48 (R&C −353), üçüncü olay kesit dışında → boş; hepsi bir küme; 20 Kasım ayrı küme.

**Şok bayrağı** (`solar_wind/shock.py`, 6 Eki) — ölçüm tablosu `06` içinde. Dört R&C şokunda 3-10 dk, 9 Kas 2004'te +29 dk, iki olayda kaçırma (plazma boşluğu). `confirmed_at = zaman + 10 dk`.

**Öznitelik kurucu** (`features/drivers.py`, 6 Eki)

- 32 öznitelik (`06`). Her değer `frame.loc[:t0]` üzerinden; hafıza integrali nedensel; şok yalnız `confirmed_at ≤ t0` ise sayılır.
- Sızıntı testi: `t0` sonrası tüm sütunlar 10⁵ yapıldı, hiçbir öznitelik değişmedi. OMNI boşluğunda `em_valid_6h` 1,0 → 0,0 düşüyor, SYM-H sürüyor.
- Hız: kurulum 0,11 s; 391 t0 için 1,66 s (235 satır/s).

**Yoğunluk okuyucu** (`density/toleos.py`, 6 Eki)

- Ürün tanım belgesindeki alanlar; dolgular `FILLVAL` özniteliğinden (0,999e33 ve 127); bayraklar `Int8` (eksik `<NA>`); `TIME SYSTEM` UTC değilse hata; `attrs` içinde kaynak etiketi, uydu, işleme zamanı, yazılım sürümü (42).
- Doğrulama: 29 Eki 2003 CHAMP dosyası 8640 kayıt (10 s), 00:00:00 - 23:59:50, ilk irtifa 417 923,84 m, enlem −76,536°, yoğunluk 5,322e−12; %100 nominal.

## Kod yazarken çıkan bulgular

1. **OMNI en büyük fırtınada boş** (5 Eki): 29 Eki 05:50-18:42 ve 30 Eki boyunca IMF ve plazma yok; indeksler sürüyor. Sonuçları `02`, `05`, `06`, `07` içinde.
2. **ACE yedeği yalnız alan için** (6 Eki): yukarıda. Sürücüsüz B3 türevi için gerekçe güçlendi: o günlerde Em yok, Bz var.
3. **Katalog penceresi kesilmeli** (6 Eki): ardışık ICME'lerde pencere bir sonraki olayın minimumunu yakalıyor; kesme olmadan sınıflar yanlış.
4. **Şok eşikleri Knipp'ten sıkı** (6 Eki): %20 / 20 km/s OMNI'de çok aday veriyor; 40 km/s ve 1,3 kat seçildi. Dört olayda ayar; bağımsız doğrulama yok.

## Henüz yok (sıradaki işler)

| # | Parça | Neden |
| --- | --- | --- |
| 1 | ~~Öznitelik kurucuya indeks girdileri~~ | 6 Eki akşam: yapıldı (`06`); 37 + 8 + 6 öznitelik |
| 2 | Katalog kurucuyu 2001-2015 yıllık OMNI ile koşmak, sınıf sayımını 90/78/28/14/7 ile karşılaştırmak, kapsam tablosu | OMNI yıllık indirmesi (yaklaşık 1,5 GB) onayını bekliyor |
| 3 | ~~ACE gecikmeli Bz'yi OMNI ile karşılaştırmak~~ | 6 Eki akşam: yapıldı (`02`): r = 0,73, en iyi ek gecikme +7 dk, tek gün |
| 4 | Başlangıç kuralının bağımsız doğrulaması (10 rastgele zayıf/orta fırtına, elle) | Beş olay ayar; doğrulama değil |
| 5 | Şok adaylarının R&C dışı olanlarına elle bakmak; CfA şok listesiyle karşılaştırma | Yanlış pozitif oranı bilinmiyor |
| 6 | DTCFILE birimi için birincil belge; saat eşlemesi pyatmos ile çapraz kontrol edildi (`02`) | Birim (K) hâlâ ikincil |
| 7 | ~~Bant bölütleme~~ 6 Eki gece: `analysis/passes.py` yazıldı (`04`). Kalan: referans yoğunluk sütunu (NRLMSIS ap=4) izin üstüne eklenmesi; Sidera köprüsüyle yapılabilir | Tez hattının ilk uçtan uca koşusu |
| 9 | JB2008 adaptörü: pyatmos kernel'i (`JB2008_subfunc.JB2008`, numba) girdilerimizle çağrılabilir; paket içe aktarması IERS indiriyor | Çevrimdışı kip ya da kernel'i ayırma kararı |
| 8 | R&C ek harflerinin anlamı (katalog web sayfası) | `*_note` alanları yorumlanmıyor |

## Sidera'ya taşıma planı

Ayrıntılı karar, yüzey ve taşıma günü adımları `12_sidera_entegrasyon_tasarimi.md` içinde; aşağıdaki tablo özet (yollar eski adlarla, eşleme `12`'de güncel):

| Bu paket | Sidera'da | Gerekçe |
| --- | --- | --- |
| `io/hapi.py`, `indices/gfz.py`, `indices/kyoto.py`, `indices/set_jb2008.py`, `indices/weimer_heating.py`, `solar_wind/omni.py`, `solar_wind/ace.py` (okuyucu kısmı), `solar/cycle.py` (okuyucular), `density/toleos.py` | `sidera.io.space_weather` | Okuyucular `io` katmanında; `physics`'in altında |
| `indices/conventions.py`, `indices/provider.py`, `set_jb2008.jb2008_solar_inputs` | `sidera.physics.atmosphere.space_weather` içine | Mevcut `SpaceWeatherState` ile birleşir; JB2008 girdileri ileride bir JB2008 atmosferine gider |
| `solar_wind/coupling.py`, `memory.py`, `shock.py`, `ace.ballistic_delay_s` | Yeni: `sidera.physics.space_environment` | Sidera'da karşılığı yok |
| `storms/`, `features/`, `solar/cycle.py` (evre kuralı) | `sidera.analysis.space_environment` ya da tez paketinde kalır | Analiz katmanı; yayılımın girdisi değil |

Taşıma günü yapılacaklar (Sidera'nın "bitti" tanımından):

1. `lint-imports`: yeni alt paket için içe aktarma sözleşmesi ve `docs/ARCHITECTURE.md` güncellemesi.
2. Algoritma kaydı: birleşme elektrik alanı, Newell fonksiyonu, üstel hafıza integrali, fırtına sınıfları, başlangıç kuralı, şok kuralı, JB2008 gecikmeleri, çevrim evresi. Her biri **doğrulanmış birincil kaynakla**; Newell 2007 ve JB2008 belgesi o güne kadar okunmuş olmalı.
3. `mypy` kapsam listesine ekleme; genel yüzey değiştiği için API envanteri.
4. Test işaretleri: `requires_data` düzeni Sidera'nınkiyle birleştirilir; xlsx (82 kB) ve Kyoto CSV (40 kB) depoda kalabilir, OMNI kesiti (1,3 MB) bir güne indirilebilir.
5. Sidera'nın yasaklı sözcük ve terminoloji testleri taşınan dosyalarda koşulmalı.
6. Hata sınıfları: Sidera alan hatalarını `SideraError` + yerleşik sınıftan türetiyor; burada düz `ValueError` var.
7. pandas: okuyucular ve öznitelik kurucu pandas kullanıyor. `physics` katmanında kullanımı deponun alışkanlığına uygun mu, bak.
8. İsteğe bağlı bağımlılıklar (openpyxl, cdflib, h5py) Sidera'nın `extras` düzenine girer.

Taşımadan önce beklemeye değer: modül tezin ilk üç haftasında (katalog ve öznitelik kurucu gerçek yük altında) denenecek; arayüzler o zaman oturur.

## Nasıl çalıştırılır

Proje ortamında:

```bash
"D:/Masaustu/Polar Precursor/.venv/Scripts/python.exe" -m pytest "D:/Masaustu/Polar Precursor/tests" -q
```

Sidera köprüsü dahil (Sidera ortamında):

```bash
PYTHONPATH="D:/Masaustu/Polar Precursor/src" "D:/sidera/.venv/Scripts/python.exe" -m pytest "D:/Masaustu/Polar Precursor/tests" -q -p no:randomly
```

Kanıt betiği (gerçek veri, tüm yeni parçalar):

```bash
"D:/Masaustu/Polar Precursor/.venv/Scripts/python.exe" "D:/Masaustu/Polar Precursor/plans/kanit/space_environment_genisletme.py"
```

Kullanım örneği:

```python
import pandas as pd
from space_environment.solar_wind.omni import read_omni_hro
from space_environment.solar_wind.shock import detect_shocks
from space_environment.storms.catalog import read_richardson_cane, build_storm_catalog
from space_environment.features.drivers import DriverFeatureBuilder

omni = read_omni_hro("data/raw/omni/omni_min2003.asc")
icmes = read_richardson_cane("data/raw/catalog/icmetable2.xlsx").between(2003, 2003)
catalog = build_storm_catalog(icmes, omni)                 # olay başına min SYM-H, sınıf, epok, küme
builder = DriverFeatureBuilder(omni, shocks=detect_shocks(omni))
features = builder.table(pd.date_range("2003-10-28", "2003-10-31", freq="10min", tz="UTC"))
```

## Sınırlar

- GFZ tam dosyası indirildi ama okuyucu tam dosyada koşulmadı (1932-1946 eksik F10.7 satırları, dosya sonu anlık değerler).
- OMNI 5 dakikalık biçim yalnız alan sayısıyla sınandı.
- Köprü testi tek nokta ve tek an; yayılım içinde kullanılmadı.
- ACE gecikmesi OMNI ile karşılaştırılmadı; balistik yöntem OMNI'nin faz cephesi yönteminden kaba.
- Şok kuralı ve başlangıç kuralı az olayda ayarlandı; bağımsız doğrulama yok.
- DTCFILE birimi ve saat eşlemesi; R&C ek harfleri; Newell 2007 aslı: doğrulanmadı.
- Isıtma serisinde `OKFLAG=1` olan dönemler OMNI'nin boş olduğu günleri de kapsıyor (Halloween'de %100 ok); yazarlar başka bir IMF kaynağı kullanmış olmalı (çıkarım, doğrulanmadı).
