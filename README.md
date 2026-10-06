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
- Henüz yok: 2001-2015 tam veri koşusu, pilot, modeller, istatistik, tez metni.
  Durum ve kararlar: [`plans/00_genel_bakis.md`](plans/00_genel_bakis.md).

## Yapı

```
00_ana_plan.md         Tez araştırma planı (kaynak belge)
plans/                 00-12 numaralı tasarım, durum ve karar belgeleri
plans/kanit/           Ölçüm betikleri ve çıktıları; plandaki her sayının kaynağı
src/space_environment/ Güneş ve jeomanyetik etkinlik paketi (aşağıda)
tests/                 Gerçek veri kesitleriyle testler (tests/fixtures)
examples/              Sidera ortamında koşan örnek
sidera_merge/          Sidera'ya taşıma için kayıt, kaynakça ve veri kataloğu taslakları
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

## Kurulum

Python 3.10-3.12. Depo `uv` ile kuruldu; `pip` de çalışır.

```bash
uv venv .venv --python 3.12
uv pip install --python .venv/Scripts/python.exe -e ".[dev,catalog,density,heating]"
```

İsteğe bağlı ekler: `catalog` (openpyxl, Richardson-Cane xlsx), `density`
(cdflib, ESA CDF), `heating` (h5py, Zenodo arşivi), `magnetic` (apexpy; Windows'ta
kaynak derleme, tarif `plans/04`). Çekirdek yalnız numpy ve pandas ister.

## Denetimler

```bash
.venv/Scripts/ruff.exe check src tests examples
.venv/Scripts/python.exe -m mypy
.venv/Scripts/lint-imports.exe
.venv/Scripts/python.exe -m pytest tests -q
```

Büyük ham dosyalara bağlı testler `requires_data` işaretlidir ve dosya yoksa
atlanır; Sidera köprüsü testleri Sidera kurulu değilse atlanır. Son koşu:
`plans/kanit/space_environment_testler_2026-10-06d.txt`.

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
