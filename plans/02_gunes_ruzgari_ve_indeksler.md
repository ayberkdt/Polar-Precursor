# 02 — Güneş rüzgarı, jeomanyetik indeksler ve güneş aktivitesi

Hazırlanma: 5 Ekim 2026 (erişim denemeleri 18:45-19:00 UTC). Ana plan: `../00_ana_plan.md`, "Güneş rüzgarı ve indeksler".

**Etiketler.** `[OKUNDU]` sayfa/dosya başlığı ham olarak okundu ya da API canlı sınandı. `[ÖZETLEYİCİ]` yalnız sayfa özetleyici üzerinden. `[DOĞRULANMADI]` açılamadı.

## Ana plana göre değişenler

1. **F10.7 için NRCan 2001-2004'ü vermiyor.** `fluxtable.txt` 28 Eki 2004'te başlıyor. Tüm dönem için GFZ dosyası kullanılacak (Ekim 2003 değerleri API'den doğrulandı).
2. **Hp30/ap30 1985'ten itibaren var.** Dosyanın ilk satırı 1 Oca 1985.
3. **Kyoto'nun HAPI sunucusu var**; Dst ve SYM-H için form doldurmaya gerek yok.
4. **Gerçek zamanlı SYM-H yok.** Kyoto'da SYM-H günler-haftalar gecikmeli; gerçek zamanlı olan yalnız saatlik Dst. A katmanının "gerçek zamanlı erişilebilir" iddiası SYM-H için tutmuyor (aşağıda).
5. **AE 2001-2015 için geçici (provisional) değer.**
6. **OMNI HRO2'de PC(N) yok** ve kapsamı yılda %2-10 daha az. HRO kullan.
7. **SET indeks dosyaları erişilebilir** (ana plandaki "DTCFILE doğrulanmadı" kapandı).

## OMNI yüksek çözünürlük `[OKUNDU]`

**Karar: HRO, 1 dakikalık, aylık CDF, pyspedas ile.**

| | ASCII | CDF |
| --- | --- | --- |
| Yol | `spdf.gsfc.nasa.gov/pub/data/omni/high_res_omni/omni_minYYYY.asc` | `.../omni/omni_cdaweb/hro_1min/YYYY/omni_hro_1min_YYYYMM01_v01.cdf` |
| Boyut | 157,7 MB/yıl (1 dk), 34,4 MB/yıl (5 dk) | 8,4 MB/ay (1 dk), 2,0 MB/ay (5 dk) |
| 2001-2015 | yaklaşık 2,4 GB | yaklaşık 1,5 GB (türetme) |

- ASCII'de başlık satırı yok, sabit uzunluklu kayıt, her dakika mevcut, boşluklar dolgu değeriyle.
- pyspedas 2.2.0 (22 Eyl 2026; ana plandaki 2.1.5 eskidi), kaynaktan okunan imza:

```python
pyspedas.projects.omni.data(trange=[...], datatype="1min", level="hro",
                            downloadonly=False, notplot=False, time_clip=True, ...)
```

- Yerel dizin `omni_data/`; `SPEDAS_DATA_DIR` ya da `OMNI_DATA_DIR` ile değişir. **D diskine yönlendir.** Yerelde çalıştırılmadı.

**Sütunlar** ([hroformat.txt](https://spdf.gsfc.nasa.gov/pub/data/omni/high_res_omni/hroformat.txt)), sırayla: yıl, gün, saat, dakika; IMF ve plazma uydu kimliği; ortalamadaki nokta sayıları; ara değer yüzdesi; zaman kaydırma (s) ve RMS'i; faz cephesi normali RMS'i; gözlemler arası süre; |B|; Bx; By, Bz (GSE); **By, Bz (GSM)**; B RMS'leri; **akış hızı**; Vx, Vy, Vz; **proton yoğunluğu**; sıcaklık; **akış basıncı**; elektrik alan; beta; Alfven Mach; uydu konumu; yay şoku burnu konumu; **AE, AL, AU; SYM/D, SYM/H, ASY/D, ASY/H; PC(N)**; manyetosonik Mach.

- Türetilmişler (kaynakta): akış basıncı `= 2·10⁻⁶·Np·Vp²` nPa; elektrik alan `= −V·Bz(GSM)·10⁻³` mV/m.
- Uydu kimlikleri: ACE 71, Wind 51, Geotail 60, IMP 8 50.
- İndeks kaynakları: AE/AL/AU/SYM/ASY Kyoto geçici yüksek çözünürlüklü; PC(N) DTU kesin.
- Zaman damgası yay şoku burnuna kaydırılmış.

**Dolgu değerleri** ([HRO2 biçim dosyasından](https://spdf.gsfc.nasa.gov/pub/data/omni/high_res_omni/modified/hro_modified_format.txt); HRO ile aynı düzen): B 9999.99; hız 99999.9; yoğunluk 999.99; sıcaklık 9999999; basınç 99.99; elektrik alan 999.99; indeksler 99999; zaman kaydırma 999999. PC(N) dolgusu belgede okunmadı (biçimden çıkarım 999.99). CDF yolunda dolgular öznitelikte yazar; elle kodlama.

**Boşluk oranı.** 2001-2015 için belgelenmiş bir mutlak oran bulunamadı. Kendin ölç: yıl başına Bz(GSM), hız ve yoğunluk için dolgu oranı; ayrıca fırtına pencereleri içinde. HRO2'nin HRO'ya göre ek kaybı (bilgi için): 2001 %3,1; 2003 %2,4; 2005 %4,8; 2010 %9,9; 2013 %10,1; 2014 %9,4.

**Boşluk politikası (öneri).** 10 dakikaya kadar doğrusal ara değer; daha uzun boşlukta ilgili gecikme kutusunu "eksik" say, kutu ortalamasını kalan veriden al ve kutu başına "geçerli oran" özniteliği tut. Kutu geçerli oranı %50'nin altındaysa örneği at. Eşikleri pilotta sabitle. Büyük fırtınalarda plazma verisi tam da en kritik anda kesilebilir (29-30 Eki 2003); bu olayları elle gözden geçir.

## OMNI en büyük fırtınada boş (5 Eki 2026, sonradan; ölçüldü)

2003 yılı 1 dakikalık HRO dosyasının 28-30 Ekim kesitinde (bayt aralığı isteğiyle alındı; `../tests/fixtures/`):

| Gün | Bz (GSM) geçerli | Hız geçerli |
| --- | --- | --- |
| 28 Eki 2003 | %100 | %99,9 |
| 29 Eki 2003 | %45,5 | %44,7 |
| 30 Eki 2003 | %0 | %0 |

- 29 Eki 05:50 - 18:42 UT arasında ve 30 Eki boyunca IMF ve plazma sütunlarının tamamı dolgu; SYM-H ve AE kesintisiz.
- Yani en büyük iki fırtınanın ana evresinde OMNI'den sürücü özniteliği üretilemiyor ve Bz dönüşü epoku OMNI ile belirlenemiyor.
- Yedek (6 Eki 2026, ölçüldü): CDAWeb HAPI'den alınan ACE verisinde (`../data/raw/ace/`) **MFI manyetik alan 28, 29 ve 30 Ekim'de %100 dolu**, OMNI boşluğunda (29 Eki 05:50-18:42) 2898 kayıt kesintisiz; **SWEPAM plazma 29 ve 30 Ekim'de %0**, 28 Ekim'de %51. Yani yedek Bz'yi geri getiriyor, hız ve yoğunluğu getirmiyor; Em bu günlerde hesaplanamaz, yalnız Bz tabanlı öznitelikler ve indeksler kalır. ACE L1'de olduğu için kendi zaman kaydırmamız gerekir (`solar_wind/ace.py`: balistik gecikme, dakika ortalaması). Hedef x konumu açık parametre; OMNI'nin faz cephesi yöntemi yeniden üretilmiyor.
- **Gecikme hatası ölçüldü (6 Eki 2026, `kanit/ace_gecikme_olcum_cikti_2026-10-06.txt`):** 28 Eki 2003'te OMNI'nin IMF kaynağı Geotail (kimlik 60, ~30 Re), ACE 231 Re'de. ACE konumu, SWEPAM vx'i ve OMNI'nin yay şoku x'i ile balistik gecikme ortanca 2288 s (p10-p90: 1750-2804). Kaydırılmış ACE Bz ile OMNI Bz arasında 1369 ortak dakikada r = 0,73, RMS fark 3,0 nT (OMNI Bz std 4,1 nT); ek gecikme taraması en iyi değeri **+7 dk** veriyor (r 0,75, RMS 2,9 nT), yani balistik gecikme birkaç dakika kısa kalıyor. Tek gün; genel bütçe değil. 29-30 Ekim'de SWEPAM vx olmadığından gecikme için hız dışarıdan (son geçerli değer ya da katalog hızı) verilmeli.
- Yapılacak: yıllık dosyalar indiğinde **her fırtına penceresi için** Bz, hız ve yoğunluk kapsam tablosu. Aşağıdaki "boşluk politikası" bu tabloya göre sabitlenmeli.
- Ayrıntı ve test: `11_space_environment_modulu.md`.

## Jeomanyetik indeksler

**GFZ** `[OKUNDU]`

| Dosya | Boyut | İçerik |
| --- | --- | --- |
| [Kp_ap_Ap_SN_F107_since_1932.txt](https://kp.gfz.de/app/files/Kp_ap_Ap_SN_F107_since_1932.txt) | 5,5 MB | günlük satır; 8 Kp, 8 ap, Ap, SN, **F10.7obs, F10.7adj**, D |
| [Kp_ap_since_1932.txt](https://kp.gfz.de/app/files/Kp_ap_since_1932.txt) | 16,6 MB | 3 saatte bir satır |
| [Hp30_ap30_complete_series.txt](https://kp.gfz.de/app/files/Hp30_ap30_complete_series.txt) | 43,9 MB | 30 dakikalık; 1985-01-01'den |
| [Hp60_ap60_complete_series.txt](https://kp.gfz.de/app/files/Hp60_ap60_complete_series.txt) | 22,0 MB | 60 dakikalık |

- Günlük dosya: 40 başlık satırı (`#`); eksik değer Kp −1.000, ap −1, F10.7 −1.0.
- Hp30 dosyası: 30 başlık satırı; sütunlar `YYYY MM DD hh.h hh._m days days_m Hp30 ap30 D`.
- Lisans: CC BY 4.0 (güneş lekesi sayısı CC BY-NC 4.0). Atıf: Matzka ve ark. 2021 (doi 10.1029/2020SW002641); Hpo için Yamazaki ve ark. 2022 (doi 10.1029/2022GL098860) ve veri doi 10.5880/Hpo.0003.
- JSON API (canlı sınandı): `https://kp.gfz.de/app/json/?start=2003-10-29T00:00:00Z&end=2003-10-29T23:59:59Z&index=Kp&status=def` → `Kp: [4.667, 4.0, 9.0, 8.0, 7.667, 7.667, 8.667, 8.667]`. İndeks adları: `Kp, ap, Ap, Cp, C9, Hp30, Hp60, ap30, ap60, SN, Fobs, Fadj`.
- Toplu iş için dosyaları indir; API yalnız nokta kontrolü için.

**Kyoto WDC** `[OKUNDU]`

- Dst: kesin 1957-2020 (2001-2015 tamamı kesin); geçici 2021/01-2026/07; sonrası anlık.
- SYM-H/ASY-H: 1981'den, 1 dakikalık; "Best Available ... (currently Provisional only)".
- HAPI: `https://wdc.kugi.kyoto-u.ac.jp/hapi/`; veri kümeleri `hour_dst_final`, `min_asysym`, `min_ae`, `hour3h_kp`. Sınanan çağrı: `.../hapi/data?id=hour_dst_final&start=2003-10-30T20:00:00Z&stop=2003-10-31T00:00:00Z` → 22:29:30'da −383 nT. `min_asysym` için tek istekte en çok 366 gün; dolgu 99999.
- Koşullar ([Sec3](https://wdc.kugi.kyoto-u.ac.jp/wdc/Sec3.html)): bilimsel kullanım serbest; ticari kullanım yok; anlık veriyi yayında kullanmadan önce iletişim; veri DOI'lerini kaynakçaya koy. DOI: Dst 10.17593/14515-74000; AE 10.17593/15031-54800; ASY/SYM 10.14989/267216.

**Hangi SYM-H?** OMNI içindeki SYM-H de Kyoto'dan geliyor. Öneri: OMNI'dekini kullan (tek dosya, aynı zaman ekseni); Kyoto HAPI'den iki fırtına çekip birebir aynı olduğunu bir kez doğrula. Dst yalnız Richardson-Cane kataloğuyla çapraz kontrol için gerekli.

## Güneş aktivitesi

**F10.7** `[OKUNDU]`

- Kaynak: GFZ günlük dosyasındaki `F10.7obs`. Sınama: 27-31 Eki 2003 için `Fobs = [257.2, 274.4, 291.7, 271.4, 248.9]`, `Fadj = [254.0, 270.9, 287.7, 267.6, 245.2]`.
- **MSIS gözlenen akıyı ister** (1 AU'ya düzeltilmiş olanı değil). Dayanaklar: pymsis belgesi; NRLMSISE-00'ın bir C uyarlamasının başlığı ("at the actual distance of the Earth from the Sun rather than the radio flux at 1 AU"); NRCan ("this is the quantity to use when terrestrial phenomena are being studied"); GFZ biçim belgesi ("For ionospheric and atmospheric studies we recommend F10.7obs"). Özgün NRL Fortran kaynağı açılmadı.
- MSIS girdisi: önceki günün F10.7'si ve güne ortalanmış 81 günlük ortalama. Pencerenin tam tanımı (gün −40 … +40, aritmetik ortalama) hiçbir kaynakta açık yazmıyor; çıkarım. CelesTrak `SW-All.csv` içindeki hazır ortalamayla bir tarihte karşılaştır.
- Günlük F10.7'de parlama kaynaklı aykırı değerler olabilir (2001'de günlük en yüksek 655,6 sfu). 81 günlük ortalamayı etkiler mi, bak; pymsis 0.9.0'dan beri belirgin patlamaları kendi indirdiği veride ayıklıyor, GFZ dosyası ayıklamıyor olabilir.
- LASP LISIRD'e ulaşılamadı `[DOĞRULANMADI]`; gerek yok.

**JB2008 indeksleri (SET)** `[OKUNDU, başlık ve son satırlar]`

- [SOLFSMY.TXT](https://sol.spacenvironment.net/JB2008/indices/SOLFSMY.TXT) (0,84 MB): `YYYY DDD JulianDay F10 F81c S10 S81c M10 M81c Y10 Y81c Ssrc`; 1997 gün 1 - 2026 gün 233. Başlık notu: "F10 and S10 are 1-day lagged, M10 is 2-day, and Y10 is 5-day lagged in JB2008".
- [DTCFILE.TXT](https://sol.spacenvironment.net/JB2008/indices/DTCFILE.TXT) (1,19 MB): başlıksız; `DTC YYYY DDD` + 24 tam sayı (saatlik sıcaklık düzeltmesi, K; çıkarım).
- Ayrıca `SOLRESAP.TXT`, `DSTFILE.TXT`. Dosyalar her gün yenileniyor, içerik yaklaşık 45 gün geriden geliyor.
- Fortran kaynağı: `sol.spacenvironment.net/JB2008/code/JB2008.for.txt` (25,8 kB).
- Lisans: ücretsiz ve kısıtsız dağıtım, teşekkür şartı; yazılımı ve onu süren veri ürünlerini değiştirme/uyarlama yasağı var.
- Kullanım: S10, M10, Y10 B katmanı öznitelikleri; JB2008 koşulursa girdi.

**Güneş çevrimi bağlamı** (SILSO 13 aylık düzgünleştirilmiş, v2.0 `[OKUNDU]`)

| Olay | Tarih | Düzgünleştirilmiş SN |
| --- | --- | --- |
| 23. çevrim en yüksek | Kas 2001 | 180,3 |
| 23/24 en düşük | Ara 2008 | 2,2 |
| 24. çevrim en yüksek | Nis 2014 | 116,4 |

Gözlenen F10.7 yıllık ortalamaları (GFZ API'den hesap): 2001 = 184,4; 2002 = 180,1; 2008 = 69,0; 2014 = 146,2 sfu.

Sonuçlar:

- Fırtınaların çoğu 2001-2005'te (ICME satırları: 2001'de 48, 2007'de 2). CHAMP bu dönemde 440-360 km'de: sinyal açısından en iyi veri.
- 2007-2009: 16 ICME, F10.7 yaklaşık 69, GRACE'te radyasyon basıncı aerodinamik ivme kadar. Bu yılları çıkarmak fırtına sayısından çok az götürür.
- 2011-2015 (142 ICME) yalnız GRACE; GRACE o sırada 465 km'den 385 km'ye iniyor ve F10.7 orta düzeyde: kullanılabilir.

## Gerçek zamanlı karşılıklar (A katmanının savunması)

| Büyüklük | Gerçek zamanlı ürün | Durum |
| --- | --- | --- |
| IMF, plazma | SWPC `services.swpc.noaa.gov/json/rtsw/rtsw_mag_1m.json`, `rtsw_wind_1m.json`; 1 dk, son 24 sa | `[OKUNDU]` Eski `products/solar-wind/*.json` yolları 404 |
| Dünya'ya yayılmış güneş rüzgarı | `products/geospace/propagated-solar-wind-1-hour.json` | `[OKUNDU]` Gözlenen öndelik: 581 km/s'de 39,6 dk |
| Kp | SWPC 3 saatlik ve 1 dakikalık kestirim; GFZ anlık dosya | `[OKUNDU]` |
| Hp30/ap30 | GFZ `Hp30_ap30_nowcast.txt` | `[OKUNDU]` 18:56 UTC'de 18:00-18:30 aralığı mevcuttu: gecikme yaklaşık 30 dk'nın altında |
| Dst | Kyoto anlık, saatlik (SWPC `products/kyoto-dst.json`) | `[OKUNDU]` |
| **SYM-H** | **Yok.** Kyoto HAPI'de 1 Eki 2026 sonrası boş; anlık ASY/SYM veri kümesi yok | `[OKUNDU]` |
| F10.7 | Günlük | — |

- L1 öndeliği: 1,5 milyon km; 400 km/s'de yaklaşık 62 dk, 800 km/s'de yaklaşık 31 dk (hesap). Hızlı fırtına akışında öndelik yarıya iniyor; H3 ile aynı yönde bir etki.
- **SYM-H sorunu için karar gerekli.** Seçenekler: (a) A katmanında SYM-H yerine ap30 ve saatlik Dst kullan, SYM-H'yi B katmanına taşı; (b) SYM-H'yi A'da tut, "gerçek zamanlı karşılığı saatlik Dst'dir" diye yaz. Öneri: (a). Daha dürüst, ve B3'ü gereksiz güçlendirip kutup kazancını yapay olarak küçültmez; B katmanı duyarlılığı zaten SYM-H'li durumu raporlar. Ön kayıt belgesine yaz.

## İndirme listesi

| Veri | Yol | Boyut |
| --- | --- | --- |
| OMNI HRO 1 dk, 2001-2015, CDF | pyspedas | yaklaşık 1,5 GB |
| GFZ günlük + 3 saatlik + Hp30 | 3 dosya | 66 MB |
| SOLFSMY, DTCFILE | 2 dosya | 2 MB — **indirildi 6 Eki 2026** (sürüm 8_1_0, 1997-2026) |
| Kyoto Dst (HAPI) | 15 yıl saatlik | küçük — Ekim-Kasım 2003 indirildi (`hour_dst_final`, CSV + info JSON) |
| Richardson-Cane xlsx | Dataverse | 82 kB — indirildi |
| ACE MFI (16 s) ve SWEPAM (64 s), CDAWeb HAPI | fırtına pencereleri | 28-30 Eki 2003 indirildi (1,8 MB); tüm fırtınalar için pencere başına ~0,6 MB/gün |
| Zenodo 7667515 `Heating_DeltaT.h5` | 1 dosya | 58 MB — indirildi |
| SILSO aylık, düzgünleştirilmiş, çevrim tablosu | 3 dosya | 250 kB — indirildi |

Hedef dizin: `data\raw\{omni,gfz,set,kyoto,ace,heating,silso,catalog}\`. Her dosya için indirme tarihi, kaynak adresi ve SHA-256 bir bildirim dosyasına yazılır; GFZ ve SET dosyaları sürekli güncellendiği için indirilen kopya dondurulur.

## Doğrulama testleri (indirmeden sonra)

- [ ] OMNI: 29 Eki 2003 06:00-06:05 SYM-H, Kyoto HAPI ile aynı (ajan −34 nT ile başlayan 5 satır okudu).
- [ ] GFZ: 29 Eki 2003 Kp dizisi yukarıdaki değerler.
- [x] JB2008 girdileri bağımsız uygulamayla çapraz kontrol (6 Eki 2026, `kanit/jb2008_pyatmos_capraz_kontrol_cikti_2026-10-06.txt`): pyatmos 1.2.7 aynı SET dosyalarını okuyor; üç epokta gecikmeli F10/S10/M10/Y10 ve 81 günlük değerler **birebir aynı**. DTCFILE'ı pyatmos "k. değer k:30 UT'de geçerli, aralar doğrusal" diye yorumlayıp kernel'e `DSTDTC` olarak veriyor; `dtc_at(..., interpolate=True)` bunu yeniden üretiyor (07:04 için 220,27). Birim (K) hâlâ birincil belgeyle doğrulanmadı. pyatmos paketi içe aktarılırken IERS dosyası indiriyor; Sidera'nın "ağ yok" ilkesiyle çelişir, adaptör için kernel ayrı paketlenmeli.
- [x] OMNI 5 dakikalık biçim gerçek yıllık dosyayla sınandı (6 Eki 2026): `omni_5min2003.asc` (34 MB) 49 alan, 105 120 kayıt, 2,3 s; 28 Eki 12:00 kaydı ve Halloween boşluğu 1 dakikalık ile tutarlı; kesit `tests/fixtures/omni_5min_2003_doy301_303_excerpt.asc`.
- [x] Dst: 30 Eki 2003 22-23 UT = −383 nT (6 Eki 2026, Kyoto `hour_dst_final` CSV ile; okuyucu merkez damgasını saat başına çeviriyor, test `test_hapi_ace_kyoto.py`).
- [ ] F10.7: 27-31 Eki 2003 yukarıdaki beş değer.
- [ ] Yıl başına OMNI dolgu oranı tablosu.
