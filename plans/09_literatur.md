# 09 — Literatür konumu ve okuma planı

Hazırlanma: 5 Ekim 2026. Ana plan: `../00_ana_plan.md`, "Literatür konumu".

**Erişim durumu.** Wiley (AGU dergileri) ve ScienceDirect bu oturumda otomatik erişimi reddetti (403 / bot denetimi). Aşağıda `[ÖZET]` işaretli her şey OpenAlex/Crossref üzerinden okunan özettir; tam metin okunmadı. `[OKUNDU]` tam metin açıldı.

## Yenilik iddiasının bugünkü durumu

Yüksek enlemde ölçülmüş yoğunluğu, sürücüler ve alçak enlemin kendi geçmişi verilmişken, alçak enlem yoğunluğunun gecikmeli tahmin girdisi olarak sınayan bir çalışma **bulunamadı**. Dayanak: dört web araması, üç OpenAlex araması, Weimer 2023'e atıf yapanların tam listesi; hepsi özet düzeyinde. AGU/AMOS bildiri özetleri kötü dizinleniyor. Bu, yokluğun kanıtı değil.

**Ana plandaki bir iddia zayıfladı.** Ana plan "okunan ML modellerinin hiçbiri uydunun kendi yakın geçmiş yoğunluğunu girdi olarak kullanmıyor" diyor. 2026'da bunu yapan en az bir çalışma var:

- **Zhang ve ark. 2026**, Space Weather, doi 10.1029/2026SW005105 `[ÖZET]`: iTransformer, "forecasts thermospheric density over the next 24 hr using observations from the preceding 24 hr"; CHAMP, GRACE-A, GRACE-C, GOCE, TM02; MSISE-00'a göre artık.

Bu, H4'ün ("kendi geçmişini kullanan B3, yalnız sürücü modelinden belirgin iyi") yenilik değerini düşürür; H4 artık "ilk kez gösterildi" diye değil, "1-4 saatte, fırtına gruplu doğrulamayla, ne kadar" diye yazılmalı. Tam metni okumadan H4'ü tezin yedek ayağı sayma.

## Güncelleme: ikinci okuma turu (5 Eki 2026, sonradan)

Wiley, ScienceDirect, ESSOAr ve GFZpublic yine 403 verdi. Başka yollardan dört kaynak tam okundu; Zhang 2026'nın makalesi yerine yazarların açık eğitim betiği okundu.

**AETHER-P3** ([arXiv 2608.00352](https://arxiv.org/pdf/2608.00352)) `[OKUNDU, tam]`

- **Ölçülmüş yoğunluk girdi değil**, yalnız eğitim hedefi. Girdiler (Denk. 3-8): gelecekteki konumlar; geçmiş penceresinde JB2008 ve NRLMSISE-00 yoğunlukları; F10.7, F10.7A, F30; Dst, Ap30; Bz, v, proton yoğunluğu, AE.
- 10 dakikalık çözünürlük, 3 saat girdi, 6 saat ufuk. CHAMP, GRACE-A, GOCE, Swarm-C ile eğitim.
- Bölme: test aralığıyla örtüşen pencereler çıkarılmış; rastgele değil. Fırtına testi tek olay (10-13 May 2024).
- Fırtına başarımı (Tablo 4-5): aşırı olayda R 0,89-0,90, göreli hata 0,23-0,35; ana evrede R 0,77-0,80.
- Ufuk başına sayı yalnız sakin testlerde. Enlem ayrımlı analiz, kalıcılık tabanı, sürücü ablasyonu yok.
- Bizim için: D basamağının (yalnız sürücü) en yakın yayınlanmış karşılığı. Ana plandaki "kendi geçmişini kullanmıyor" tespiti bu model için doğru.

**Zhang ve ark. 2026** (makale `[ÖZET]`; kod [Zenodo 22022981](https://zenodo.org/records/22022981), `train_pure_itrans.py` `[OKUNDU]`)

- **Kendi ölçülmüş yoğunluk geçmişi girdi**: `ln(gözlem) − ln(MSISE)` artığı, 24 saatlik pencere, 60 s aralık.
- Yardımcı girdiler: F10.7, F10.7A, ap; gün ve yerel saat; irtifa, enlem, boylam. **Güneş rüzgarı yok.**
- Yardımcı girdiler geçmişi **ve tahmin penceresini** kapsıyor: gelecekteki ap ve F10.7 modele veriliyor. Bizim B3k (kahin) basamağının karşılığı; gerçek zamanlı bir tahmin değil.
- Bölme: kesintisiz parça içinde kronolojik, %85 eğitim, 12 saat boşluk; test için tüm yıl/uydu ayrılmış (2008 CHAMP, 2008 ve 2014 GRACE-A). Fırtına gruplu değil.
- Özetten: CHAMP 2008'de R² 0,9052, ortalama mutlak yüzde hata %77,66'dan %11,56'ya; **24 saatlik en büyük konum hatasında CHAMP için %24,6 azalma**.
- Fırtına örnekleri: Mart 2008 CHAMP, Mart 2015 GRACE-A (makalede Tablo 6; okunmadı).
- Kodda 1, 3, 6, 12, 24 saatlik hata hesaplanıyor, ama baştan birikimli pencere olarak; sayılar okunan dosyalarda yok.
- Enlem bandı analizi yok (enlem yalnız girdi). Sürücü-yalnız karşılaştırma tabanı özetten görünmüyor.
- Sınır: okunan betik "V4.3-Baseline"; yayınlanan model bunun bir türevi olabilir.

**H4 için sonuç.** Zhang 2026 "kendi geçmişi işe yarar"ı gösteriyor, ama (a) gelecek ap ile, (b) güneş rüzgarı olmadan, (c) kronolojik bölmeyle, (d) 24 saat ufukta, (e) sürücü-yalnız tabana karşı değil. H4'ün kalan özgün kısmı: 1-4 saatte, yalnız tahmin anına kadarki sürücülerle, fırtına gruplu doğrulamayla, sürücü-yalnız modele göre artış. Dar ama savunulabilir. Ayrıca Zhang konum hatası sonucu veriyor; yörünge bölümünde kıyas noktası.

**Oliveira ekibinin kalibrasyonu** (Zesta ve Oliveira 2019 `[OKUNDU]`): her uydu ayrı ayrı JB2008'e göre kalibre ediliyor, birbirine göre değil. Düşük etkinlik dönemleri |SYM-H| < 30 nT; gözlem/model oranına 15. dereceden polinom, uydu başına `f(t)`; analiz edilen oran `ρ / (f(t)·ρ0(t))`, `ρ0` Dst = 0 ile JB2008. Bizim fırtına başına `b_s` bunun yerel karşılığı.

**Hâlâ yalnız özet:** Wang 2022/2023 (girdi listesi ve ufuk bilinmiyor), Oliveira 2017 JGR (159 fırtına bilgisi yalnız arama özetinden), Newell 2007, Emmert 2017, Sutton 2009, Hejduk ve Snow 2018. Bruinsma ve Forbes 2009/2010 için açık kopya yok. Hepsi yayıncıda açık ya da üniversite erişimiyle açılır; normal tarayıcıdan bak.

## Önce okunacaklar (öncelik sırasıyla)

| # | Çalışma | Neden | Durum |
| --- | --- | --- | --- |
| 1 | Zhang ve ark. 2026, doi 10.1029/2026SW005105 | Kendi geçmişi girdi; H4'e en yakın. Girdi listesi, bölme biçimi, 1-4 saatteki başarım, enlem ayrımı var mı? | `[ÖZET]` |
| 2 | Wang ve Bai, AETHER-P3, [arXiv 2608.00352](https://arxiv.org/abs/2608.00352) | 3 saat girdi penceresiyle 6 saate kadar tahmin; ufuk bizimkiyle aynı. Girdi penceresinde ölçülmüş yoğunluk var mı, özetten anlaşılmıyor | `[ÖZET]` arXiv, açık |
| 3 | Wang ve ark. 2022, doi 10.1029/2021SW002950 | LSTM topluluğu; **GOCE ile eğitim, Swarm-C ile test**, taban NRLMSISE-00. Girdi listesi ve ufuk özetten çıkmıyor | `[ÖZET]` Altın açık erişim; normal tarayıcıda açılır |
| 4 | Wang ve ark. 2023, doi 10.1029/2023SW003576 | "short-time prediction ... along the satellite orbit"; CHAMP, GOCE, Swarm-C | `[ÖZET]` |
| 5 | Oliveira ve ark. 2017 JGR, doi 10.1002/2017JA024006 + ek dosyalar | 159 ve 168 farkı; fırtına listesi; ara kalibrasyon | `[ÖZET]` |
| 6 | Weimer ve ark. 2023, doi 10.1029/2022SW003410 | Gecikme haritaları; H2'nin dayanağı | [Açık PDF](https://spacewx.com/wp-content/uploads/2023/06/Space-Weather-2023-Weimer-Global-Variations-in-the-Time-Delays-Between-Polar-Ionospheric-Heating-and-the-Neutral.pdf) |
| 7 | Cheng ve ark. 2024, doi 10.1029/2024SW004010 | CHAMP yoğunluğu WAM'e asimile, Kasım 2003; "ölçüm başka yere bilgi taşır"ın fizik modeli karşılığı | `[ÖZET]` |
| 8 | Sutton, Forbes ve Knipp 2009, doi 10.1029/2008JA013667 | Alçak enlem 3-4 sa, orta-yüksek 2 sa altı | `[ÖZET]` |
| 9 | Bruinsma ve Forbes 2007 (10.1029/2007GL030243), 2009 (10.1016/j.asr.2008.10.031), 2010 (10.1016/j.jastp.2010.06.010) | Gezen atmosferik bozulma hızları | 2007 `[ÖZET]`, diğerleri açılamadı |
| 10 | Weimer ve ark. 2020, EXTEMPLAR, doi 10.1029/2019SW002355 | Poynting akısı sürücülü ekzosfer sıcaklığı modeli | `[ÖZET]` |

Ana plandaki not düzeltmesi: Wang 2022 CHAMP/GRACE değil GOCE/Swarm-C kullanıyor.

## Fizik: doğrulanmış sayılar

| Kaynak | Bulgu | Durum |
| --- | --- | --- |
| Oliveira ve ark. 2017 (bildiri, [arXiv 1710.07743](https://arxiv.org/pdf/1710.07743)) | Yüksek enlem ilk 1,5 sa; ekvator 3 sa içinde; soğuma yaklaşık 21. saatte | `[OKUNDU]` |
| Zesta ve Oliveira 2019 ([NTRS](https://ntrs.nasa.gov/api/citations/20200000388/downloads/20200000388.pdf)) | Aşırı fırtınada "reach the equator only 1.5 hr after storm onset"; en yükseğe 9,5 sa, toparlanma 22 sa | `[OKUNDU]` |
| Sutton ve ark. 2009 | "between 3 and 4 h at low latitudes while less than 2 h at midlatitudes to high latitudes"; üç fırtına, 20-29 Tem 2004; gece tarafı daha belirsiz | `[ÖZET]` |
| Bruinsma ve Forbes 2007 | Gündüz tarafı bozulmalar %20-30 genlik; kuzeyden 730 m/s, güneyden 460 m/s; tek olay, 29 May 2003 | `[ÖZET]` |
| Weimer ve ark. 2023 | 60°-30° coğrafi enlem arasında kısa-uzun gecikme arasında sert geçiş; gecikme 18-20 yerel saatte en uzun; gündüz ekvator geceden erken | `[ÖZET]` |

Hepsi sürücüden (ya da ısıtmadan) yoğunluğa gecikme ya da tasvir. Yoğunluktan yoğunluğa gecikmeli tahmin yok.

## Weimer 2023'e atıf yapanlar (tam liste, OpenAlex, 5 kayıt = 3 ayrı çalışma)

| Çalışma | Ne yapıyor | Bizimle ilişki |
| --- | --- | --- |
| Billett ve ark. 2024, doi 10.1029/2023SW003748 (+2 ön baskı) | 2022 Starlink fırtınaları; Swarm-C ve GRACE-FO yoğunluğu, AMPERE akımları; tasvir | Yüksek enlem gözleminin önemini savunuyor, ama akım gözlemi; tahmin deneyi yok |
| Bag ve ark. 2023, doi 10.1016/j.asr.2023.09.064 | NO soğuma, örnek olaylar | İlgisiz (başlıktan) |
| Cheng ve ark. 2024, doi 10.1029/2024SW004010 | CHAMP yoğunluğunun WAM'e asimilasyonu | Ruhen en yakın; enlem gecikmeli sınama yok |

Hiçbiri bir enlemdeki ölçülmüş yoğunlukla başka bir enlemi önceden tahmin etmiyor (özetlerden).

## Yakın çalışmalar tablosu (2023-2026)

| Çalışma | Yaptığı | Farkı |
| --- | --- | --- |
| Zhang 2026 (10.1029/2026SW005105) | Kendi geçmişiyle 24 sa tahmin | Enlem ayrımlı öncül sınaması ve sürücülere göre artış sınaması yok (özetten) |
| AETHER-P3 (arXiv 2608.00352) | 6 saate kadar, 3 saat girdi penceresi | Ölçülmüş yoğunluk girdisi belirsiz |
| Briden ve ark. ([arXiv 2310.16912](https://arxiv.org/abs/2310.16912)) | "historical atmospheric density data" ile Transformer | Model alanlarıyla eğitilmiş indirgenmiş küresel durum |
| Bös ve ark. ([arXiv 2511.06105](https://arxiv.org/abs/2511.06105)) | 3 güne kadar Transformer | Girdiler özetten belli değil |
| STORM-AI yarışması 2026 (10.22541/essoar.177170467.73030997/v1) | Yörünge ortalaması yoğunluk, 3 gün | Yerinde yoğunluk öncülü yok. Mayıs 2024 fırtınasında JB2008'e göre kazancın %6,1'e düştüğünü bildiriyor; gerekçe bölümü için alıntılanabilir |
| Forootan ve ark. 2023 (10.1038/s41598-023-47440-x) | CHAMP/GRACE/Swarm ile NRLMSISE-00 kalibrasyonu, kısa vadeli tahmin | Küresel ölçekleme |
| Acciarini ve ark. 2024, Karman (10.1029/2023SW003652) | Ampirik model girdileriyle ML | Yoğunluk geçmişi yok |

Yöntem öncülü: arXiv 2206.13992, manyetosfer-iyonosferde aktarım entropisi (açılmadı; Bz'den indekslere, yoğunluğa değil).

## Konumlama cümlesi (taslak, tam metin okumalarından sonra kesinleşir)

Fiziksel gecikme iyi belgelenmiş (ekvatora ortalama 3 saat, aşırı fırtınada 1,5 saat). Makine öğrenmesi modelleri ya ölçülmüş yoğunluğu hiç kullanmıyor ya da uydunun tüm geçmişini enlem ayırmadan kullanıyor. Açık kalan soru: yüksek enlem ölçümünün, sürücüler ve alçak enlem geçmişi bilinirken, kattığı ek tahmin değeri.

## Yinelenecek taramalar

- [ ] Ocak 2027 ve Mart 2027: OpenAlex'te `cites:W4362705618` (Weimer 2023) ve Zhang 2026, AETHER-P3'e atıf yapanlar.
- [ ] Google Scholar'da elle: "high-latitude density" + "precursor", "lagged" + "thermospheric density" + "low latitude".
- [ ] AGU Fall Meeting 2026 özetleri (Aralık): SA oturumları.
