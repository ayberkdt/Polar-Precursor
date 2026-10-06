# 13 — Deney katmanı: `polar_precursor` paketi

Hazırlanma: 6 Ekim 2026. Ana plan: `../00_ana_plan.md` "Model merdiveni", "İstatistik tasarım"; `07_istatistik_pilot_ve_kapi.md`. Bu belge tezin araştırma kodunu (model merdiveni, fırtına gruplu doğrulama, birincil ve doğrulayıcı testler, sentetik iskelet) tanımlar. `space_environment` Sidera'ya gidecek altyapıdır; `polar_precursor` tezde kalır ve onu tüketir.

## Karar

Yeni bir üst paket: `src/polar_precursor/`. Gerekçe: deney kodu Sidera'ya taşınmayacak, `space_environment` katman yığınının üstünde durur ve ters yönde bağımlılık yasaktır (`lint-imports` sözleşmesi "space_environment does not depend on the thesis package", 6 Eki 2026 KEPT, `kanit/space_environment_testler_2026-10-06f.txt`).

Üçüncü taraf ML kütüphanesi yok: ridge kapalı biçimde numpy ile (`models/ridge.py`). Nedeni: katsayılar yorumlanabilir olmalı (ana plan "Model sınıfı" 1), permütasyon ve iskelet testleri binlerce yeniden uydurma ister, ve ortam `uv.lock` ile sabitlenirken bağımlılık yüzeyi küçük kalmalı. scikit-learn'ün `GroupKFold`'u yerine kendi kat ataması (aşağıda) yazıldı; nedeni plan 07'deki "katları epok sırasına dizip dönüşümlü ata" kuralı, `GroupKFold`'da yok.

## Yapı ve katmanlar

```
polar_precursor/
  config.py          ExperimentConfig: ön kayıt düğmeleri; configs/*.toml okuyucu; SHA-256 özet
  design/ladder.py   Sütun sözleşmesi; merdiven B0, B1, B2, D, B3, B3k, B3t, M (aile → sütun)
  design/matrix.py   build_samples çıktısı + parçalar + katalog + sürücüler → tasarım matrisi
  models/ridge.py    Standartlaştırma ve doldurma yalnız eğitim satırlarıyla; kapalı biçim ridge
  metrics/scores.py  Artık ortalama/SD, RMSE, korelasyon, beceri; fırtına başına MSE; tepe hataları
  validation/folds.py     Gruplu katlar (epok sırası, dönüşümlü); 57 saat tampon denetimi
  validation/crossval.py  İç içe gruplu ÇD; fırtına dışı tahminler; kat başına seçilen ceza
  statistics/bootstrap.py    Küme bootstrap (fırtına yerine koyarak); göreli RMSE azalması; d_s
  statistics/permutation.py  Kutup bloğunu sınıf × öngörü kutusu içinde karıştır, M'yi yeniden uydur
  statistics/power.py        2,8 × SD / √G
  synthetic.py       Bilinen kutup katkılı sentetik fırtınalar (aynı sütun sözleşmesi)
  experiment/pipeline.py  run_experiment: tampon → merdiven → ÇD → tablolar → bootstrap → permütasyon
  experiment/skeleton.py  Plan 07 iskelet testi (python -m polar_precursor.experiment.skeleton)
  experiment/manifest.py  Koşu kaydı: commit (+dirty), yapılandırma özeti, sürümler, veri SHA-256
  statistics/secondary.py İkincil karşılaştırmalar (H4, kontroller, merdiven adımları), öngörü kutusu
                          başına bootstrap + Holm, H2 betimi, sınıf başına d_s dağılımı
  experiment/report.py    Kapı raporu (Markdown): plan 07 "Kapı raporuna eklenecekler" tabloları
  experiment/dataset.py   Fırtına penceresi başına veri seti: günlük CDF'ler → iz → QD → referans →
                          parçalar → örnekler → tasarım; parquet önbellek; kapsam tablosu
  design/drivers.py       CombinedDrivers: OMNI + GFZ + Hp30 + Dst tek çağrıda, L1 boşluğunda NaN + bayrak
```

Katman sözleşmesi (`pyproject.toml`, `lint-imports` KEPT): `experiment → statistics → validation → models | metrics | synthetic → design → config`.

## Sütun sözleşmesi (`design/ladder.py`)

| Aile | Sütunlar | Kullanan basamaklar |
| --- | --- | --- |
| hedef | `target_value` (hedef alçak enlem parçasının log-oran ortalaması) | hepsi |
| kalıcılık | `persistence` (hedefle aynı yöndeki son alçak parça; yoksa NaN) | B1 |
| alçak geçmiş | `low_lag1..4` (en yeni önce) | B2, B3, B3k, B3t, M |
| sürücüler | `drv_*` (t0'da, dakikaya aşağı yuvarlanmış: nedensel) | D, B3, B3k, B3t, M |
| kahin | `drv_oracle_*` (hedef anında) | yalnız B3k |
| orta enlem | `mid_same` (t0'da biten geçişin 40-55° ortalaması) | yalnız B3t |
| kutup | `polar_north_lag1..4`, `polar_south_lag1..4` | yalnız M |
| geometri | `geo_lead_time_h`, `geo_target_lst_sin/cos`, `geo_doy_sin/cos`, `geo_altitude_km` | B2 ve üstü |
| kimlik | `group` (fırtına kümesi), `intensity`, `lead_bin`, `t0_utc`, `target_mid_utc`, `satellite` | ÇD ve tablolar |

B0 ve B1 uydurulmaz (sırasıyla 0 ve `persistence`). Diğerleri ridge; ceza iç döngüde seçilir.

## Ön kayıt düğmeleri (`configs/pilot.toml`)

Plan 07'deki 11 kararın her biri bir TOML alanı. Dosyadaki değerler plan 07'nin **önerileridir**, karar değil; ön kayıt belgesi yazılınca dosya düzenlenir ve her koşunun `manifest.json` içindeki `config_digest` hangi sürümle üretildiğini gösterir. Bugünkü varsayılanlar: birincil havuz min SYM-H < −50 nT; eşit ağırlık; CHAMP (pilot); 60-270 dk; dış 10 / iç 5 kat; tampon 57 sa; alfa ızgarası 0,01-1000; bootstrap 10 000 (tohum 20270207); permütasyon 1000 (sınıf × öngörü kutusu tabakalı); H1 tek yönlü.

## Doğrulama iskeleti

- Grup = `group` (fırtına kümesi). Katlar: gruplar ilk t0'a göre sıralanır, sırayla katlara dağıtılır (plan 07 önerisi). Testi: `test_grouped_folds_round_robin_by_epoch`.
- Tampon: ardışık iki grubun örnek pencereleri (ilk t0 → son hedef zamanı) arasında 57 saatten az varsa `run_experiment` **koşmayı reddeder**; önce katalogda küme birleştirilir.
- İç döngü yalnız cezayı seçer; ölçekleme ve doldurma her katın eğitim kısmında uydurulur.
- Çıktı: her satır için her modelin fırtına dışı tahmini; kat kimliği; kat başına seçilen alfa (permütasyonda yeniden ayar yapılmaz, aynı alfa kullanılır: belgelenmiş sadeleştirme, `statistics/permutation.py` başlığı).

## Sentetik üreteç ve iskelet testi

`synthetic.py`: fırtına başına 46 dk adımda sürücü (AR 0,8), gizli kutup ısınması (AR 0,7), alçak enlem `x_t = s + 0,6 x_{t-1} + 0,5 d_t + γ h_{t-3} + ε`; kutup gözlemi `h_t` + gürültü. γ = 0 → kutup bloğu hedeften bağımsız (sıfır durumu); γ > 0 → yalnız kutup geçişlerinden erişilebilen, 3 adım (≈2,3 sa) gecikmeli bilgi. Fırtınalar 200 sa arayla (tampon sağlanır), sınıflar sırayla atanır.

İskelet testi (plan 07, hafta 4) `experiment/skeleton.py`: 200 tekrar × {γ = 0, γ = 0,3}, 30 fırtına × 40 örnek, tam merdiven, dış 10 / iç 5 kat, bootstrap 2000. Ölçüt: (1) sıfır durumunda aralığın **tamamen sıfırın üstünde** kalma oranı ≤ %5 (H1 tek yönlü); (2) γ = 0,3'te aralık tekrarların ≥ %80'inde sıfırın üstünde ve ortalama kazanç pozitif.

**Ölçülen (6 Eki 2026, 200 tekrar, `kanit/iskelet_testi_cikti_2026-10-06.txt`):**

| Durum | Nokta tahmini (göreli RMSE azalması) | Aralık tamamen > 0 (M iyi) | Aralık tamamen < 0 (M kötü) | Süre |
| --- | --- | --- | --- | --- |
| γ = 0 (sıfır) | ortalama −0,48 %, SD 0,32 %, aralık −1,25..+0,61 % | **%0,0** | %39,0 | 1134 s |
| γ = 0,3 | ortalama +7,17 %, SD 1,47 %, aralık +3,90..+11,41 % | **%100,0** | %0,0 | 1266 s |

Sonuç PASS: yanlış pozitif %0 ≤ %5; geri bulma %100 ≥ %80; ortalama kazanç pozitif. Bulgu: sıfır durumunda nokta tahmini sistemli olarak **eksi** ve aralık sıfırı tekrarların %39'unda eksi tarafta dışlıyor. Nedeni: M, gerçekte sıfır olan sekiz kutup katsayısını kestiriyor; iç içe model cezası (ana planın andığı Clark-West etkisi). "Aralık sıfırı içermeli" ölçütü iki yönlü okunursa iskelet bu etkiden dolayı düşer, H1'in yönünde okununca geçer; ölçüt tek yönlü yazıldı, iki yönlü oran raporlanıyor. Birincil bootstrap testi M aleyhine muhafazakârdır; ön kayıt belgesine yazılmalı (`07`).

**Permütasyon testi sentetik kanıtı (`kanit/permutasyon_sentetik_kaniti_cikti_2026-10-06.txt`, 30 × 40, 200 permütasyon, 3 tohum):** sıfır durumunda gözlenen −0,17..−0,36 %, sıfır dağılımı ortalaması −0,16..−0,52 % (SD ≈ 0,2 %), p = 0,14 / 0,20 / 0,56; γ = 0,3'te gözlenen +8,7..+9,6 %, p = 0,005 (200 permütasyonla alınabilecek en küçük değer). Sıfır dağılımının ortalaması eksi: permütasyon, iç içe model cezasını sıfır dağılımına taşıyor ve karşılaştırmayı adil kılıyor. Koşu başına 23-36 s.

## Gerçek veri hattı (6 Eki 2026 öğleden sonra)

**Referans yoğunluk** (`space_environment/analysis/reference_density.py`): `QuietNrlmsisReference` pymsis 0.13'ü vektörel çağırır; F10.7 (önceki gün) ve 81 günlük ortalama `GfzIndexProvider`'dan, yedi Ap yuvasının hepsi 4 (`geomagnetic_activity=-1`); `f107s/f107as/aps` her zaman verildiği için pymsis ağa çıkmaz (belgesi okundu). Testte doğrulandı: yuvaların hepsi 4 iken fırtına kipi ile günlük kip birebir aynı (plan 03'ün bulgusu, rtol 1e-6). `add_reference_density(track, model, stride=)` düğümlerde değerlendirip `ln ρ` için doğrusal içdeğerler. Ölçülen hata (60 s CHAMP izi, 29 Eki 2003): düğüm aralığı 2 dk → en büyük |Δ ln ρ| 0,006; 3 dk → 0,012; 6 dk → 0,051; 10 dk → 0,13 (yaklaşık karesel). 10 s üründe adım 6 (60 s düğüm) → **0,0015** (`kanit/uctan_uca_2003_10_29_cikti.txt`); önerilen ayar bu. Sidera köprüsünden tek tek örnekle giden `integration.sidera.SideraReferenceModel` çapraz kontrol için yazıldı (Sidera ortamında koşulmadı).

**Uçtan uca koşu** (`kanit/uctan_uca_2003_10_29.py`, çıktı `_cikti.txt`, `results/uctan_uca_20031029_20261006/`): CDF 8640 kayıt → QD/MLT → referans (adım 6) → 125 parça (31 alçak, 16+16 kutup, 31+31 orta; hepsi tam) → 138 örnek → Richardson-Cane + OMNI kesiti ile fırtına tablosu (28 Eki −58 nT orta ve 29 Eki −391 nT aşırı, **aynı küme 11**) → `CombinedDrivers` → **138 satır × 120 sütun** tasarım matrisi; parquet ve `manifest.json` (commit, yapılandırma özeti, 7 veri dosyasının SHA-256'sı). Toplam 8 s. Ölçülen: hedef `ln ρ/ρ_ref` 3 saatlik ortalamaları 00h −0,11 → 06h +0,13 → 21h +0,63 (fırtına tepkisi görünür); hedef ortalama +0,23, SD 0,28; sürücü ailesinde NaN oranı %35 (Halloween L1 boşluğu, `02`), `solar_wind_available` bayrağı tüm satırlarda 1 (OMNI çerçevesi var, değerler boş); kalıcılık NaN %5; kutup ailesi NaN %13 (gün başı). Tek fırtına olduğundan ÇD koşulmadı.

## İkincil analizler ve kapı raporu (6 Eki 2026 akşam)

`statistics/secondary.py`: `comparison_table` aynı küme bootstrap'ini altı çifte uygular (B3→M birincil; D→B3 H4; B3t→M ve B3k→M kontroller; B1→B2, B2→B3 merdiven); tek yönlü bootstrap p değeri = adayın referansı geçmediği yeniden örnekleme oranı (`BootstrapResult.p_one_sided`). `lead_bin_tests` birincil karşılaştırmayı öngörü kutusu başına yapar ve `holm_adjust` ile düzeltir (ana plan "Çoklu test"); `h2_gain_peaks_mid_lead` H2'yi betimsel olarak işaretler; `loss_difference_by_class` sınıf başına d_s dağılımını verir. `experiment/report.py` `gate_report` bunları plan 07'nin kapı listesine göre Markdown'a döker; d_s'nin ölçülen SD'si ile güç tablosunu da ekler (madde 9 için girdi). Testler sentetik veride (`tests/test_pp_secondary_report.py`).

Eksik olan: B3t'nin iki tanımıyla sonuç (bugün tek tanım: aynı geçişin orta enlem ortalaması), Liu-2010 taban puanı, kısmi korelasyon; `07` kapı listesinde kalıyor.

## Fırtına penceresi veri seti kurucu (6 Eki 2026 akşam)

`experiment/dataset.py`: her katalog satırı için `[rahatsızlık − 6 sa, pencere sonu]` aralığını kapsayan günlük CDF'ler bulunur (`daily_file`, sürüm eki en yüksek olan; GRACE adları plan 01'den, diskte doğrulanmadı), tek iz olarak birleştirilir, QD (apexpy varsa; yoksa coğrafi, kapsam satırında yazar), referans (adım 6), parçalar, örnekler, tasarım; yalnız t0'ı fırtına penceresinde olan satırlar kalır (`group == küme`). Fırtına başına parquet önbelleği (anahtar: yapılandırma özeti + uydu + satır + adım). `build_dataset` tüm fırtınaları birleştirir ve **kapsam tablosu** üretir (gün gereken/bulunan, kayıt, geçerli oran, parça, örnek, satır). 29 Eki 2003 gününde test: 2 gün gerekli 1 bulundu, 8640 kayıt, 98 tasarım satırı; önbellekten ikinci okuma birebir aynı (`tests/test_pp_dataset.py`, `requires_data`).

## Test ve kapı durumu (6 Eki 2026)

`kanit/space_environment_testler_2026-10-06h.txt`: ruff temiz, mypy 58 dosya temiz, 3 import sözleşmesi KEPT, **120 geçti, 1 atlandı** (önceki kayıtlar `06f`: 111, `06g`: 114). Yeni test dosyaları: `test_pp_design_and_models.py` (yapılandırma, merdiven, gerçek CHAMP gününde tasarım matrisi ve nedensellik, ridge), `test_pp_validation_and_statistics.py` (katlar, tampon, iç içe ÇD, tablolar, bootstrap, permütasyon, güç), `test_pp_experiment.py` (uçtan uca, küçük iskelet, manifest).

## Kalanlar

| # | İş | Bağlı olduğu |
| --- | --- | --- |
| 1 | ~~Gerçek veri hattı~~ 6 Eki öğleden sonra yazıldı ve 29 Eki 2003 CHAMP gününde uçtan uca koşuldu (aşağıda) | — |
| 2 | ~~Sürücü işlevi~~ `design/drivers.py` `CombinedDrivers` (OMNI + GFZ + Hp30 + Dst; L1 boşluğunda NaN + `solar_wind_available` bayrağı) | — |
| 3 | Pilot koşusu: 30 fırtına, CHAMP 2001-05..2005-12; önce CHAMP 2001-2005 indirme (onay) | `07`, `01` |
| 4 | Ön kayıt belgesi → `configs/pilot.toml` güncellemesi, 9. madde pilottan sonra | `07` |
| 3b | Pilot koşusu artık tek komutluk: `build_dataset` → `run_experiment` → `gate_report`; eksik olan veri | `01` |
| 5 | Gradient boosting basamağı (ana plan "Model sınıfı" 2); bugün yalnız ridge | — |
| 6 | Diebold-Mariano / Clark-West ikincil testleri; koşullu karşılıklı bilgi eki (isteğe bağlı) | — |
| 7 | Permütasyonda alfa yeniden ayarı (bugün sabit); maliyet 5× | — |
