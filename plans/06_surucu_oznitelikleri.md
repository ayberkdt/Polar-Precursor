# 06 — Sürücü öznitelikleri

Hazırlanma: 5 Ekim 2026. Ana plan: `../00_ana_plan.md`, "Model merdiveni ve sürücü seti". Ham verinin nereden ineceği: `02_gunes_ruzgari_ve_indeksler.md`.

**Etiketler.** `[OKUNDU]` tam metin bu oturumda açıldı. `[İKİNCİL]` asıl kaynak açılamadı, başka bir makaleden. `[DOĞRULANMADI]` açılamadı ya da hafızadan.

## Ana plana göre değişenler

1. **W05 Poynting akısını kendin çalıştırmana gerek yok; hazır seri var.** Weimer 2023'ün Zenodo arşivi (doi 10.5281/zenodo.7667515) "the polar heating values and ΔT as a function of time for the years 2000 through 2019" içeriyor (makalenin veri bildiriminden `[OKUNDU]`; Zenodo sayfası açılmadı). EXTEMPLAR arşivinde de `W05_Poynting_flux.zip` (27,6 MB) var. B katmanı böylece kolaylaşıyor.
2. **Açık kaynak W05 kodu yok.** Zenodo'daki sürüm derlenmiş IDL `.sav`, lisans CC BY-NC-ND. Python uyarlaması bulunamadı.
3. **Hp30/ap30, 1985'ten itibaren var** (GFZ Hpo V3.0). A katmanında 3 saatlik ap yerine 30 dakikalık ap30 kullanılabilir.
4. **Liu 2010'un modeli örneklem dışı doğrulanmamış.** Tek fırtına dizisinde gösterilmiş. D modelinin doğal bir "yayınlanmış taban" karşılığı: `ρ = 0,5·Ēm + ρ_ortam`.
5. **Licata kutuları SYM-H içindir**; Poynting akısı yalnız anlık yarımküre toplamı olarak giriyor.

## Bağlaşım fonksiyonları

Hepsi GSM'de, `B_T = sqrt(By² + Bz²)`, saat açısı `θ = atan2(By, Bz)`.

| Fonksiyon | Formül | Durum |
| --- | --- | --- |
| Birleşme elektrik alanı (Kan-Lee) | `Em = v · B_T · sin²(θ/2)`, mV/m | `[OKUNDU]` Liu 2010 Denk. 3 |
| Newell | `dΦ/dt = v^(4/3) · B_T^(2/3) · sin^(8/3)(θ/2)` | `[İKİNCİL]` [Holappa ve Mursula](https://arxiv.org/pdf/1805.10699), Borovsky 2022. Newell 2007 (10.1029/2006JA012015) açılamadı |
| Doygunluklu Em | `Em_d = 8·Em / sqrt(64 + Em²)` | `[OKUNDU]` Liu 2010 Denk. 4; yazarlar sonunda bırakmış |

- Birim: `v` km/s, `B` nT ile `Em [mV/m] = v · B_T · sin²(θ/2) · 10⁻³`. Bu dönüşüm birim hesabıdır; Newell için yaygın kullanım (km/s, nT, sabitsiz) yalnız arama özetinden, `[DOĞRULANMADI]`. Ridge öncesi ölçekleme yapıldığı için sabit çarpan sonucu etkilemez; yine de teze yaz.
- Ana plandaki "Kan-Lee üssü doğrulanamadı" notu kapandı: Liu 2010 Denk. 3.
- Liu'nun veri hazırlığı: ACE, 1 dakikaya örnekleme, 10 RE'de manyetopoza yayılım, üstüne "an additional average delay of 15 min ... as travel time to the thermosphere". OMNI yay şoku burnuna kaydırılmış; aynı 15 dakikayı eklemek ya da eklememek bir tasarım seçimi. Öneri: ekleme; gecikme kutuları zaten bunu öğrenir. Seçimi yaz.

## Hafıza terimleri

**Üstel ağırlıklı integral** (Liu 2010 Denk. 8) `[OKUNDU]`:

```
Ēm(t, τ) = ∫ Em(t') · exp((t' − t)/τ) dt'  /  ∫ exp((t' − t)/τ) dt'
```

- Liu: `τ = 3 sa`; "differs only weakly when τ ranges from 1 h to 10 h. So the exact choice of τ is not critical."
- Uygulama: 1 dakikalık seride özyinelemeli süzgeç. `τ ∈ {1, 3, 6, 10} sa` dört sabit öznitelik üret; τ'yu uydurmaya çalışma. Ana plandaki "zaman sabitlerini eğitim verisinde uydur" adımı böylece sadeleşir ve sızıntı riski kalkar.

**Weimer tarzı ısınma terimi** (Weimer 2023 Denk. 2) `[OKUNDU]`:

```
ΔT(t+δt) = ΔT(t) + α·S_T(t) − ΔT(t)·δt/τ_c − P_NO(t)
```

- ΔT tepesi Poynting akısı tepesinden yaklaşık 3 saat sonra.
- Parametreler Weimer ve ark. 2020'de ([VTechWorks açık kopya](http://hdl.handle.net/10919/101873)) `[OKUNDU, sonradan]`. Denklem numaraları: ΔT özyinelemesi (9), NO soğuma gücü (10), NO özyinelemesi (11):
  - (10) `P_NO = β·ΔNO·exp(−2700 / (ΔT + T_Solar))`
  - (11) `ΔNO(t+δt) = ΔNO(t) − ΔNO(t)·δt/τ_NO + γ·S_T(t)`
  - Sürüm 6 değerleri: `α = 0,005001 K/GW`, `β = 0,8499 K`, **`τ_c = 9,999 sa`**, **`τ_NO = 17,00 sa`**, `γ = 0,0001 /GW` (sabit), `δt = 4 dk`; W05 doygunluk parametresi 3100 GW.
  - Sürüm 4 (ölçülmüş SABER NO ile): `α = 0,00771 K/GW`, `τ_c = 9,671 sa`.
- Sonuç: üstel hafıza özniteliklerine **10 saatlik** bir zaman sabiti zaten dahil (1, 3, 6, 10); NO soğuması için 17 saatlik bir sabit eklemek fiziksel dayanağı olan tek ek. Zaman sabiti kümesi: {1, 3, 6, 10, 17} sa.

**Hazır seri: Zenodo 7667515** `[OKUNDU, sonradan]` — CC BY 4.0, 22 Şub 2023.

- `Heating_DeltaT.h5` (57,9 MB): anahtarlar `DELTAT` (K), `JHNORTH`, `JHSOUTH` (yarımküre toplam ısıtma, GW; W05 alan-integralli Poynting akısı), `MJTIMES` (değiştirilmiş Jülyen günü), `OKFLAG`.
- **4 dakikalık aralık, 1 Oca 2000 - 1 Oca 2020, kesintisiz**; IMF boşlukları ara değerle doldurulmuş, `OKFLAG = 0` doldurulan yerleri işaretliyor.
- `Figure7a/7b/9a/9b_Data.h5`: 1620 ızgara hücresi için gecikme (dakika). H2'nin "beklenen pencere"sini yerel zamana göre sayısal olarak verir.
- `GridCellData.zip` (707 MB): CHAMP ve GRACE-A'dan türetilmiş ekzosfer sıcaklıkları; gerek yok.
- B katmanı için yalnız `Heating_DeltaT.h5` ve dört küçük şekil dosyası yeter (yaklaşık 58 MB). `OKFLAG = 0` olan anları öznitelikte "eksik" say; ara değerle doldurulmuş ısıtma fırtına anında yanıltıcı olabilir.

**Gecikme kutuları** (ana plan): bağlaşımın 0-1, 1-2, 2-3, 3-4,5, 4,5-6 saat ortalamaları. Liu: "More than 95% of the delays are within 6 h." Kutular bunu kapsıyor.

**SYM-H geçmişi** (CHAMP-ML Tablo 1, [arXiv 2206.05824](https://arxiv.org/html/2206.05824); özetleyici üzerinden iki kez sorgulandı, tablo doğrudan görülmedi): SYM-H anlık, 0-3, 3-6, 6-9, 9-12, 12-33, 33-57 saat ortalamaları. En uzun hafıza 57 saat; çapraz doğrulama tamponu bundan geliyor.

## Yayınlanmış gecikmeler (öznitelik tasarımının dayanağı)

Liu ve ark. 2010 `[OKUNDU]`, 30 fırtına (Dst < −100 nT), CHAMP 2002-2005. Gecikmeler 3 saatlik ağırlıklandırmanın ve 15 dakikanın üstüne:

| Bant | Sektör (MLT) | Gecikme |
| --- | --- | --- |
| Alçak (±30°) | sabah 05-09 | 1,5 sa |
| Alçak (±30°) | diğerleri | yaklaşık 3 sa |
| Orta (30-60°) | öğle 10-16 | 0 sa |
| Orta (30-60°) | sabah | 1,5 sa |
| Orta (30-60°) | akşam 17-20, gece 21-04 | 4,5 sa |

Üç süper fırtınada yoğunluk "almost immediately or within 1 to 2 h" tepki veriyor. Mevsim bağımlılığı yok.

Weimer ve ark. 2023 `[OKUNDU]`, toplam Poynting akısına göre:

| Bölge | Gecikme |
| --- | --- |
| 60° üstü | "generally less than 60 min" (gündüz yaklaşık 40 dk) |
| 30° altı | "in the range of 180–300 min" |
| Ekvator, 20 yerel saat | yaklaşık 280 dk |
| 30° enlem, 18 yerel saat | 350 dakikaya kadar |
| Yumuşatılmış harita aralığı | 45-353 dk |

- Gecikmeler yay şoku-iyonosfer yayılımını (20-35 dk) **içeriyor**; ayrıca kaydırma uygulanmamış.
- Fırtına şiddetine göre ayrım yapılmamış. Makale, Wang ve ark. 2020'nin büyük fırtınalarda daha uzun, Liu 2010'un süper fırtınalarda daha kısa gecikme bulduğunu not ediyor. **H3'ün yönü literatürde tartışmalı**; ön kayıt belgesinde bunu belirt.
- Veri: Mehta ve ark. 2017 CHAMP ve GRACE-A yoğunlukları, NRLMSIS 2.0 ile ekzosfer sıcaklığına çevrilmiş. TU Delft ürünü değil; ölçek farkı olabilir.

**Sonuç.** Kutup girdisinin pencere argümanı: kutup 1 saatten kısa, alçak enlem 3-5 saat. Akşam/gece alçak enlem en uzun gecikmeli sektör; kutup ölçümünün en çok işe yarayabileceği yer orası. Hedefi yerel zaman sektörüne göre ayrıştırma (ana plan) bu yüzden önemli.

## Şok bayrağı

Knipp ve ark. 2017 ([PMC5562409](https://pmc.ncbi.nlm.nih.gov/articles/PMC5562409/)) `[OKUNDU]`:

- Şok ölçütü: birkaç dakika içinde manyetik alan büyüklüğünde ve yoğunlukta %20 ya da daha fazla artış, eşzamanlı sıcaklık değişimi, hızda 20 km/s artış.
- 192 yalıtılmış ICME (2002-2014): 84 şok öncüllü, 109 şoksuz (kaynakta toplam 193 ediyor).
- Etki: "an approximate doubling" (NO akısı ve yoğunluk tepkisi ortancası).
- Zamanlama: AE ve NO artışı ICME varışından yaklaşık 12 saat önce başlıyor; büyük NO artışlı olaylarda yoğunluk "usually within a day" toparlanıyor.
- Sıfır epok ejecta ön kenarı; bizim Bz dönüşü epokumuzla aynı değil.

Uygulama: A katmanı için OMNI'den otomatik kural (5 dakikada dinamik basınç ve |B| en az %20, hız en az 20 km/s artış). B katmanı için CfA şok veritabanı (bkz. `05_firtina_katalogu.md`). Öznitelik: "son şoktan beri geçen süre", 0-48 saat, sonrası doygun.

**Yazılan kural ve ölçümü (6 Eki 2026; `solar_wind/shock.py`):** her dakika için önceki 10 dakikanın ortancası ile o dakikadan başlayan 10 dakikanın ortancası karşılaştırılıyor; hız ≥ 40 km/s artmış, |B| ve yoğunluk ≥ 1,3 kat olmuşsa işaret; 30 dk içindeki işaretler tek aday, zamanı ilk işaret. Knipp'in %20 / 20 km/s eşikleri OMNI'de çok sayıda yanlış aday verdiği için sıkılaştırıldı (bu projenin seçimi; dört olayda ayarlandı, doğrulanmadı). R&C rahatsızlık zamanlarına göre:

| Olay (R&C) | Aday | Fark |
| --- | --- | --- |
| 28 Eki 2003 02:06 | 02:02 | −4 dk |
| 19 Kas 2001 18:15 | 18:05 | −10 dk |
| 24 Kas 2001 05:56 | 05:51 | −5 dk |
| 7 Kas 2004 18:27 | 18:24 | −3 dk |
| 9 Kas 2004 18:25 | 18:54 | +29 dk (OMNI'de basamak 18:55'te) |
| 24 Ağu 2005 06:13 | 06:05 | −8 dk |
| 15 May 2005 02:38, 6 Kas 2001 01:52 | yok | OMNI plazması boşluklu |

Ayrıca R&C listesinde karşılığı olmayan adaylar var (7 Kas 2004 02:52, 9 Kas 09:58, 17 Ağu 2005 20:19, 24 Kas 2001 04:50 vb.); şok mu, iç yapı mı belirlenmedi. Aday ancak `zaman + 10 dk` anında "bilinir" (`confirmed_at`); tahmin özniteliği yalnız o andan sonra şoku sayar.

## Öznitelik tablosu

**A katmanı (gerçek zamanlı erişilebilir)**

| Grup | Öznitelik | Sayı |
| --- | --- | --- |
| Bağlaşım, gecikme kutuları | Em ve Newell × 5 kutu | 10 |
| Bağlaşım, üstel hafıza | Em × 5 zaman sabiti (1, 3, 6, 10, 17 sa) | 5 |
| Güneş rüzgarı anlık | v, n, dinamik basınç, By, Bz (son 30 dk ortalaması) | 5 |
| SYM-H | anlık + 6 kutu | 7 |
| ap30 (ya da ap) | anlık, 0-3, 3-6 sa | 3 |
| Güneş | F10.7 (önceki gün), 81 günlük ortalama | 2 |
| Şok | son şoktan beri süre | 1 |
| Geometri | hedef yerel zamanı (sin, cos), yılın günü (sin, cos), irtifa, öngörü süresi | 6 |

**Yazıldı (6 Eki 2026; `analysis/features.py` ve `analysis/index_features.py`):**

| Grup | Sınıf / işlev | Öznitelik |
| --- | --- | --- |
| Sürücü | `DriverFeatureBuilder` | OMNI anlık (7), Em / doygun Em / Newell (3), Em ve güney Bz üstel hafızası × 5 τ (10), Em, Bz ve SYM-H gecikme kutuları × 5 (15), son 6 saatte Em geçerli oranı (1), son şoktan beri saat (1) = **37** |
| İndeks | `IndexFeatureBuilder` | önceki gün F10.7, ortalanmış 81 gün (nedensel değil, işaretli), günlük Ap, o dilimin Kp'si, son tamamlanmış ap30, ap30 0-3 ve 3-6 sa ortalamaları, son tamamlanmış saat Dst = **8** |
| Geometri | `geometry_features` | hedef yerel zaman (sin, cos), yılın günü (sin, cos), irtifa, öngörü süresi = **6** |

Toplam 51; plandaki 39'un üst kümesi (fazlası Bz hafızası ve kutuları). Pilotta ridge ile budanır. Nedensellik: yarım saatlik ve saatlik indeksler yalnız aralık bittikten sonra kullanılıyor (07:04'te ap30 06:30-07:00 dilimi, Dst 06-07 saati; test var). Sürücü tablosu 210-235 t0/s.

Yaklaşık 39 sürücü özniteliği. Etkin örneklem 150-200 fırtına; ridge cezası ve fırtına gruplu doğrulama bu oranı taşır, ama daha fazla öznitelik ekleme. İki bağlaşım fonksiyonundan biri pilotta elenebilir.

**B katmanı (sonradan işlenmiş, duyarlılık)**

- W05 toplam Poynting akısı, kuzey ve güney: Zenodo 7667515 ya da EXTEMPLAR arşivi (10.5281/zenodo.3525166, CC BY 4.0).
- ΔT serisi (aynı arşiv).
- AE, AL, PC(N) (OMNI).
- S10, M10, Y10 (SOLFSMY).

Dikkat: Kyoto SYM-H kesin değerleri gerçek zamanlı ürünle aynı değil. A katmanındaki SYM-H'nin gerçek zamanlı erişilebilirliği `02`'de tartışılıyor; tezde "A katmanı = gerçek zamanlı karşılığı olan büyüklükler, sonradan işlenmiş değerleriyle" diye yaz.

## Sürücü verisi her fırtınada yok (sonradan eklendi, ölçüldü)

OMNI'de 29 Eki 2003 05:50'den 18:42'ye ve 30 Eki boyunca IMF ve plazma yok (bkz. `02`). Sonuçları:

- A katmanının güneş rüzgarı öznitelikleri bu olaylarda hesaplanamaz. Örnekleri atmak, en bilgilendirici fırtınaları atmak demek.
- Öneri: öznitelik başına "geçerli oran" sütunu zaten planlıydı; ek olarak **sürücüsüz bir B3 türevi** (yalnız indeksler: ap30, Dst, F10.7) tanımla ve sürücü kapsamı eşiğin altındaki örneklerde onu kullan. M'nin kazancını iki alt kümede ayrı raporla: sürücü var / sürücü yok.
- Beklenti (sınanacak): sürücü yokken kutup yoğunluğu elde kalan tek erken bilgi; kazanç orada daha büyük olabilir. Bu, ön kayıt belgesine ikincil hipotez olarak yazılabilir.

Yazılan kod: bağlaşım fonksiyonları, üstel hafıza ve gecikme pencereleri `space_environment.solar_wind` içinde, testleriyle (bkz. `11`).

## Zaman hizalama kuralı (sızıntıya karşı)

- Tahmin anı `t0` = kutup bandı geçişinin bitişi.
- Sürücü öznitelikleri yalnız `t ≤ t0` verisinden. OMNI zaten yay şokuna kaydırılmış zaman damgası taşıyor; `t0`'a kadar olan damgalar kullanılır.
- B3k (kahin) için aynı öznitelikler `t ≤ t_hedef` ile yeniden üretilir; ayrı sütun adlarıyla.
- Birim testi: bir örnek için `t0`'dan sonraki OMNI satırlarını NaN yap; A katmanı öznitelikleri değişmemeli. **Yapıldı (6 Eki 2026):** `t0` sonrası tüm sütunlar 10⁵ ile bozuldu, 32 özniteliğin hiçbiri değişmedi (`tests/test_shock_and_features.py`, kanıt çıktısı).

## Yayınlanmış taban: Liu modeli

D basamağının yanına "Liu-2010" satırı ekle (öneri): `ρ = 0,5·Ēm(τ=3 sa, gecikme tablosu) + ρ_ortam`, `ρ_ortam = ρ_r·(P10.7 − 60)/(P10.7_r − 60)`. Katsayı ortancası 0,5, ölçüm birimi 10⁻¹² kg/m³, 400 km için.

- Liu'nun kendi başarımı: tek fırtına dizisi (22-28 Tem 2004), R = 0,83-0,95, göreli hata standart sapması %17-32, tepeler %15-20 fazla tahmin.
- Bizim katkımız: aynı modelin 200 fırtınada örneklem dışı puanı. Küçük ama somut bir yan sonuç.

## Açık noktalar

- [ ] Newell 2007 aslını aç; birim ve formülü teyit et.
- [x] Zenodo 7667515 içeriği (5 Eki 2026, yukarıda).
- [ ] CHAMP-ML Tablo 1'i PDF'ten gözle doğrula.
- [x] Weimer 2020 parametreleri (5 Eki 2026, yukarıda).
- [ ] Hpo lisansı (sayfada yazmıyor).
