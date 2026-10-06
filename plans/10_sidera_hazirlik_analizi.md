# 10 — Sidera hazırlık analizi: tezin ne kadarı hazır, ne eklenmeli

Hazırlanma: 5 Ekim 2026. İncelenen depo: `D:\sidera`, commit `6dcb8f63` (5 Eki 2026); çalışma ağacında işlenmemiş değişiklikler vardı.

**Yöntem ve sınır.** Depoyu salt okunur bir araştırma ajanı taradı (kod koşmadan, dosya ve satır numarasıyla). Kararı etkileyen altı noktayı kendim kaynaktan yeniden okudum; bunlar `[DOĞRULADIM]` ile işaretli. Kalanı `[AJAN OKUDU]`. Bir nokta uçtan uca koşuldu: `[ÇALIŞTIRDIM]`. Hız hakkındaki her şey koddan çıkarım; ölçülmedi.

## Özet

Sidera tezin **yayılım yarısını** büyük ölçüde karşılıyor: Dünya alçak yörüngesi, küresel harmonik çekim, Güneş/Ay, ışınım basıncı, top modeliyle sürüklenme, iz boyunca (RIC) ayrıştırma, UTC/TDB, Dünya yönelimi. En önemlisi, sürüklenme **kullanıcının yazdığı herhangi bir atmosfer nesnesiyle** sürülebiliyor.

**Veri ve bilim yarısı** yok: yoğunluk verisi okuma, güneş rüzgarı ve jeomanyetik indeksler, manyetik enlem, istatistik tahmin, ölçülmüş yoğunluğu atmosfer modeli olarak kullanma, koşu başına farklı atmosferle toplu çalıştırma.

Kabaca: yörünge bölümü için gereken altyapının çoğu hazır, eksik olan üç küçük sınıf ve bir sürücü betik. Tezin ana gövdesi (tahmin deneyi) Sidera'nın dışında, bu projede kurulacak.

## İhtiyaç tablosu

| Tez ihtiyacı | Durum | Dayanak | Eklenecek |
| --- | --- | --- | --- |
| Alçak yörünge yayılımı (çekim, üçüncü cisimler, ışınım, sürüklenme) | Hazır | `core/config.py` `load_body_config`; `core/body_engine/orbits.py:639` `propagate_body_orbit` `[DOĞRULADIM: imza]` | Yok |
| Keyfi atmosfer modeliyle sürüklenme | Hazır (arayüz) | `AtmosphereModel` protokolü `physics/atmosphere/models.py:114`; `AtmosphericDrag(atmosphere=...)` `core/drag/aerodynamics.py:198` `[DOĞRULADIM]` | Yok; ama hazır bir "ölçülmüş yoğunluk" sınıfı yok |
| Ölçülmüş yoğunluğu "doğruluk" olarak kullanma | Eksik | Zamana göre tablo modeli yok; `AtmosphereProfile` yalnız kendi dosyasında geçiyor `[DOĞRULADIM: 6 eşleşme, tek dosya]` | `TabulatedTrackAtmosphere` (aşağıda E1) |
| Bant içinde tahmin, dışında ölçüm | Eksik | — | Bileşik model (E2) |
| Sabit balistik katsayı, birkaç değer | Hazır | `SpacecraftProps` (kütle, alan, C_D) `[AJAN OKUDU]` | Yok. **Tanım farkı:** Sidera `ballistic_coefficient = m/(C_D·A)` [kg/m²] tutuyor; tez planı `C_D·A/m` kullanıyor |
| İz boyunca fark | Hazır | `frames/local_orbital.py:109` `to_ric` `[DOĞRULADIM: imza]` | İnce bir karşılaştırma işlevi |
| Binlerce kısa koşu (epok × katsayı) | Kısmi | `backends/body_batch.py:38-40` çalışma zamanı sürüklenmesini reddediyor: "A runtime AtmosphericDrag holds per-run state and cannot be shared" `[DOĞRULADIM]` | Kendi döngümüz: koşu başına yeni sürüklenme nesnesi, süreç havuzu (E4) |
| F10.7, ap, Kp | Kısmi | `physics/atmosphere/space_weather.py`: günlük CSV, `f107a` hazır verilmeli, **`ap_history` hiç doldurulmuyor** (`_state`, satır 329-336) `[DOĞRULADIM]` | Bu projede yazıldı ve Sidera ile çalıştırıldı (aşağıda) |
| Fırtına kipinde NRLMSIS'i gerçek indekslerle sürme | Eksikti | Yukarıdaki boşluk yüzünden CSV'den mümkün değildi | **Kapandı** `[ÇALIŞTIRDIM]`: `space_environment` köprüsüyle Sidera'nın `NrlmsiseAtmosphere(storm_mode=True)` sınıfı gerçek GFZ indeksleriyle yoğunluk üretti (test: `tests/test_sidera_bridge.py`) |
| Güneş rüzgarı, IMF, SYM-H/Dst | Eksik | Kaynakta hiçbir iz yok `[AJAN OKUDU]` | Bu projede: `space_environment.solar_wind` (okuyucu ve bağlaşım fonksiyonları yazıldı) |
| Manyetik enlem (bant kapısı) | Kısmi | IGRF-14 var: `physics/geomagnetism/igrf.py:163` `north_geomagnetic_pole_deg` `[DOĞRULADIM: imza]`; QD/apex/AACGM yok | Seçenek: apexpy (bu makinede kuruldu) ya da dipol enlem (E3) |
| Yerel güneş zamanı | Kısmi | Güneş açıları `models.py` içinde, genel işlev yok `[AJAN OKUDU]` | Küçük yardımcı; yoğunluk dosyasında hazır sütun olduğu için acil değil |
| CHAMP/GRACE yoğunluk dosyası okuma | Eksik | CDF, SP3 okuyucu yok `[AJAN OKUDU]` | Bu projede: `cdflib` ile okuyucu (CDF bugün açıldı) |
| Başlangıç durumu (gerçek yörüngeden) | Kısmi | TLE/SGP4, CCSDS OEM okuyucu; konumdan en küçük kareler `estimation/batch.py` `[AJAN OKUDU]` | Aşağıda "Başlangıç durumu" |
| İstatistik tahmin modelleri | Eksik, ve öyle kalmalı | — | Bu projede; Sidera'nın motor katmanlarına girmemeli |
| JB2008, DTM | Eksik | Plan da yok `[AJAN OKUDU]` | Tez için gerekmiyor (bkz. `03`) |

## Dikkat edilecek üç tuzak

**1. Zaman ölçeği sabiti 2017 öncesi için yanlış.** `[DOĞRULADIM]` `common/timekeeping/scales.py:706-726`: `EpochConversion.tdb_minus_utc_s` varsayılanı 69,184 s ve belge dizgisi "holds from 2017-01-01 ... before that it is 1 s per leap second too large" diyor. `AtmosphericDrag` bunu varsayılan olarak alıyor (`aerodynamics.py:206`), atmosfer modeline giden UTC bundan türetiliyor (`aerodynamics.py:247`).

- Sidera bunu yerel güneş zamanı için ihmal edilebilir sayıyor. **Bizim için değil:** yoğunluğu zamana göre tablodan okuyacağız. 2003'te fark 5 saniye; uydu 5 saniyede yaklaşık 38 km gider, yani tablo yanlış konumun yoğunluğunu verir.
- Çözüm: her koşuda `EpochConversion(tdb_minus_utc_s=TAI−UTC + 32,184)` açıkça ver. TAI−UTC: 2001-2005 için 32 s, 2006-2008 için 33 s, 2009 - Haz 2012 için 34 s, Tem 2012 - Haz 2015 için 35 s, sonrası 36 s. Bu değerleri hafızadan yazdım; Sidera'nın kendi `LEAP_SECONDS` tablosundan (`scales.py`, 738. satır civarı) okuyup kullan.
- Sınama: tablo modelinin aldığı `sample.utc` ile yoğunluk dosyasındaki zaman damgası aynı noktada 1 saniyeden yakın olmalı.

**2. Balistik katsayı tanımı ters.** Sidera `m/(C_D·A)`, tez planı ve Emmert `C_D·A/m`. Karşılaştırma betiğinde tek bir tanım kullan, adını değişkene yaz (`cd_a_over_m_m2_kg`).

**3. Dünya dönüşü sadeleştirilmiş.** `[AJAN OKUDU]` Sürüklenme yolunda eylemsiz → cisme bağlı dönüşüm yalnız z ekseni etrafında dönme; presesyon eğimi modellenmiyor (belgelere göre 2010'da yaklaşık 0,06°). Yaklaşık 400 km'de bu yaklaşık 7 km'lik konum farkı demek (hesap: 0,06° × 6771 km); tabloyu zamana göre okuduğumuz için yoğunluğa etkisi yok, yalnız yedek modele düşülen noktalarda küçük bir etkisi olur. Tam IERS zinciri (`load_earth_orientation`) dönüş modeli olarak verilebiliyor gibi görünüyor; sınanmadı.

## Hız (ölçülmedi)

`[AJAN OKUDU]` Çalışma zamanı sürüklenme yolunda her kuvvet çağrısı saf Python: dönüş açısı, yinelemeli jeodezik dönüşüm, `datetime`, doğrulamalı veri sınıfları, model çağrısı. Sağ taraf işlevi de Python kapanışı, SciPy `solve_ivp` altında. Koşular arası vektörleştirme yok.

- Bizim tablo modelimiz ucuz (zaman dizisinde arama); NRLMSIS çağrısı yok.
- **Ölçüldü (6 Eki):** nokta kütle çekimi ve sabit yoğunluklu protokol sınıfıyla 4 saatlik koşu 0,3 s (`08`). Küresel harmonik çekimle ölçülmedi.

## Başlangıç durumu

Karşılaştırma aynı başlangıç durumundan iki yayılımın farkı; başlangıç durumunun doğruluğu ikinci mertebe. Seçenekler:

1. **Yoğunluk dosyasındaki konumlardan.** CDF'te 10 saniyede bir jeodezik enlem, boylam, irtifa var. Dünya'ya bağlı konum → eylemsiz konum; hız sonlu farkla ya da kısa bir yay üzerinde en küçük karelerle (`estimation/batch.py`, konum ölçümü). Ek veri gerektirmez. Önerilen.
2. TLE/SGP4. Hazır okuyucu var; tarihsel TLE'leri ayrıca bulmak gerekir.
3. Hassas yörünge (SP3). Okuyucu yok; gereksiz.

Seçenek 1 için eksik parça: cisme bağlı → eylemsiz **durum** dönüşümü (ω×r hız terimiyle). `[AJAN OKUDU]` Yalnız matris var, durum yardımcısı yok.

## Sidera'ya eklenecekler

| # | Parça | Nerede durmalı | Büyüklük | Not |
| --- | --- | --- | --- | --- |
| E1 | `TabulatedTrackAtmosphere`: zamana göre yoğunluk tablosu, boşlukta yedek model, isteğe bağlı irtifa ölçeklemesi | Önce bu projede; olgunlaşınca `sidera.physics.atmosphere` | Küçük | Protokol: `name`, `ellipsoid`, `evaluate`, `provenance`. Boşluk politikası ve dosya özeti kayıtta olmalı |
| E2 | Bileşik model: manyetik enlem bandının içinde A, dışında B | Bu proje | Küçük | E1 + E3 üstüne |
| E3 | Manyetik enlem | Bu proje (apexpy); Sidera'ya girecekse isteğe bağlı bağımlılık olarak | Küçük | Sidera kuralı: isteğe bağlı bağımlılık içe aktarmada güvenli olmalı, test temizce atlanmalı |
| E4 | Toplu sürücü: epok × katsayı ızgarası, koşu başına yeni sürüklenme nesnesi, süreç havuzu, sonuç tablosu + köken kaydı | Bu proje; sonra `sidera.analysis.studies` | Orta | Kalıp: `analysis/studies/atmosphere_fidelity.py` (aynı çıktı ızgarası, örnek başına fark) |
| E5 | Cisme bağlı → eylemsiz durum dönüşümü | `sidera.frames` | Küçük | Bağımsız doğruluk sınaması şart (gidiş-dönüş) |
| E6 | Uzay havası: GFZ okuyucu, F10.7 kuralları, Ap geçmişi, sağlayıcı | **Yazıldı**, bu projede `space_environment`; hedef `sidera.physics.atmosphere` + `sidera.io` | Hazır | Bkz. `11` |
| E7 | Güneş rüzgarı: OMNI okuyucu, bağlaşım fonksiyonları, hafıza öznitelikleri | **Yazıldı**, `space_environment.solar_wind`; Sidera'da yeni bir alt paket gerekir | Hazır | Sidera'da karşılığı yok; mimari kararı senin (bkz. `11`) |

Sidera'ya taşırken geçilecek kapılar (deponun `CLAUDE.md` dosyasından `[DOĞRULADIM]`): sabitlenmiş `ruff==0.12.0`, `mypy`, `lint-imports`, test seçimi, genel yüzey değiştiyse API envanteri, **adlandırılmış her model ya da veri ürünü için doğrulanmış birincil kaynakla algoritma kaydı**, isteğe bağlı bağımlılıkların içe aktarmada güvenli olması, commit'lerde yapay zekâ atıf satırı olmaması. `space_environment` aynı lint ve tip ayarlarıyla yazıldı; algoritma kaydı ve içe aktarma sözleşmeleri taşıma sırasında yapılacak.

## Yörünge bölümü için iş sırası

1. `[YAPILDI]` Uzay havası sağlayıcısı Sidera'nın NRLMSIS sınıfını fırtına kipinde sürüyor.
2. `[YAPILDI, 6 Eki]` Tek koşu ölçümü: 0,3 s; 4 saatte 34,1 m, formül 34,95 m (`08`).
3. E5 ve başlangıç durumu: 29 Eki 2003 CDF'inden bir durum üret; 10 dakika ileri yay, CDF konumlarıyla karşılaştır.
4. E1: aynı gün için ivmeölçer yoğunluğuyla yayılım; `sample.utc` hizasını sına.
5. E3, E2, E4: pilot fırtınalarda üç koşu.

## Bu analizde belirlenemeyenler

- Küresel harmonik çekimle çalışma zamanı sürüklenmesinin koşu süresi (nokta kütleyle 0,3 s ölçüldü).
- `EarthOrientation`'ın dönüş modeli protokolünü çalışma zamanında sağladığı.
- Kestirim katmanının çalışma zamanı sürüklenmesini kabul edip etmediği.
- `propagate` çıktı ızgarasının nasıl kurulduğu (iki koşunun aynı zamanlarda örneklenmesi için önemli).
- Sidera'nın gizli plan dizininde atmosfer yol haritası var (etkin; Harris-Priester ve NRLMSIS aşaması tamam, 4. aşama "fitted C_D per epoch"); fırtına, yoğunluk tahmini ya da güneş rüzgarı için plan yok `[AJAN OKUDU]`.
