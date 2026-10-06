# 00 — Genel bakış ve iş sırası

Hazırlanma: 5 Ekim 2026. Ana plan: `../00_ana_plan.md` (İndirilenler klasöründeki dosyanın birebir kopyası).

## Bu klasördeki planlar

| Dosya | Konu |
| --- | --- |
| `01_yogunluk_verisi.md` | CHAMP ve GRACE yoğunluğu: kaynak, biçim, hacim, kalite, indirme adımları |
| `02_gunes_ruzgari_ve_indeksler.md` | OMNI, Kp/ap/Hp30, Dst/SYM-H, F10.7, JB2008 indeksleri, güneş çevrimi, gerçek zamanlı karşılıklar |
| `03_atmosfer_modeli.md` | Referans model (NRLMSIS 2.1, ap = 4), ölçümler, JB2008 seçenekleri |
| `04_koordinat_ve_gecis_bolutleme.md` | Quasi-dipole koordinat, bantlar, geçiş bölütleme, örnek kurma, hedef değişken |
| `05_firtina_katalogu.md` | Richardson-Cane, şiddet sınıfları, sıfır epok kuralı, doğrulama seti |
| `06_surucu_oznitelikleri.md` | Bağlaşım fonksiyonları, hafıza terimleri, öznitelik tablosu, Poynting akısı |
| `07_istatistik_pilot_ve_kapi.md` | Ön kayıt kararları, çapraz doğrulama, güç, pilot, kapı |
| `08_yorunge_etkisi_sidera.md` | Yoğunluk hatasından konum hatasına, Sidera'nın durumu, yayılım protokolü |
| `09_literatur.md` | Yenilik durumu, okuma listesi, yakın çalışmalar |
| `10_sidera_hazirlik_analizi.md` | Sidera'da ne hazır, ne eksik, hangi tuzaklar var |
| `11_space_environment_modulu.md` | Güneş ve jeomanyetik etkinlik modülü: tasarım, durum, Sidera'ya taşıma planı |
| `15_on_kayit_taslagi.md` | Ön kayıt belgesi taslağı: hipotezler, 17 karar maddesi (öneri + ölçülmüş gerekçe), kapı kuralı; kararlar sana ait |
| `14_pilot_2001_2005.md` | 1. kademe veri indirmesi (OMNI 2001-2005, CHAMP pencere günleri), pilotun iki koşusu, merdiven tanısı ve kapı okuması |
| `13_deney_katmani.md` | `polar_precursor` paketi: merdiven B0-M, fırtına gruplu iç içe ÇD, küme bootstrap, permütasyon, sentetik iskelet; ölçülen iskelet sonuçları |
| `12_sidera_entegrasyon_tasarimi.md` | Sidera'ya güneş aktivitesi bölümü: karar (evet), hedef yerleşim, genel yüzey, kayıt ve veri taslakları, taşıma adımları |
| `kanit/` | Bu oturumda koşulan kontrol betiği ve çıktısı |

Her belgede iddialar etiketli: bu makinede ölçülen, kaynağı açılıp okunan, yalnız özeti okunan, doğrulanamayan.

**Araştırmanın sınırı.** Web kaynaklarını beş araştırma ajanı okudu; çoğu sayfa özetleyici bir okuyucudan geçti. Sayıları teze almadan önce asıl kaynaktan kontrol et. Wiley (AGU dergileri) ve ScienceDirect otomatik erişimi reddetti; o makaleler yalnız özet düzeyinde. TU Delft'in canlı sunucusuna ulaşılamadı.

## Ana planı değiştiren on bulgu

1. **Yoğunluk verisi ESA'dan alınacak.** Aynı V2 ürünü, girişsiz, bayrak anlamı belgeli (0 = iyi); toplam yaklaşık 7,1 GB. TU Delft ASCII biçimi hâlâ bilinmiyor. (`01`)
2. **Zenodo 4602380 ana veri olamaz.** Farklı yoğunluk ürünü, 2001 ve 2011-2015 yok, yalnız GRACE-A. (`01`)
3. **"ap = 4" ile jeomanyetik anahtarı kapatmak aynı yoğunluğu veriyor**; MSIS 2.0 ve 2.1 400 km'de aynı; hız yaklaşık 16.000 nokta/s. Bu makinede ölçüldü. (`03`)
4. **apexpy ve aacgmv2 için Windows tekerleği yok**, ama apexpy bu makinede derlendi ve çalışıyor (tarif `04` içinde; hız yaklaşık 534.000 nokta/s). Risk kapandı. (`04`)
5. **Fırtına listesi yayınlanmamış, sıfır epok elle seçilmiş, 217'nin 90'ı zayıf sınıf.** Katalog bugün 334 ICME satırı veriyor; 217 birebir üretilemeyebilir. Yayınlanmış tek başlangıç zamanları yedi aşırı fırtına. (`05`)
6. **168 sayısı bildirinin sayısı; JGR makalesi 159 diyor.** (`05`)
7. **Kendi geçmişini girdi yapan bir tahmin modeli 2026'da yayınlanmış** (Zhang ve ark.). Yazarların kodu okundu: gelecekteki ap'yi de girdi alıyor, güneş rüzgarı yok, kronolojik bölme, 24 saat ufuk. H4 daraldı ama duruyor: 1-4 saat, yalnız geçmiş sürücüler, fırtına gruplu doğrulama, sürücü-yalnız tabana göre artış. AETHER-P3 ise ölçülmüş yoğunluğu girdi almıyor (tam metin okundu). (`09`)
8. **Gerçek zamanlı SYM-H yok.** A katmanı tanımı gözden geçirilmeli. (`02`)
9. **W05 Poynting akısı ve ΔT serisi hazır olarak Zenodo'da** (2000-2019). Açık kaynak W05 kodu yok, ama gerek de yok. (`06`)
10. **Konum hatası formülü kaynaklı hale geldi** (Emmert 2014, Denk. 3-5) ve **Sidera'da MSIS var, JB2008 yok, keyfi yoğunluk için arayüz var**. (`08`)

## İkinci tur (5 Eki 2026, sonradan): ölçülen ve kapanan noktalar

- **Gerçek CHAMP verisi çekildi** (VirES HAPI, jetonsuz): biçim ve birimler belgedekiyle aynı. (`01`)
- **CHAMP'te 1 Mar - 6 Tem 2005 arası 128 günlük boşluk var**; 15 May 2005 aşırı fırtınası bu boşlukta. (`01`, `05`)
- **Geçerli kayıt oranı** veri olan günlerde çoğunlukla %98 üstü; tek tük yarı boş günler var. (`01`)
- **"ap = 4 ≡ anahtar kapalı" gerçek izde de tam tutuyor**; güneş minimumunda MSIS 2.1 gözlemin yaklaşık 1,4 katı (tek gün). (`03`)
- **29 Eki 2003 önizlemesi**: kutup bir geçişte yaklaşık +0,65 sıçrıyor, gece tarafı alçak enlem aynı düzeye yaklaşık 2,6 saat sonra çıkıyor. Tek olay; hipotezi sınamaz, hattın çalıştığını gösterir. (`01`)
- **apexpy kuruldu**; tarif ve hız `04` içinde.
- **MSIS 2.0 uydurmasında ivmeölçer verisi yok**; referans ile hedef arasında döngüsellik yok. (`03`)
- **Weimer ısınma modeli parametreleri ve hazır ısıtma serisi** (4 dakikalık, 2000-2019) doğrulandı. (`06`)
- **TU Delft sunucusuna yine ulaşılamadı** (zaman aşımı).

## Üçüncü tur (5 Eki 2026): Sidera incelemesi ve modülün ilk sürümü

- **Sidera yayılım tarafını karşılıyor, veri ve bilim tarafını karşılamıyor.** Keyfi atmosfer nesnesiyle sürüklenme, iz boyunca ayrıştırma, zaman ölçekleri hazır; yoğunluk okuma, güneş rüzgarı, manyetik enlem, ölçülmüş yoğunluk modeli, koşu başına atmosferle toplu çalıştırma yok. (`10`)
- **Üç tuzak:** zaman ölçeği sabiti 2017 öncesi için yanlış (2003'te 5 s); balistik katsayı tanımı ters; Dünya dönüşü sadeleştirilmiş. (`10`)
- **`space_environment` paketi yazıldı** (`../src/`): GFZ ve OMNI okuyucuları, NRLMSIS indeks kuralları, sakin referans kipi, bağlaşım fonksiyonları, hafıza öznitelikleri, fırtına sınıfı, başlangıç kuralı, Sidera köprüsü. 40 test geçti (Sidera ortamında, köprü dahil); ruff ve mypy temiz. (`11`)
- **Sidera'da bir boşluk kapandı:** fırtına kipinde NRLMSIS artık gerçek GFZ indeksleriyle sürülebiliyor (Sidera'nın kendi sağlayıcısı Ap geçmişini doldurmuyordu). (`10`, `11`)
- **OMNI en büyük fırtınada boş:** 29 Eki 2003 05:50-18:42 ve 30 Eki boyunca güneş rüzgarı verisi yok. Sürücü öznitelikleri ve epok kuralı bu olaylarda OMNI ile çalışmıyor. (`02`, `05`, `06`, `07`)
- **ESA'dan dosya indirme girişsiz çalışıyor**; CDF açıldı. (`01`)

## Dördüncü tur (6 Eki 2026)

- **Epok kuralı yayınlanmış zamanlarla ayarlandı:** OMNI'de verisi olan beş olayın beşinde 7 dakika içinde; göreli derinlik parametresi bu beş olayda seçildi (ayarlama, doğrulama değil). Yedi aşırı fırtınanın üçünde OMNI'de başlangıç anı boş. (`05`)
- **Sidera'da tek koşu:** kullanıcı tanımlı atmosfer sınıfı çalışıyor; 4 saatlik koşu 0,3 s; iz boyunca fark 4 saatte 34,1 m, formül 34,95 m. Daha yoğun atmosferdeki uydu ileride. (`08`, `10`)
- **Ürün tanım belgesi okundu:** belirsizlik "yörünge ortalaması varyansının %30'u ya da 5×10⁻¹⁴ kg/m³, hangisi büyükse". (`01`)
- İndirilenler: GFZ tam dosyası, Richardson-Cane xlsx (sürüm 5.1, özet doğrulandı), beş aylık OMNI dosyası. Hepsi `../data/raw/`.
- Modül: 42 test geçiyor; ruff ve mypy temiz.

## Beşinci tur (6 Eki 2026): modül genişletmesi

Hedef: `space_environment` modülünü Sidera'ya paralel büyütmek. Eklenenler (hepsi gerçek veriyle sınandı; ayrıntı `11`, sayılar `kanit/space_environment_genisletme_cikti_2026-10-06.txt`):

- **ACE yedeği ölçüldü:** OMNI'nin boş olduğu 29-30 Eki 2003'te ACE manyetik alan (MFI, 16 s) **%100** dolu; ACE plazma (SWEPAM) **%0**. Yedek alanı geri getiriyor, hızı ve yoğunluğu getirmiyor. (`02`)
- **Fırtına kataloğu kurucu:** Richardson-Cane xlsx okuyucu (644 olay, 2001-2015'te tam 334) ve OMNI'den en düşük SYM-H, sınıf, epok, sürücü kapsamı, küme kimliği üreten kurucu. Pencere bir sonraki rahatsızlıkta kesiliyor; yoksa 28-30 Ekim'in üç olayı aynı minimumu alıyordu. (`05`)
- **Şok bayrağı:** hız, |B| ve yoğunluk basamağı kuralı; dört R&C şokunda 3-10 dk içinde, 15 May 2005 ve 6 Kas 2001'de kaçırıyor (OMNI plazma boşluğu). (`06`)
- **Öznitelik kurucu:** tahmin anı için 32 sürücü özniteliği; `t0` sonrası veriyi bozunca hiçbir öznitelik değişmiyor (sızıntı testi); 235 satır/s. (`06`)
- **Yeni okuyucular:** Kyoto Dst (HAPI), ACE (HAPI), SET SOLFSMY/DTCFILE ve JB2008 gecikme kuralı, Zenodo 7667515 ısıtma/ΔT serisi (4 dk, 2000-2019), SILSO güneş lekesi ve çevrim tablosu, ESA CDF yoğunluk ürünü.
- İndirilenler: SET (2 MB), Zenodo ısıtma (58 MB), Kyoto Dst Ekim-Kasım 2003, ACE 28-30 Eki 2003, SILSO (3 dosya). Hepsi `../data/raw/`.
- Testler: proje ortamında **74 geçti**, 1 atlandı; Sidera ortamında (Python 3.10) 71 geçti, 5 atlandı (openpyxl/cdflib yok). ruff ve mypy temiz.

## Altıncı tur (6 Eki 2026): Sidera entegrasyon tasarımı ve katman düzeni

Soru: Sidera'ya güneş aktivitesi bölümü eklenmeli mi? **Evet**; gerekçe ve tasarım `12`. Özet:

- Sidera'nın kendi kodu okunarak dört boşluk saptandı: okuyucu `physics`'te ("indices are data" ilkesine karşı), `ap_history` hiçbir yolda dolmuyor (fırtına kipi gerçek veriyle çalışmıyor), JB2008 yolu yok, katman yığını yeni sözleşme gerektirmiyor.
- **Paket Sidera katman düzenine taşındı:** `common/`, `io/`, `physics/`, `analysis/`, `integration/`; kendi `lint-imports` sözleşmesi **KEPT**. Taşıma kopyalama olacak.
- **Örnek Sidera ortamında koştu:** 29 Eki 2003 CHAMP izinde NRLMSIS 2.1 fırtına kipi / sakin referans 1,56-1,63; gözlem / fırtına kipi **0,74-0,81** (NRLMSIS o gün %20-25 fazla). `kanit/ornek_firtina_sakin_nrlmsis_cikti_2026-10-06.txt`.
- Taslaklar: `../sidera_merge/` altında algoritma kaydı (8 giriş, dürüst doğrulama durumlarıyla), bib ve veri kataloğu girişleri. Sidera deposuna dokunulmadı.
- Denetimler: 74 test (proje), 71 test (Sidera ortamı), ruff, mypy, lint-imports temiz.
- Akşam eki (Sidera belgeleri sana kalırken): **ACE gecikmesi ölçüldü** (28 Eki 2003: kaydırılmış ACE Bz ile OMNI r = 0,73, ek gecikme +7 dk; `02`); **indeks ve geometri öznitelikleri** yazıldı (A katmanı 37 + 8 + 6 = 51, aralık bitmeden kullanılmaz; `06`); **sakin sarmalayıcı** `QuietGeomagneticProvider` (`12`). Testler 79 (proje) / 76 (Sidera ortamı); tüm kapılar temiz (`kanit/space_environment_testler_2026-10-06c.txt`).
- Gece eki: **geçiş bölütleme ve örnek kurucu** yazıldı; gerçek CHAMP gününde 31 alçak / 16+16 kutup parça, 46 dk aralık, sızıntı sıfır (`04`). **apexpy proje ortamına kuruldu**, QD enlem ve MLT iz üstüne ekleniyor. **JB2008 girdileri pyatmos ile birebir doğrulandı**; DTC saat eşlemesi ikincil kaynakla kapandı (`02`). **OMNI 5 dk** gerçek yıllık dosyayla sınandı. Testler 91 (proje) / 87 (Sidera ortamı), tüm kapılar temiz (`kanit/space_environment_testler_2026-10-06d.txt`).
- Öğle eki: **deney katmanı yazıldı** (`src/polar_precursor/`, `13`): merdiven B0 B1 B2 D B3 B3k B3t M (kapalı biçim ridge), epok sıralı fırtına gruplu iç içe ÇD + 57 sa tampon reddi, fırtına başına MSE / beceri / tepe hataları, küme bootstrap, sınıf × öngörü kutusu tabakalı permütasyon, güç, sentetik fırtına üreteci, uçtan uca `run_experiment`, koşu kaydı. Ön kayıt düğmeleri `configs/pilot.toml` (plan 07 önerileri; karar değil). **Sentetik iskelet testi (plan 07) koşuldu:** sıfır durumunda aralık sıfırı yalnız eksi tarafta dışlıyor (iç içe model cezası), artı tarafta değil; ölçüt H1 yönünde tek yönlü yazıldı; sayılar `kanit/iskelet_testi_cikti_2026-10-06.txt` ve `kanit/permutasyon_sentetik_kaniti_cikti_2026-10-06.txt`. Depo eklentileri: `uv.lock`, `.github/workflows/ci.yml`, `data/README.md`, `results/README.md`. Testler **111** (proje), tüm kapılar temiz (`kanit/space_environment_testler_2026-10-06f.txt`).
- Öğleden sonra eki: **referans yoğunluk** (`analysis/reference_density.py`, pymsis vektörel, Ap = 4; adım hatası ölçüldü) ve **`CombinedDrivers`** yazıldı; **uçtan uca gerçek veri hattı** 29 Eki 2003'te koşuldu: CDF → QD → referans → 125 parça → 138 örnek → fırtına tablosu → 138 × 120 tasarım matrisi + manifest, 8 s (`13`, `kanit/uctan_uca_2003_10_29_cikti.txt`). C: diski doldu, `%TEMP%` temizlendi. Testler **114**, kapılar temiz (`kanit/space_environment_testler_2026-10-06g.txt`).
- Akşam eki: **ikincil analizler** (H4, kontroller, öngörü kutusu başına Holm, sınıf başına d_s), **kapı raporu** üreteci ve **fırtına penceresi veri seti kurucu** (günlük CDF'ler → tasarım, parquet önbellek, kapsam tablosu) yazıldı (`13`). Pilot artık veri gelince tek komutla koşar. Testler **120**, kapılar temiz (`kanit/space_environment_testler_2026-10-06h.txt`).
- Gece eki: **1. kademe veri indi** (OMNI 2001-2005, CHAMP pencere günleri 403 dosya, Hp30, Dst; `14`) ve **pilot koşuldu** (30 küme, 20 525 örnek). İlk koşu bir tasarım hatası yakaladı (sektör karışımı: B2 kalıcılıktan kötüydü), ikinci koşu bir merdiven hatası (LOW öneki); üçüncü koşu: **M vs B3 +6,0 % [+3,3, +9,9], fırtınaların %90'ında iyileşme, permütasyon p = 0,001; M vs B3t +2,9 % [+0,8, +5,8]; H4 +56 %; kazanç 105-270 dk kutularında, ilk saatte yok.** Kapı: devam, B3t sınırda (soru keskinleşiyor: kutba özgü mü, tazelik mi). **Koşu 4 (B3t ikinci tanımı):** daha taze orta enlem ölçümü daha az yararlı (M vs B3t2 +3,6 %); tazelik tek başına açıklamıyor. **2. kademe veri:** OMNI 2006-2015 (10 yıl, doğrulandı), GRACE-A 2002-2005 pencereleri (263 dosya), CHAMP 2006-2010 (128 dosya); GRACE-A 2006-2015 iniyor. Ön kayıt taslağı `15`. Statü keşif; ön kayıt sonrası ana analiz belirler. Testler **121**, kapılar temiz (`kanit/space_environment_testler_2026-10-06j.txt`).

## Senden karar bekleyenler

| # | Karar | Öneri | Belge |
| --- | --- | --- | --- |
| 1 | Birincil testte zayıf sınıf fırtınalar | Dışarıda; birincil test SYM-H < −50 nT | `07` |
| 2 | A katmanında SYM-H | Çıkar; ap30 + saatlik Dst | `02` |
| 3 | Oliveira ve Zesta'dan fırtına listesini istemek | İste; kısa e-posta | `05` |
| 4 | GRACE-B | Kullanma | `01` |
| 5 | Pilot seçimi | Orantılı yerine tabakalı (6/10/8/4/2) | `07` |
| 6 | Bandın dışındaki yoğunluk (yörünge koşuları) | İvmeölçer yoğunluğu | `08` |
| 7 | Sürücüsüz fırtına örnekleri (OMNI boşluğu) | Ayrı ikincil analiz; birincil test sürücüsü olan örneklerle | `07` |
| 8 | Modülün Sidera'daki yeri | `io` + `physics.atmosphere` + yeni `physics.space_environment` | `11` |

## Çalışma ortamı

Bu makinede okunanlar (5 Eki 2026):

- C diski 12,4 GB boş, D diski 380,5 GB boş. **Veri, önbellek ve sanal ortam D'de olacak.**
- Sistem Python 3.12.1; `uv` 0.11.28; `D:\uv_cache` mevcut.
- `D:\sidera\.venv`: Python 3.10.20, pymsis 0.13.0, numpy 2.2.6, pandas 2.3.3, scipy 1.15.3. scikit-learn ve cdflib kurulu değil.
- gfortran: `C:\Strawberry\c\bin\gfortran.exe`. WSL dağıtımı: yalnız `docker-desktop`.

Önerilen düzen:

```
D:\Masaustu\Polar Precursor\
  00_ana_plan.md
  plans\
  data\raw\{density,omni,gfz,set,kyoto,catalog}\
  data\interim\        (parquet: yoğunluk, koordinat, referans, geçişler)
  data\features\
  src\ , tests\ , notebooks\
  outputs\             (kapı raporu, şekiller)
  .venv\
```

- Proje için ayrı sanal ortam (Sidera'nınkini değiştirme). Python 3.10-3.12; Sidera'yı düzenlenebilir bağımlılık olarak ekle.
- Paketler: pymsis, cdflib, pyspedas, scikit-learn, pandas, pyarrow, numpy, scipy, matplotlib, openpyxl; apexpy ayrı (bkz. `04`).
- Ortam değişkenleri: `SPEDAS_DATA_DIR` → `data\raw\omni`; `UV_CACHE_DIR` → `D:\uv_cache`.
- pymsis indeksleri hiç otomatik indirmesin: F10.7 ve ap her çağrıda açıkça verilir.
- Git deposu aç; `data\` izlenmez, bildirim dosyaları (ad, boyut, SHA-256, kaynak, tarih) izlenir.

## İş sırası

**Ocak öncesi (toplam 3-4 gün)**

| # | İş | Süre | Belge |
| --- | --- | --- | --- |
| 1 | Ortam kurulumu; apexpy'yi çalıştır (Windows derleme ya da Docker) | yarım gün | `04` |
| 2 | Tek CHAMP günü indir, CDF'i aç, HAPI ile karşılaştır; TOLEOS belgesini oku | 1 saat | `01` |
| 3 | Gerçek izde "ap = 4 ≡ anahtar kapalı" tekrarı | yarım saat | `03` |
| 4 | Okuma: Zhang 2026, AETHER-P3, Wang 2022/2023, Oliveira 2017 JGR + ek, Weimer 2023 | 2 gün | `09` |
| 5 | Sidera'da sabit yoğunluklu sınama: `δs = (3/2)·a·ε·t²` | yarım gün | `08` |
| 6 | Ön kayıt sayfası; danışmana gönder | yarım gün | `07` |
| 7 | Oliveira/Zesta'ya e-posta (karar 3) | — | `05` |

**Hafta 1 (18 Oca)** — indirme (CHAMP 2001-2005, OMNI, GFZ, katalog); CDF → parquet; koordinat; geçiş bölütleme. Çıktı: `passes.parquet`, kapsam raporu.

**Hafta 2 (25 Oca)** — referans yoğunluk; katalog ve sıfır epok kuralı (yedi aşırı fırtınayla doğrulama); `b_s`; normalize seriler. Çıktı: `katalog.parquet`, gerçek fırtına sayısı G.

**Hafta 3 (1 Şub)** — hat doğrulaması (üst üste bindirilmiş epok); 30 fırtınalık pilot; kapı raporu. **Kapı: 7 Şubat.**

**Hafta 4-13** — ana plandaki takvim. Kalan veri (GRACE, CHAMP 2006-2010) kapı kararından sonra indirilir. İskelet sentetik testi hafta 4'te (`07`); Poynting akısı ve ΔT hafta 8'de (`06`); yörünge protokolü hafta 12'de (`08`).

## Doğrulanamayan ve elle bakılacaklar (toplu)

- TU Delft ASCII biçimi; ESA'dan gerçek dosya indirmenin girişsiz çalıştığı.
- CHAMP 2005 boşluğunun nedeni.
- Wiley ve ScienceDirect tam metinleri: Newell 2007, Emmert 2017/2021/2022, Oliveira 2017 JGR, Wang 2022/2023, Zhang 2026, Sutton 2009, Bruinsma ve Forbes, Weimer 2020, Hejduk ve Snow 2018.
- Zenodo 7667515 (Weimer 2023 arşivi) içeriği.
- apexpy'nin bu makinede kurulabildiği ve hızı.
- Sidera tümleyicisinin protokol sınıfını uçtan uca çalıştırdığı.
- SpaceX FCC raporundaki manevra sayıları; Starlink düşük sürüklenme alanı.
- İstatistik kaynaklarının tam metinleri (bu oturumda yeniden açılmadı).
