# 03 — Atmosfer referans modeli

Hazırlanma: 5 Ekim 2026. Ana plan: `../00_ana_plan.md`, "Değişken tanımları ve ön işleme".

**Etiketler.** `[ÖLÇÜLDÜ]` bu makinede koşulup çıktısı kaydedildi. `[OKUNDU]` kaynak sayfa/kod bu oturumda açıldı (ajan, özetleyici bir sayfa okuyucu üzerinden; imzalar kurulu paketten ayrıca teyit edildi). `[DOĞRULANMADI]` açılamadı ya da hafızadan.

## Karar

Birincil referans: **pymsis 0.13.0 ile NRLMSIS 2.1, ap dizisi 7 elemanı da 4'e sabit, günlük Ap kipi.**
İkincil referans (yalnız Oliveira ile karşılaştırma adımı için): JB2008, Dst sıcaklık düzeltmesi sıfır.

Gerekçe:

- Windows tekerleği var, derleyici gerekmiyor; yörünge boyunca vektörel çalışıyor.
- "ap = 4" ile "jeomanyetik anahtarı kapat" **aynı yoğunluğu** veriyor (aşağıda ölçüm). Yani tezde tek cümleyle tanımlanabilen "Ap = 4 sakin durum" seçilebilir; anahtar kapatma ayrı bir duyarlılık koşusu gerektirmez.
- MSIS 2.0 ve 2.1 toplam kütle yoğunluğu 400 km'de aynı çıktı; sürüm seçimi bu irtifada önemsiz.

## Bu makinede ölçülenler `[ÖLÇÜLDÜ]`

Betik: `kanit/msis_check.py`. Çıktı: `kanit/msis_check_cikti_2026-10-05.txt`. Ortam: `D:\sidera\.venv` (Python 3.10.20, pymsis 0.13.0).
Kurgu: 100.000 nokta, 10 s aralık, 400 km sabit irtifa, 87,3° eğimli sentetik iz, F10.7 = 150, F10.7a = 140, başlangıç 29 Eki 2003.

| Karşılaştırma | ln-oran ortalaması | en büyük mutlak |
| --- | --- | --- |
| anahtar kapalı (ap=4) / ap=4 | +0,00000 | 0,00000 |
| anahtar kapalı (ap=80) / anahtar kapalı (ap=4) | +0,00000 | 0,00000 |
| ap=80 günlük kip / ap=4 | +0,336 | 0,481 |
| ap=80 fırtına kipi / ap=4 | +0,367 | 0,487 |
| MSIS 2.0 / MSIS 2.1 (ap=4) | +0,00000 | 0,00000 |
| MSISE-00 / MSIS 2.1 (ap=4) | +0,163 | 0,229 |

- Hız: **yaklaşık 16.000 nokta/s**, tek süreç.
- Anahtar kapatma: `geomagnetic_activity=0, mixed_ap_ut_long=0`.
- Sınır: tek irtifa, tek güneş akısı, sentetik iz. Gerçek CHAMP/GRACE izinde ve düşük F10.7'de bir kez daha koşulmalı (aşağıda adım 2).
- MSISE-00 sakin durumda 2.1'den ortalama %16 kadar yüksek. Fırtına öncesi yanlılık terimi bunu emer, ama sürümü teze yaz.

## Gerçek CHAMP izinde tekrar `[ÖLÇÜLDÜ]`

Betik: `kanit/gercek_iz_kontrol.py`. Çıktı: `kanit/gercek_iz_kontrol_cikti_2026-10-05.txt`. Veri: ESA V2, VirES HAPI üzerinden; F10.7 GFZ API'den (gözlenen akı, önceki gün; 81 günlük ortalanmış ortalama kendi hesabım).

| Dönem | Kayıt | İrtifa (km) | ln(anahtar kapalı / ap=4) | ln(gözlem / MSIS 2.1, ap=4) |
| --- | --- | --- | --- | --- |
| 27 Eki - 1 Kas 2003 (fırtına) | 43.200 | 390-419 | tam 0 | ortalama −0,044; std 0,363 |
| 1 Tem 2008 (güneş minimumu) | 8.640 | 329-358 | tam 0 | ortalama −0,363; std 0,193 |

- "ap = 4 ≡ anahtar kapalı" gerçek izde ve iki uç güneş akısında da tutuyor (F10.7: 257-298 ve 66,7). Aşağıdaki "İş adımları 2" kapandı.
- Güneş minimumunda MSIS 2.1 gözlemin üstünde: oran `exp(−0,363) ≈ 0,70`. Tek gün; ama Siemes 2023'ün "modeller minimumda fazla tahmin ediyor" bulgusuyla aynı yönde. Fırtına başına yanlılık terimi bu yüzden şart.
- Ekim 2003'te fırtına öncesi 24 saat yanlılığı küçük: alçak enlem −0,089, kuzey kutup −0,037, güney kutup −0,083. Bantlar arasında 0,05'lik fark var; `b_s`'yi bant başına almak (bkz. `04`) yerinde.

## pymsis arayüzü

Kurulu paketten okunan imza `[ÖLÇÜLDÜ]`:

```python
pymsis.calculate(dates, lons, lats, alts, f107s=None, f107as=None, aps=None, *,
                 options=None, version=2.1, interpolate_indices=False, **kwargs)
```

- Sıra: tarih, **boylam, enlem**, irtifa (km). Boylam enlemden önce.
- Tüm diziler aynı uzunluktaysa yörünge kipi; çıktı `(N, 11)`.
- `pymsis.Variable`: MASS_DENSITY=0, N2=1, O2=2, O=3, HE=4, H=5, AR=6, N=7, ANOMALOUS_O=8, NO=9, TEMPERATURE=10.
- `create_options` adları: f107, time_independent, symmetrical_annual, symmetrical_semiannual, asymmetrical_annual, asymmetrical_semiannual, diurnal, semidiurnal, geomagnetic_activity, all_ut_effects, longitudinal, mixed_ut_long, mixed_ap_ut_long, terdiurnal.

Belgelerden `[OKUNDU]`:

- `f107s`: önceki günün günlük F10.7'si. `f107as`: tarihe ortalanmış 81 günlük ortalama. Akı Güneş-Dünya uzaklığında (gözlenen), 1 AU'ya düzeltilmiş değil. ([calculate belgesi](https://swxtrec.github.io/pymsis/reference/generated/pymsis.calculate.html))
- `aps` 7 eleman: günlük Ap; şimdiki 3 saatlik ap; 3, 6, 9 saat önceki; 12-33 saat ortalaması; 36-57 saat ortalaması. 1-6 yalnız `geomagnetic_activity=-1` iken kullanılır.
- İndeksler verilmezse paket `https://celestrak.org/SpaceData/SW-All.csv` dosyasını indirip **paket dizinine** önbellekler. ([utils.py](https://raw.githubusercontent.com/SWxTREC/pymsis/main/pymsis/utils.py))
- Belgeler sakin referans için bir yöntem önermiyor. "Ap = 4" seçimi bizim tasarımımız; dayanağı yukarıdaki ölçüm.
- Eşzamanlı çağrılar sırayla çalışır; iş parçacığı hız kazandırmaz. ([README](https://raw.githubusercontent.com/SWxTREC/pymsis/main/README.md))
- MSIS 2 kodunun ticari kullanımı NRL iznine bağlı; akademik kullanımda sorun yok.

`[DOĞRULANMADI]`: SW-All.csv'deki F10.7 sütununun gözlenen mi düzeltilmiş mi olduğu sütun adından teyit edilmedi.

## İş adımları

1. **İndeks dosyasını dondur.** F10.7 ve F10.7a'yı her zaman açıkça ver; otomatik indirmeye bırakma. Kaynak GFZ dosyası (bkz. `02_gunes_ruzgari_ve_indeksler.md`). Önceki gün kaydırmasını ve 81 günlük ortalamayı kendi kodunda yap, birim testi yaz (bir tarihte elle hesapla karşılaştır).
2. **Gerçek izde tekrar.** Bir aylık CHAMP dosyası indiğinde ölçümü gerçek konumlarla ve bir güneş minimumu ayıyla (2008) yinele; tablonun ilk iki satırı yine sıfır çıkmalı. Çıkmazsa "ap = 4" tanımını gözden geçir.
3. **Referans yoğunluğu üret.** Her yoğunluk kaydı için `rho_ref = MSIS2.1(konum, zaman, F10.7 gerçek, ap = 4)`. Yıllık parçalar halinde, parquet'e yaz.
4. **Hedef değişken.** `y = ln(rho_obs / rho_ref) − b_s`; `b_s` fırtına başlangıcından önceki 24 saatin ortalaması (ana plan).
5. **Oliveira karşılaştırması için** 410 km'ye taşıma: `rho_410 = rho_obs × rho_ref(410) / rho_ref(h_uydu)`. Bu, nokta başına ikinci bir model çağrısı demek.

**Hesap bütçesi (ölçülen hızdan türetme).** 10 s aralıkla bir uydu-yıl yaklaşık 3,15 milyon nokta, yani yaklaşık 3,3 dakika. CHAMP (yaklaşık 9 yıl) + GRACE-A (yaklaşık 13,5 yıl) yaklaşık 71 milyon nokta: tek süreçte **1,2 saat**, 410 km taşımasıyla 2,5 saat. Süreç havuzuyla bölünebilir. Darboğaz değil.

## JB2008 (ikincil)

Oliveira 2017'nin yaptığı `[OKUNDU, arXiv PDF s. 1-4]`:

- Tüm yoğunluk JB2008 ile 410 km'ye taşınıyor: ρ410 = (ρJB,410 / ρJB) × ρ.
- Sakin yoğunluk: "the model input with no Dst correction, or ΔT_Dst = 0", 410 km için; analiz edilen büyüklük log10(ρ410 / ρQ,410).
- CHAMP-GRACE ara kalibrasyonu bu sayfalarda anlatılmıyor; ayrıntı eşlik eden JGR makalesinde (açılmadı).

Python seçenekleri:

| Seçenek | Durum | Not |
| --- | --- | --- |
| [pyatmos 1.2.7](https://pypi.org/pypi/pyatmos/json) | Son sürüm ve son commit 5 Kas 2024, MIT `[OKUNDU]` | Üst düzey `jb2008(t, konum, swdata)` tek noktalık ve DTC'yi dışarıdan almıyor |
| pyatmos çekirdeği | `JB2008(AMJD, YRDAY, SUN, SAT, F10, F10B, S10, S10B, M10, M10B, Y10, Y10B, DSTDTC)`, numba `[OKUNDU]` | **DSTDTC = 0 doğrudan verilebilir.** Güneş konumu ve gecikmeli indeksleri kendin hazırlarsın |
| [SET resmi Fortran 77](https://spacewx.com/jb2008/) | "Python wrapper" ile birlikte zip `[OKUNDU, zip indirilmedi]` | Lisans sayfada yazmıyor |
| Orekit | JB2008 sınıfı var `[DOĞRULANMADI, arama özeti]` | Java bağımlılığı |

Öneri: JB2008'i yalnız hat doğrulaması haftasında (hafta 3), pyatmos çekirdeğiyle, 30 pilot fırtına için kullan. Önce birkaç noktayı resmi Fortran çıktısıyla karşılaştır; pyatmos az bakım görüyor. Zenodo 4602380 gerçekten yörünge boyunca JB2008 içeriyorsa (bkz. `01_yogunluk_verisi.md`) bu adım büyük ölçüde gereksizleşir, ama oradaki JB2008 fırtına terimi açık halidir; sakin referans yerine geçmez.

## Kullanılmayacaklar

- **DTM2020.** Kod açık ([swami-h2020-eu/mcm](https://github.com/swami-h2020-eu/mcm)), ama Python sarmalayıcı bir çalıştırılabiliri nokta nokta çağırıyor ve hazır ikili yalnız Ubuntu 18.04 için `[OKUNDU]`. Windows'ta ve on milyonlarca noktada pratik değil.
- **HASDM.** 2000-2019 (+2020-2025 uzantısı), 10°×15°, 175-825 km, 3 saatlik; yalnız araştırma amaçlı ücretsiz, erişim başvuru/API ile ([SET](https://spacewx.com/hasdm/)) `[OKUNDU, kısmi]`. Fırtına tepkisini içerdiği için sakin referans olamaz; isteğe bağlı karşılaştırma verisi.

## MSIS sürümleri hakkında bilinen ve bilinmeyen

- 2.1, 2.0'a yalnız NO ekliyor ([CCMC](https://ccmc.gsfc.nasa.gov/models/NRLMSIS~2.1/)) `[OKUNDU]`; yukarıdaki ölçüm 400 km'de kütle yoğunluğunun aynı olduğunu gösteriyor.
- Emmert ve ark. 2021 (doi 10.1029/2020EA001321), [NOAA deposundaki açık kopya](https://repository.library.noaa.gov/view/noaa/53074/noaa_53074_DS1.pdf) `[OKUNDU, sonradan; hedefli bölümler]`:
  - Uydurmada yalnız **yörüngeden türetilmiş günlük küresel ortalama yoğunluk** kullanılmış (250-575 km, yaklaşık 5000 nesnenin TLE'leri, 1986-2005 uydurma). **İvmeölçer verisi uydurmada yok**; CHAMP ve GOCE yalnız doğrulamada, GRACE hiç anılmıyor.
  - CHAMP doğrulama örneği "excluding the anomalous solar minimum years 2005–2009".
  - "The MSIS 2.0 mass densities are ~10% lower than MSISE-00"; N2 yaklaşık %20 düşük. Yazarlar termosferi büyük ölçüde MSISE-00'dan koruduklarını ve büyük bir yükseltmeyi ertelediklerini söylüyor.
  - Bizim ölçüm: MSISE-00, 2.1'den ortalama %16 yüksek (400 km, F10.7 = 150, ap = 4); makaledeki "yaklaşık %10" ile aynı yönde.
  - Sonuç: referans model CHAMP/GRACE'i görmemiş; hedef değişken ile referans arasında döngüsellik yok. Fırtına (ap) bağımlılığı MSISE-00'dan miras; zaten kapatıyoruz.
  - CHAMP'e göre yanlılık sayıları ek veri setinde (S6); okunmadı.
- Emmert ve ark. 2022 (doi 10.1029/2022JA030896) açılamadı.

## Sidera ile ilişki

`D:\sidera` (commit `6dcb8f63`, 5 Eki 2026) `src/sidera/physics/atmosphere/models.py` içinde `NrlmsiseAtmosphere` sınıfıyla pymsis'i sarıyor; sürüm "00", "2.0", "2.1" seçilebiliyor, uzay havası `SpaceWeatherProvider` ile dışarıdan veriliyor. Sidera'da JB2008 yok (kaynakta arandı). Ayrıntı: `08_yorunge_etkisi_sidera.md`.

## Açık noktalar

- [x] Gerçek izde ve güneş minimumunda "ap = 4 ≡ anahtar kapalı" tekrarı (5 Eki 2026, yukarıda).
- [ ] F10.7: gözlenen akı kullanıldığını GFZ sütunundan teyit et.
- [ ] Emmert 2021/2022 tam metin.
- [ ] pyatmos çekirdeğinin resmi Fortran'la nokta karşılaştırması (yalnız JB2008 kullanılacaksa).
