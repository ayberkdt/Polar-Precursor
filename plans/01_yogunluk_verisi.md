# 01 — Yoğunluk verisi (CHAMP, GRACE)

Hazırlanma: 5 Ekim 2026. Ana plan: `../00_ana_plan.md`, "Veri kaynakları ve erişim".

**Etiketler.** `[OKUNDU]` kaynak bu oturumda açıldı. `[ARŞİV]` yalnız Wayback Machine kopyası (Mart-Nisan 2026). `[ÖRNEKLEME]` ajan tarafından küçük sorgularla ölçüldü. `[DOĞRULANMADI]` açılamadı.

## Karar

**Birincil kaynak ESA Swarm dağıtım sunucusundaki CDF ürünü** (TU Delft V2 ile aynı veri seti). TU Delft ASCII yedek.

Gerekçe: ESA yolu uçtan uca doğrulandı (dizin listesi, değişken adları, bayrak anlamı, dosya boyutları, girişsiz erişim). TU Delft'in canlı sunucusuna bu makineden hiç ulaşılamadı (bağlantı sıfırlandı; üç ayrı araçla); sütun düzeni ve bayrak kodlaması hâlâ bilinmiyor.

## Ana plana göre değişenler

1. **Zenodo 4602380 işe yaramıyor.** İçeriği doğrulandı: Mehta 2017 tabanlı yoğunluk (TU Delft V2 değil), CHAMP 2002 - Şubat 2010, yalnız GRACE-A, 2010'da bitiyor; 2001 ve 2011-2015 yok; bayrak sütunu yok. İçindeki JB2008 fırtına terimi açık halidir. Yalnız çapraz kontrol ve HASDM karşılaştırması için değerli.
2. **CHAMP 2005'te yalnız 230 günlük dosya var** (ESA V2). Ana planın pilotu "yalnız CHAMP, 2002-2005" diyor; 2005'teki boşluk pilot seçiminden önce incelenmeli.
3. **CHAMP irtifası görev boyunca 460 km'den 260 km'ye iniyor.** "Yaklaşık 400 km" varsayımı yalnız 2003-2004 için doğru. Yörünge periyodu da değişiyor; zamanlama geometrisi (kutuptan ekvatora +23 dk vb.) sabit sayılamaz, geçiş zamanlarından hesaplanmalı.
4. **GRACE yoğunluğu iz boyunca 422 km'ye alçak geçiren süzgeçli** (CHAMP 152 km). Geçiş ortalamaları için sorun değil; cusp gibi dar yapılar GRACE'te bulanık.
5. **Helyum uyarısı Siemes 2023'e atfedilemez.** Makale gövdesinde helyum tartışılmıyor. Thayer 2012 (ana planda) ve Bernstein ve ark. 2020 kaynak gösterilmeli.
6. **ESA ürün kısa adları:** GRACE için `GR_DNSxACC_2_`, GRACE-FO için `GF_DNSxACC_2_` (ana plandaki `GR_DNS_ACC_2_` boş sayfa veriyor).

## ESA CDF ürünü `[OKUNDU]`

Kaynak sayfalar: [CH_DNS_ACC_2_](https://swarmhandbook.earth.esa.int/catalogue/CH_DNS_ACC_2_), [GR_DNSxACC_2_](https://swarmhandbook.earth.esa.int/catalogue/GR_DNSxACC_2_), [GF_DNSxACC_2_](https://swarmhandbook.earth.esa.int/catalogue/GF_DNSxACC_2_).

| Uydu | Klasör | Dosya adı | DOI |
| --- | --- | --- | --- |
| CHAMP | `swarm-diss.eo.esa.int/#swarm/Multimission/CHAMP/DNS` (düz) | `CH_OPER_DNS_ACC_2__YYYYMMDDT000000_YYYYMMDDT235959_0001.cdf` | 10.57780/esa-d259fd1 |
| GRACE-A | `.../Multimission/GRACE/DNS/Sat_1/<YYYY>/` | `GR_OPER_DNS1ACC_2__..._0001.cdf` | 10.57780/esa-d069715 |
| GRACE-B | `.../Multimission/GRACE/DNS/Sat_2/<YYYY>/` | `GR_OPER_DNS2ACC_2__..._0001.cdf` | aynı |
| GRACE-FO C | `.../Multimission/GRACE-FO/DNS/Sat_1/<YYYY>/` | — | 10.57780/esa-2559fd1 |

- Günlük dosya, 10 s aralık; CHAMP dosyası 563.686 bayt, GRACE 563.699 bayt.
- FTP karşılığı: `ftp://swarm-diss.eo.esa.int/Multimission/...`
- Dizin listesi girişsiz açıldı (`?do=list&...&file=swarm%2FMultimission%2FCHAMP%2FDNS`). **Gerçek dosya indirmesi sınanmadı.**
- GRACE klasörlerinde ürün tanım belgesi var: `SW-TN-DUT-GS-129-01_TOLEOS_Product_Definition_Document.pdf` (2,8 MB). Açılmadı; biçim ve bayrak için asıl başvuru belgesi. İlk iş olarak oku.

**CDF değişkenleri** (üç uydu için aynı):

| Değişken | Tür, birim |
| --- | --- |
| `time` | CDF_EPOCH, ms, UTC |
| `altitude` | m, GRS80 |
| `latitude` | derece, jeodezik |
| `longitude` | derece |
| `local_solar_time` | saat |
| `density` | kg/m³ |
| `density_orbitmean` | kg/m³, kayan ortalama olarak yörünge ortalaması |
| `validity_flag` | "0 = nominal data, 1 = anomalous data" |
| `validity_flag_orbitmean` | aynı |

**İyi veri = bayrak 0.** Ana plandaki "geçerlilik bayrağı 1 olan kayıtları at" ifadesi bununla uyumlu.

**Dosya sayıları** (dizin listesinden):

| Yıl | CHAMP | GRACE-A | GRACE-B |
| --- | --- | --- | --- |
| 2001 | 355 | — | — |
| 2002 | 364 | 198 | 198 |
| 2003 | 365 | 365 | 327 |
| 2004 | 366 | 366 | 364 |
| 2005 | **230** | 365 | 348 |
| 2006 | 358 | 365 | 365 |
| 2007 | 365 | 365 | 360 |
| 2008 | 363 | 366 | 366 |
| 2009 | 361 | 365 | 365 |
| 2010 | 247 | 365 | 360 |
| 2011 | — | 311 | 276 |
| 2012 | — | 292 | 288 |
| 2013 | — | 293 | 287 |
| 2014 | — | 310 | 308 |
| 2015 | — | 259 | 247 |

- Hacim: CHAMP tüm görev 1,97 GB (3496 dosya); GRACE-A 2002-2015 2,58 GB (4585 dosya); GRACE-B 2,51 GB (4459 dosya). **Toplam yaklaşık 7,1 GB.**
- Eksik gün = dosya yok. Dosya var diye günün tamamı geçerli sayılmaz; bayrak oranını ayrıca ölç.
- GRACE 2011 sonrası yılda 55-105 gün eksik. 2011-2015 fırtınalarının bir kısmı uydu kapsamı yüzünden düşecek; 217 hedefi buna göre okunmalı.

**Alternatif erişim: VirES HAPI** (jetonsuz çalıştı) `[OKUNDU]`

- `https://vires.services/hapi/info?dataset=CH_OPER_DNS_ACC_2_`: aralık PT10S, 2000-07-29 - 2010-09-04, tek sorguda en çok 50 gün.
- Veri kümeleri: `CH_OPER_DNS_ACC_2_`, `GR_OPER_DNS1ACC_2_` (2002-04-04 - 2017-10-31), `GR_OPER_DNS2ACC_2_` (- 2017-05-22), `GF_OPER_DNS1ACC_2_`.
- Parametreler: `Timestamp, Latitude_GD, Longitude_GD, Height_GD, local_solar_time, density, density_orbitmean, validity_flag, validity_flag_orbitmean`.
- Kullanım koşulları sayfası (vires.services/data_terms) açılmadı.
- Küçük denemeler ve tek fırtına çekmek için uygun; toplu indirme için dosya yolu daha temiz.

`viresclient` aynı koleksiyonları sunuyor ([belge](https://viresclient.readthedocs.io/en/latest/available_parameters.html)); jeton gereksinimi doğrulanmadı.

## TU Delft ASCII (yedek) `[ARŞİV]`

- "Update on December 13, 2025: Our FTP server has been replaced by a more secure web server."
- Kök: `https://thermosphere.tudelft.nl/data`; yoğunluk: `/data/data/version_02/{CHAMP_data,GRACE_data,GRACE-FO_data,GOCE_data,Swarm_data}/`.
- En güncel sürüm 02 (CHAMP: 1 Oca 2023; GRACE A/B: 15 Tem 2022). 3 Mart 2026 tarihli README'de sürüm 03 yok.
- Adlandırma (README): uydu kısaltması + `DNS` + `ACC` + yıl + ay + sürüm. Olası desen `CH_DNS_ACC_YYYY_MM_v02.txt`; ayırıcı (alt çizgi mi tire mi) doğrulanmadı.
- Lisans: yoğunluk ve yan rüzgar verisi **CC BY 4.0**; geometri/aerodinamik/radyasyon basıncı modelleri CC BY-NC-SA 4.0.
- Atıf: Siemes ve ark. 2023, doi 10.1051/swsc/2023014.
- `[DOĞRULANMADI]`: sütun listesi, birimler, başlık biçimi, bayrak değerleri, dosya boyutları.
- Ek dizinler ileride işe yarayabilir: `geometry_models/`, `aerodynamic_models/` (balistik katsayı için), `crossovers/`, `orbital_plane_alignments/` (çapraz uydu testi için düzlem hizalanma tarihleri).

Başka bir ağdan (üniversite, mobil) `https://thermosphere.tudelft.nl/data/README.txt` adresini bir kez dene.

## Gerçek veriyle ilk bakış (5 Eki 2026, sonradan eklendi) `[ÖLÇÜLDÜ]`

Betikler ve çıktılar `kanit/` altında: `gercek_iz_kontrol.py`, `bayrak_orani_ornekleme.py`. Veri VirES HAPI'den, jetonsuz çekildi (CDF dosyası indirilmedi).

**HAPI yolu çalışıyor.** 27 Eki - 1 Kas 2003 için 43.200 kayıt geldi; aralık 10 s; irtifa metre cinsinden (389,7-419,4 km); sütunlar belgedekiyle aynı.

**CHAMP boşlukları** (ESA dizin listesinden, 2001-2010; 3 gün ve üstü):

| Boşluk | Gün |
| --- | --- |
| 20-25 Mar 2001 | 6 |
| **1 Mar - 6 Tem 2005** | **128** |
| 19-21 Eyl 2005 | 3 |
| 2-4 Eki 2005 | 3 |
| 19-23 Nis 2006 | 5 |

Toplam eksik 160 gün. **Yedi aşırı fırtınadan biri (15 May 2005) CHAMP boşluğunun içinde**; o olay yalnız GRACE-A ile incelenebilir. Boşluğun nedeni bilinmiyor.

**Geçerli kayıt oranı** (her ayın 15'i, tek gün örneklemesi; bayrak 0 oranı):

- CHAMP: veri bulunan 112 örnek günün 109'unda %95 ve üstü. Düşük günler: Oca 2001 %85, Kas 2002 %70, Oca 2009 %55. Ayrıca 1 Tem 2008 günü %46 çıktı (örnekleme dışı, ayrı kontrol).
- GRACE-A: örneklenen günlerin neredeyse tamamı %98 ve üstü. Düşük günler: Oca 2004 %51, Haz 2010 %92, Kas 2010 %83. 2011-2015'te ayın 15'ine denk gelen 11 günde veri yok (dosya eksikliğiyle tutarlı).
- Sonuç: veri olan günlerde bayrak sorunu seyrek, ama tek tük yarı boş günler var. Geçiş başına %70 eşiği makul görünüyor; tam dağılımı toplu indirmeden sonra ölç.
- Sınır: ayda bir gün örnekleme; fırtına günlerinde oran farklı olabilir. 27 Eki - 1 Kas 2003'te oran %99,99.

**29 Ekim 2003 fırtınası önizlemesi.** Tek olay, coğrafi enlem (quasi-dipole değil), bantlar |enlem| > 63° ve < 30°; `y = ln(gözlem / MSIS 2.1, ap=4) − b_s`, epok 07:04 UT (Zesta ve Oliveira Tablo 2). Geçiş ortalamaları:

| Epok (sa) | Bant | y ortalama |
| --- | --- | --- |
| −1,62 | kutup K | −0,20 |
| −0,85 | kutup G | 0,00 |
| −0,08 | kutup K | **+0,66** |
| +0,30 | alçak, 13,3 yerel saat | −0,10 |
| +0,69 | kutup G | +0,59 |
| +1,08 | alçak, 1,3 yerel saat | +0,10 |
| +1,85 | alçak, 13,3 | +0,17 |
| +2,62 | alçak, 1,3 | **+0,60** |
| +3,38 | alçak, 13,3 | +0,25 |
| +4,16 | alçak, 1,3 | +0,55 |

- Kutup, epok civarında bir geçişte yaklaşık +0,65 sıçrıyor; gece tarafı alçak enlem aynı düzeye yaklaşık 2,6 saat sonra çıkıyor; gündüz tarafı daha yavaş ve daha küçük.
- Kutup sıçraması epoktan hemen önceki geçişte görünüyor; şok 06:11 UT'de gelmişti, yani ısınma Bz dönüşünden önce başlamış olabilir. Epok tanımının (şok mu, Bz dönüşü mü) sonucu etkileyeceğinin somut örneği.
- Fırtına öncesi 24 saatte kutup değerleri `b_s`'nin 0,2 altında: önceki gün de etkin, `b_s` kirlenmiş. `04`'teki "fırtına öncesi pencere temiz mi" denetimi gerekli.
- Bu tek olay hipotezi sınamaz; yalnız veri hattının ve tanımların çalıştığını, sinyalin gözle görülür olduğunu gösterir. Tam tablo çıktı dosyasında.

**Dosya yolu da doğrulandı (sonradan eklendi).** `CH_OPER_DNS_ACC_2__20031029T000000_20031029T235959_0001.cdf` ESA sunucusundan **girişsiz** indi (`?do=download&file=...`, HTTP 200, 563.686 bayt; dizin listesindeki boyutla aynı). `cdflib` ile açıldı: 9 değişken, 8640 kayıt, 00:00:00 - 23:59:50, bayrakların tamamı 0, irtifa metre. Dolgu değeri 0,999×10³³ (bayrak için 127). Dosya `../data/raw/density/CHAMP/` altında; ürün tanım belgesi (`SW-TN-DUT-GS-129-01`, 2,8 MB) `../data/raw/docs/` altında, henüz okunmadı.

**Ürün tanım belgesi okundu (6 Eki 2026).** `SW-TN-DUT-GS-129_01`, Rev. 3, 12 Tem 2022, TOLEOS (TU Delft, CNES, DLR, Bonn). Yoğunluk ürünü `DNSxACC_2` bölümünden:

- Dosya adı deseni: `CC_SRC_DNSxACC_2__start_end_bbvv`; uydu alanı CHAMP için `_`, GRACE ve GRACE-FO için 1/2; `bb` işlem temeli, `vv` dosya sürümü.
- Girdi: kalibre ivmeölçer, uydu aerodinamik ve radyasyon basıncı modelleri, termosfer modelleri (sıcaklık, bileşim, iz boyunca rüzgâr), konum ve hız, yönelim, kütle.
- Çözünürlük: "10–30 s time step (depending on the mission), equivalent to 76–228 km along the orbit".
- **Belirsizlik:** "30% of variance of orbit average of mass density or 5 × 10⁻¹⁴ kg/m³, whichever value is largest". Fırtına tepkisi (log-oranda 0,3-1,0) bunun çok üstünde; sakin dönemde ve yüksek irtifada (GRACE 2008-2009, yoğunluk 10⁻¹³ mertebesi) taban belirsizlik oranın %10-50'si olabilir. `b_s` ve geçiş ortalaması bunu kısmen bastırır; GRACE güneş minimumu dışlaması bu yüzden de yerinde.
- Bayrak: 0 = nominal, 1 = anomalous (ESA el kitabıyla aynı). Bayrağın hangi durumlarda 1 olduğu belgede açıklanmıyor.
- Güncelleme sıklığı 3 ay, gecikme 2 ay (GRACE-FO için).

## İrtifa geçmişi `[ÖRNEKLEME]`

Tek yörüngelik anlık örnekler (VirES HAPI, `Height_GD`); yıllık ortalama değil.

| Tarih | CHAMP (km) | GRACE-A (km) |
| --- | --- | --- |
| 1 Tem 2001 | 443 (408-479) | — |
| 1 Tem 2002 | 419 | veri yok |
| 1 Tem 2003 | 407 | 493 |
| 1 Tem 2004 | 388 | 487 |
| 1 Oca 2005 | 377 | — |
| 31 Ara 2005 | 357 | — |
| 1 Tem 2006 | 368 | 480 |
| 1 Tem 2007 | 354 | 478 |
| 1 Tem 2008 | 339 (329-358) | 477 (456-502) |
| 1 Tem 2009 | 328 | 476 |
| 1 Tem 2010 | 283 | 474 |
| 4 Eyl 2010 | 259 (248-278) | — |
| 31 Ara 2011 | — | 465 (449-493) |
| 1 Tem 2013 | — | 448 |
| 1 Tem 2015 | — | 399 |
| 31 Ara 2015 | — | 385 (372-408) |

- Başlangıç irtifaları (Siemes 2023 Tablo 2 `[OKUNDU]`): CHAMP 461 km, GRACE 506 km.
- Ana plandaki açık nokta ("2011 sonundaki irtifalar") kapandı: GRACE-A 465 km; CHAMP o tarihte yok.
- Sonuç: CHAMP-GRACE irtifa farkı 2003'te 85 km, 2009'da 150 km. Çapraz uydu testinde genlik ölçeği zamana bağlı; uydu çiftine tek bir sabit katsayı yetmez. Ölçek katsayısını irtifa farkının fonksiyonu yap ya da testi yıllara böl.
- 2015'te GRACE 385-400 km'de: CHAMP'in 2003-2004 irtifası. 2014-2015 GRACE verisi sinyal/gürültü açısından 2007-2009'dan çok daha iyi.

## Kalite uyarıları (Siemes ve ark. 2023, [HTML](https://www.swsc-journal.org/articles/swsc/full_html/2023/01/swsc230004/swsc230004.html)) `[OKUNDU]`

- **Isıl kontrol.** 2010 ortasında 5 °C'lik basamak; "In April 2011, the accelerometer's thermal control was entirely deactivated, leading to temperature variations up to 10 °C". V2 sıcaklık kaynaklı yanlılığı modelliyor. GRACE-A sıcaklığı 2013-2014'te yok (GRACE-B'ninki kullanılmış; kalıntı dalga var).
- **Radyasyon basıncı.** İz boyunca, 2007-2009'da GRACE-A için aerodinamik ivmenin yaklaşık %100'ü. %5 model belirsizliği varsayımıyla GRACE-A yoğunluğunda %5 belirsizlik. CHAMP için daha az kritik.
- **Modeller güneş minimumunda yoğunluğu fazla tahmin ediyor.** Gözlem/model oranı 2006'dan 2009'a NRLMSISE-00 için %20'den fazla düşüyor. Fırtına başına yanlılık terimi `b_s` bunu emer; yine de `b_s`'yi yıla karşı çiz, eğilimi gör.
- **Yüzey etkileşimi.** Sabit enerji uyum katsayısı; en büyük etki 500 km'de ve düşük güneş aktivitesinde.
- Çözünürlük: CHAMP 152 km, GRACE A/B 422 km.

Ana plandaki önlem geçerli: 2007-2009 GRACE verisini ana analizden çıkar, duyarlılık testi yap.

## Zenodo 4602380 `[OKUNDU]`

- "CHAMP and GRACE-A Density Estimates with Associated HASDM and JB2008 Predictions"; Licata, Mehta, Tobiska, Bowman, Pilinski; 12 Mar 2021; CC BY 4.0.
- `CHAMP_New.zip` 1,18 GB (açılınca 3,69 GB; 2944 günlük dosya, 2002 - 2010 gün 53); `GRACE_A_New.zip` 2,09 GB (açılınca 7,21 GB; 2002 gün 213 - 2010).
- CHAMP 10 s, GRACE-A 5 s.
- Sütunlar: `GPS Time (sec), Geodetic Altitude (km), Geodetic Latitude (deg), Geodetic Longitude (deg), Local Solar Time (hours), Velocity Magnitude (m/s), Surface Temperature (K), Free Stream Temperature (K), Yaw (rad), Pitch (rad), Proj_Area_Eric (m^2), CD_Eric (~), Density_Eric (kg/m^3), Proj_Area_New (m^2), CD_New (~), Density_New (kg/m^3), Density_HASDM (kg/m^3), Density_JB2008 (kg/m^3)`.
- Kullanım: (a) TU Delft V2 ile Mehta yoğunluğu arasındaki ölçek farkını ölçmek (Weimer 2023 ve CHAMP-ML Mehta verisini kullanıyor; onlarla sayı karşılaştırırken gerekli); (b) HASDM'yi B0'ın yanına "en iyi operasyonel model" satırı olarak koymak; (c) izdüşüm alanı ve C_D sütunlarından balistik katsayı. Hiçbiri ilk üç hafta için şart değil; indirmeyi kapıdan sonraya bırak.

## İş adımları

**A. Ocak öncesi kontrol (1 saat)**

1. TOLEOS ürün tanım belgesini indir ve oku.
2. Tek bir CHAMP günü indir: `CH_OPER_DNS_ACC_2__20031029T000000_20031029T235959_0001.cdf` (0,56 MB). `cdflib` ile aç; değişken adları, 8640 kayıt, bayrak dağılımı, irtifa birimi (m) yukarıdakiyle aynı mı?
3. Aynı günü VirES HAPI'den çek, yoğunlukları karşılaştır (aynı olmalı).
4. Sonucu `kanit/` altına yaz.

**B. Toplu indirme (hafta 1, ilk gün)**

1. Hedef: `D:\Masaustu\Polar Precursor\data\raw\density\{CHAMP,GRACE_A,GRACE_B}\`. C diskinde 12 GB boş yer var; **hiçbir veri ve önbellek C'ye yazılmayacak.**
2. Dizin listesinden dosya bildirimi üret (ad, boyut); indir; boyutu bildirime karşı doğrula; eksik ve bozuk dosyaları raporla. Yeniden çalıştırılabilir olsun (var olan ve boyutu tutan dosyayı atla).
3. Önce yalnız CHAMP 2001-2005 (0,95 GB): pilot için yeter. Kalanı kapı kararından sonra.
4. Beklenen sayılar yukarıdaki tabloda; tutmazsa dur.

**C. Okuma ve birleştirme**

1. Günlük CDF → yıllık parquet (uydu başına): zaman, enlem, boylam, irtifa, yerel zaman, yoğunluk, bayrak.
2. Kapsam raporu: gün başına geçerli kayıt oranı; uydu-yıl ısı haritası. CHAMP 2005 boşluğunun tarihleri.
3. Akıl sağlığı kontrolleri: yoğunluk pozitif; irtifa yukarıdaki tabloyla tutarlı; ardışık kayıtlar 10 s; enlem aralığı ±87,3° (CHAMP), ±89° (GRACE).

## Açık noktalar

- [ ] Gerçek dosya indirmesinin girişsiz çalıştığı (adım A2).
- [x] CHAMP 2005 boşluğunun tarihleri: 1 Mar - 6 Tem 2005 (yukarıda). Nedeni hâlâ bilinmiyor.
- [ ] TU Delft ASCII biçimi (başka ağdan).
- [ ] VirES veri kullanım koşulları; ESA ürününün lisans metni (TU Delft kaynağı CC BY 4.0).
- [ ] GRACE-B'yi kullanıp kullanmamak: GRACE-A ile aynı yörünge, 220 km geride; bağımsız bilgi eklemez. Öneri: yalnız GRACE-A (Oliveira ve Zesta da öyle yapmış); GRACE-B boşluk doldurmada yedek.
