# Polar Precursor

Yüksek enlem termosfer yoğunluğu, alçak enlem yoğunluğunu 1-4 saat önceden
kestirmeye güneş rüzgarı sürücülerinin ve kendi geçmişinin ötesinde katkı
veriyor mu? CHAMP ve GRACE ivmeölçer yoğunlukları, 2001-2015 CME fırtınaları.
Bu depo tezin araştırma planlarını, kanıt betiklerini ve `space_environment`
paketini tutar.

## Durum (6 Ekim 2026)

- Veri erişimi doğrulandı (ESA/TU Delft CDF, OMNI, GFZ, Kyoto, SET, SILSO,
  Richardson-Cane); okuyucular gerçek veri kesitleriyle test ediliyor.
- Referans model tanımı ölçüldü: NRLMSIS 2.1, her Ap diliminde 4.
- Fırtına kataloğu kurucu, şok ve epok kuralları, sürücü/indeks/geometri
  öznitelikleri, geçiş bölütleme ve örnek kurucu yazıldı; hepsi 29 Ekim 2003
  CHAMP günü üzerinde sınandı.
- Deney katmanı yazıldı (`polar_precursor`): model merdiveni B0-M (ridge),
  fırtına gruplu iç içe çapraz doğrulama, küme bootstrap, tabakalı permütasyon,
  güç; sentetik iskelet testi plan 07'deki iki ölçütle koşuldu
  (`plans/kanit/iskelet_testi_cikti_2026-10-06.txt`).
- Gerçek veri hattı uçtan uca çalışıyor: CDF → QD → sakin NRLMSIS referansı →
  parçalar → örnekler → fırtına tablosu → tasarım matrisi ve koşu kaydı, 29 Ekim
  2003 gününde ölçüldü (`plans/kanit/uctan_uca_2003_10_29_cikti.txt`).
- Henüz yok: 2001-2015 tam veri koşusu, gerçek veride pilot, ön kayıt belgesi,
  tez metni. Durum ve kararlar: [`plans/00_genel_bakis.md`](plans/00_genel_bakis.md).

## Yapı

```
00_ana_plan.md         Tez araştırma planı (kaynak belge)
plans/                 00-13 numaralı tasarım, durum ve karar belgeleri
plans/kanit/           Ölçüm betikleri ve çıktıları; plandaki her sayının kaynağı
configs/               Deney yapılandırmaları (ön kayıt düğmeleri; pilot.toml)
src/space_environment/ Güneş ve jeomanyetik etkinlik paketi (aşağıda; Sidera'ya gidecek)
src/polar_precursor/   Tez hattı: merdiven, doğrulama, istatistik, sentetik, deney (plans/13)
tests/                 Gerçek veri kesitleri ve sentetik veriyle testler (tests/fixtures)
examples/              Sidera ortamında koşan örnek
sidera_merge/          Sidera'ya taşıma için kayıt, kaynakça ve veri kataloğu taslakları
data/                  Ham ve türetilmiş veri (depoda yok; data/README.md yerleşimi anlatır)
results/               Koşu çıktıları (depoda yok; results/README.md içeriği anlatır)
```

`space_environment` paketi Sidera'nın katman düzenini taşır ve
`lint-imports` ile korunur (`analysis | integration` → `physics` → `io` → `common`):

| Paket | İçerik | Sidera hedefi |
| --- | --- | --- |
| `io` | GFZ, OMNI (1 ve 5 dk), HAPI (Kyoto Dst, ACE), SET SOLFSMY/DTCFILE, Zenodo ısıtma, SILSO, ESA CDF yoğunluk okuyucuları | `sidera.io.space_weather` |
| `physics` | NRLMSIS indeks kuralları ve sağlayıcılar (ölçülen, sakin), JB2008 girdileri, bağlaşım fonksiyonları, hafıza integrali, şok ve fırtına kuralları, L1 gecikmesi, QD koordinatlar | `sidera.physics.atmosphere.space_weather`, `sidera.physics.space_environment` |
| `analysis` | Richardson-Cane kataloğu ve fırtına tablosu, öznitelik kurucular, geçiş bölütleme ve örnekler, güneş çevrimi bağlamı | `sidera.analysis.space_environment` |
| `integration` | Sidera `SpaceWeatherProvider` köprüsü | taşımada kalkar |

Tasarım ilkeleri: ağdan veri çekilmez, her dosya SHA-256 ile kaydedilir;
eksik değer doldurulmaz; birim ve çerçeve adın içindedir; tahmin anından
sonraki veri hiçbir özniteliğe sızmaz (test edilir). Ayrıntı:
[`plans/11_space_environment_modulu.md`](plans/11_space_environment_modulu.md),
Sidera entegrasyonu: [`plans/12_sidera_entegrasyon_tasarimi.md`](plans/12_sidera_entegrasyon_tasarimi.md).

`polar_precursor` paketi tezin araştırma kodudur ve `space_environment`'ın
üstünde durur (ters bağımlılık `lint-imports` ile yasak):

| Paket | İçerik |
| --- | --- |
| `config` | Ön kayıt düğmeleri (`configs/pilot.toml`), yapılandırma özeti |
| `design` | Sütun sözleşmesi, merdiven B0 B1 B2 D B3 B3k B3t M, tasarım matrisi kurucu |
| `models`, `metrics` | Kapalı biçim ridge; artık, RMSE, korelasyon, beceri, fırtına başına kayıp, tepe hataları |
| `validation` | Fırtına gruplu, epok sıralı katlar; 57 saat tampon denetimi; iç içe çapraz doğrulama |
| `statistics` | Küme bootstrap (d_s, göreli RMSE azalması), tabakalı permütasyon, güç |
| `synthetic`, `experiment` | Bilinen kutup katkılı sentetik fırtınalar; uçtan uca koşu, iskelet testi, koşu kaydı |

Ayrıntı ve ölçülen iskelet sonuçları: [`plans/13_deney_katmani.md`](plans/13_deney_katmani.md).

## Kurulum

Python 3.10-3.12. Ortam `uv.lock` ile sabittir:

```bash
uv sync --locked --extra dev --extra catalog --extra density --extra heating --extra reference
```

`pip` ile de kurulur (`pip install -e ".[dev,catalog,density,heating]"`).

İsteğe bağlı ekler: `catalog` (openpyxl, Richardson-Cane xlsx), `density`
(cdflib, ESA CDF), `heating` (h5py, Zenodo arşivi), `reference` (pymsis, sakin
NRLMSIS referansı), `magnetic` (apexpy; Windows'ta kaynak derleme, tarif
`plans/04`). Çekirdek yalnız numpy ve pandas ister.

## Denetimler

```bash
.venv/Scripts/ruff.exe check src tests examples
.venv/Scripts/python.exe -m mypy
.venv/Scripts/lint-imports.exe
.venv/Scripts/python.exe -m pytest tests -q
```

Büyük ham dosyalara bağlı testler `requires_data` işaretlidir ve dosya yoksa
atlanır; Sidera köprüsü testleri Sidera kurulu değilse atlanır. Aynı dört kapı
`.github/workflows/ci.yml` ile her push'ta koşar. Son yerel koşu:
`plans/kanit/space_environment_testler_2026-10-06g.txt`.

Sentetik iskelet testi (plan 07; gerçek veride birincil test bundan önce koşulmaz):

```bash
PYTHONPATH=src .venv/Scripts/python.exe -m polar_precursor.experiment.skeleton --repeats 200 --out plans/kanit/iskelet_testi_cikti_2026-10-06.txt
```

## Veri

Ham veri depoda değildir (`data/` yok sayılır). Kaynaklar, adresler ve indirilen
dosyaların özetleri `plans/01` ve `plans/02` içinde; her indirmenin SHA-256'sı
kanıt çıktılarında kayıtlıdır. Testler için gereken kesitler `tests/fixtures/`
altındadır ve bayt-birebir korunur (`.gitattributes`).

## Sidera ile ilişki

Paket, [Sidera](https://github.com/ayberkdt/sidera) astrodinamik çerçevesine
paralel geliştiriliyor ve aynı kod kurallarıyla yazılıyor. Sidera'nın
NRLMSIS adaptörü fırtına kipini bugün gerçek veriyle süremiyor; bu paketin
GFZ sağlayıcısı o boşluğu kapatıyor (`examples/storm_vs_quiet_nrlmsis.py`,
29 Ekim 2003 CHAMP izinde ölçüm). Taşıma kararı ve adımları `plans/12`.
