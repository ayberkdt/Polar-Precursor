# 15 — Ön kayıt belgesi (taslak, danışmana gidecek tek sayfa)

Hazırlanma: 6 Ekim 2026, pilot sonrası (`14`). Kaynak: `07` "Ön kayıt belgesinde sabitlenecek kararlar", `00` "Senden karar bekleyenler", pilot kapı raporu (`kanit/pilot_v3_sektorlu_rapor_2026-10-06.md`), iskelet bulgusu (`13`). Her madde için **öneri** yazılı ve gerekçesi ölçülmüş; **karar** sütunu boş, sen dolduracaksın. Belge onaylandığında `configs/main.toml` bu maddelerden üretilir ve her koşunun `manifest.json` içindeki `config_digest` bu belgeye bağlanır. Onaydan sonra hiçbir madde değişmez; değişirse yeni sürüm ve tarih.

## A. Soru ve hipotezler

**Soru.** Fırtına sırasında, 60-270 dakika öncesinden, yüksek enlem (|QD enlem| > 63°) geçiş yoğunluğu, alçak enlem (|QD enlem| < 30°) geçiş yoğunluğunun kestirimine, güneş rüzgarı/indeks sürücülerinin ve uydunun kendi alçak enlem geçmişinin ötesinde katkı veriyor mu?

| Hipotez | İfade | Yön | Statü |
| --- | --- | --- | --- |
| H1 (birincil) | M (B3 + kutup geçişleri), B3'ten daha düşük fırtına dışı hata verir | tek yönlü | pilot: +6,0 % [+3,3, +9,9] |
| H2 | Kazanç 105-195 dk kutularında en yüksektir | betimsel | pilot: evet; 60-105 dk'da kazanç yok |
| H3 | Kazanç fırtına şiddetiyle değişir | iki yönlü (literatür çelişkili, `06`) | pilot: aşırı/şiddetlide büyük, zayıfta sıfır |
| H4 | B3 (kendi geçmişi + sürücüler), D'den (yalnız sürücüler) 1-4 saatte belirgin iyidir | tek yönlü | pilot: +56 % |
| H1b (pilotta doğan ek soru) | M'nin kazancı kutba özgüdür: M, B3t'nin iki tanımını da geçer | tek yönlü | pilot: (a) +2,9 % [+0,8, +5,8], (b) +3,6 % [+0,6, +7,3] |

## B. Sabitlenecek kararlar

| # | Madde | Öneri | Gerekçe (ölçülmüş) | Karar |
| --- | --- | --- | --- | --- |
| 1 | Fırtına kümesi | Richardson-Cane 5.1 (30 Tem 2026 sürümü, `05`), rahatsızlık 2001-05-01 … 2015-12-31, OMNI 1 dk SYM-H ile sınıf; **birincil havuz: küme sınıfı ≥ orta (min SYM-H < −50 nT)**; zayıf sınıf ikincil | Pilotta zayıf sınıfta ortalama d_s = 0,0000 (6 küme); orta ve üstünde 0,0008-0,0050. Zayıfları birincil havuza almak etkiyi seyreltir; eşik sonuçtan önce yazılıyor | ☐ |
| 2 | Birim ve ağırlık | Birim = fırtına kümesi (57 sa kuralıyla birleşmiş olaylar); fırtına başına tek d_s, **eşit ağırlık** | Pilotta havuz RMSE tek aşırı katla bozuldu (B3k), eşit ağırlıklı ölçüt sağlam kaldı (`14`) | ☐ |
| 3 | Uydular | **CHAMP ve GRACE-A**; GRACE-B yok; GRACE-A 2007-2009 birincil testin dışında (`01` kalite uyarısı); aynı kümenin iki uydusu aynı grupta | `07` önerisi; GRACE-B bağımsız bilgi katmıyor | ☐ |
| 4 | Öngörü süresi havuzu | 60-270 dk; kutular 60-105, 105-150, 150-195, 195-240, 240-270 | `04`; pilotta kutu başına 30 fırtına doldu | ☐ |
| 5 | Sürücü katmanı A | Gerçek zamanlı erişilebilir: OMNI 1 dk L1 (hız, n, By, Bz; Em, Newell, gecikme pencereleri, hafıza integralleri), **SYM-H yok**, ap30 + saatlik Dst (aralık sonu nedenselliği), şok bayrağı, geometri | `02`: gerçek zamanlı SYM-H yok; pilot bu katmanla koştu | ☐ |
| 6 | Referans yoğunluk | NRLMSIS 2.1, gözlenen F10.7 (önceki gün) ve 81 günlük ortalama, Ap = 4 tüm yuvalarda, iz üstünde 60 s düğümle içdeğerleme | `03` (Ap = 4 ≡ anahtar kapalı, pymsis ile doğrulandı); adım hatası 0,0015 (`13`) | ☐ |
| 7 | Birincil ölçüt ve test | d_s = MSE_B3,s − MSE_M,s; göreli RMSE azalması; küme bootstrap %95, 10 000, tohum 20270207; bootstrap'in iç içe model cezasıyla M aleyhine muhafazakâr olduğu bilinir (`13` iskelet: sıfır durumunda −0,5 %) | İskelet testi PASS (yanlış pozitif %0, geri bulma %100) | ☐ |
| 8 | Doğrulayıcı test | Kutup bloğunu sınıf × öngörü kutusu içinde fırtınalar arasında karıştır; 1000 permütasyon; M aynı katlar ve aynı cezayla yeniden uydurulur (ceza yeniden ayarlanmaz: belgelenmiş sadeleştirme) | Sentetik kanıt: sıfırda p = 0,14-0,56, katkıda p = 0,005 (`13`) | ☐ |
| 9 | En küçük anlamlı etki | **Göreli RMSE azalması ≥ %3** (ana plan kapı eşiğiyle aynı). Pilot SD(d_s) = 0,00192; etki 0,68 SD; 150 fırtına 0,23 SD saptar → %3 eşiği 150 fırtınayla rahat | Pilot `14`; güç tablosu kapı raporunda | ☐ |
| 10 | Model sınıfı | Ridge birincil; ceza iç döngüde (5 kat, gruplu) ızgaradan {0,01 … 1000}; ölçekleme ve doldurma kat içinde; **gradient boosting ikincil** (aynı girdiler, aynı katlar) | Pilot: doğrusal kahin aşırı fırtınada ekstrapole etti (`14`) | ☐ |
| 11 | Hipotez yönleri | H1 tek yönlü; H2 betimsel; H3 iki yönlü; H4 tek yönlü; H1b tek yönlü | `07` + pilot | ☐ |
| 12 | Çapraz doğrulama | Dış 10 kat, gruplar epok sırasına göre dönüşümlü; iç 5 kat; tampon 57 sa (küme kuralı); fırtına dışı tahminler | `07`; pilotta tampon ihlali yok | ☐ |
| 13 | Çoklu test | Birincil test tek (havuz). Öngörü kutusu başına 5 test ikincil, Holm; ayrıştırmalar (evre, sınıf, yerel zaman, mevsim, yarımküre, uydu) keşif etiketli | `00` "Çoklu test" | ☐ |
| 14 | Sürücüsüz örnekler (OMNI boşluğu) | Birincil testte: eğitim ortalamasıyla doldurma + `solar_wind_available` bayrağı **değil**; birincil havuz yalnız sürücü kapsamı olan örnekler; sürücüsüz örnekler ayrı ikincil analiz | Pilotta satırların %22'sinde L1 eksik; en büyük iki fırtınanın ana evresi sürücüsüz (`02`) | ☐ |
| 15 | B3t tanımı | İki tanım da raporlanır: (a) t0'dan önceki son orta enlem parçası (M'den birkaç dk bayat), (b) t0 orta enlem parçasının bitişine kaydırılmış (M'den taze). H1b için eşik: M her ikisini de ≥ %3 geçerse "kutba özgü" | `04` satır 105; pilot: (a) +2,9 % [+0,8, +5,8], (b) +3,6 % [+0,6, +7,3]; daha taze (b) daha az yararlı → tazelik tek başına açıklamıyor (`14` koşu 4) | ☐ |
| 16 | Epok | Rahatsızlık zamanı Richardson-Cane; ana evre başlangıcı kural 2 (`05`); duyarlılık ±30 dk ikincil | `05` | ☐ |
| 17 | Pilot fırtınaları | Ana havuzda kalır; pilot sonucu keşif etiketli; ön kayıt sonrası aynı 2001-2005 verisi yeniden koşulur ve o koşu doğrulayıcıdır | `07` | ☐ |

## C. Önceden yazılan kapı/karar kuralı (ana analiz)

- H1 kabul: birincil bootstrap alt sınırı > 0 **ve** permütasyon p < 0,05 **ve** nokta tahmini ≥ %3.
- H1 kabul ama H1b ret (M, B3t'nin iki tanımından birini %3 geçmiyor): sonuç "taze ölçüm değeri; kutba özgü kısım ≤ %3" olarak yazılır. Tez başlığı buna göre yeniden kurulur.
- H1 ret: H4 ve zamanlama (H2) ana katkı olur.

## D. Veri ve kapsam (sabit)

CHAMP 2001-05 … 2010-09 ve GRACE-A 2002 … 2015 fırtına pencereleri (ESA/TU Delft V2, `01`); OMNI HRO 1 dk 2001-2015; GFZ günlük + Hp30; Kyoto Dst saatlik. Kapsam raporu (fırtına başına gün bulunan/gereken, geçerli oran) ana analizden önce yazılır; uydu kapsamı < %70 olan fırtına kümesi havuzdan düşer (öneri; eşiği sen seç).

## E. Analiz hattı (sabit, kod sürümüyle)

`scripts/pilot_kos.py` yapısı: `build_storm_catalog` → küme → `build_dataset` (DESIGN_VERSION 2) → `run_experiment` → `gate_report`. Her koşu `manifest.json` ile commit ve veri SHA-256'larını kaydeder. Onaylanan belgeyle birlikte kod da etiketlenir (`git tag on-kayit-v1`).

## Açık

- [ ] 17 kararın her birine imza.
- [ ] Uydu kapsam eşiği (D).
- [ ] Oliveira/Zesta e-postası (karar 3, `05`): listeyi istemek (kıyas için), analizi değiştirmez.
