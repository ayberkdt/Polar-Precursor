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

## Test ve kapı durumu (6 Eki 2026)

`kanit/space_environment_testler_2026-10-06f.txt`: ruff temiz, mypy 53 dosya temiz, 3 import sözleşmesi KEPT, **111 geçti, 1 atlandı**. Yeni test dosyaları: `test_pp_design_and_models.py` (yapılandırma, merdiven, gerçek CHAMP gününde tasarım matrisi ve nedensellik, ridge), `test_pp_validation_and_statistics.py` (katlar, tampon, iç içe ÇD, tablolar, bootstrap, permütasyon, güç), `test_pp_experiment.py` (uçtan uca, küçük iskelet, manifest).

## Kalanlar

| # | İş | Bağlı olduğu |
| --- | --- | --- |
| 1 | Gerçek veri hattı: iz → referans yoğunluk sütunu (NRLMSIS ap = 4, Sidera köprüsü) → `segment_track(..., reference=)` → `build_samples` → `build_design` | `11` madde 7 |
| 2 | Sürücü işlevi: `DriverFeatureBuilder.features_at` + `IndexFeatureBuilder.features_at` birleşimi `build_design(drivers=)` için tek çağrı | `06` |
| 3 | Pilot koşusu: 30 fırtına, CHAMP 2001-05..2005-12; önce CHAMP 2001-2005 indirme (onay) | `07`, `01` |
| 4 | Ön kayıt belgesi → `configs/pilot.toml` güncellemesi, 9. madde pilottan sonra | `07` |
| 5 | Gradient boosting basamağı (ana plan "Model sınıfı" 2); bugün yalnız ridge | — |
| 6 | Diebold-Mariano / Clark-West ikincil testleri; koşullu karşılıklı bilgi eki (isteğe bağlı) | — |
| 7 | Permütasyonda alfa yeniden ayarı (bugün sabit); maliyet 5× | — |
