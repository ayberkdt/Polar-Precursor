# 08 — Yörünge etkisi ve Sidera

Hazırlanma: 5 Ekim 2026. Ana plan: `../00_ana_plan.md`, "Çapraz uydu testi ve yörünge etkisi".

**Etiketler.** `[OKUNDU]` tam metin açıldı. `[ÖZET]` yalnız özet. `[YEREL]` bu makinedeki depodan okundu. `[DOĞRULANMADI]` açılamadı ya da hafızadan.

## Ana plana göre değişenler

1. **Formül artık kaynaklı.** Ana plan "bunu açıkça yazan bir kaynak bulunamadı" diyordu. Emmert ve ark. 2014 (AMOS) Denk. 3-5 açık erişimli ve tam okundu; `δs ≈ (3/2)·a·ε·t²` ondan iki satırda çıkıyor (aşağıda).
2. **Sidera'da NRLMSIS var, JB2008 yok; keyfi yoğunluk için arayüz var ama hazır sınıf yok.** Açık sorulardan ikisi yerel depodan yanıtlandı.
3. **Gerekçe için daha iyi bir dayanak:** USSPACECOM taraması 8 saatte bir; kaçırılan bir dosya için 16 saate kadar gecikme (NASA el kitabı). 1-4 saatlik tahmin ufku bu çevrimle aynı mertebede.
4. **Starlink düşük sürüklenme / açık kitap alanları doğrulanamadı.** Ana plandaki üst sınır satırı (0,131 m²/kg) en büyük alan varsayımıdır.

## Kuram

Emmert, Byers, Warren, Segerman 2014, [AMOS bildirisi](https://amostech.com/TechnicalPapers/2014/Space_Weather/EMMERT.pdf) `[OKUNDU, s. 1-8]`:

- Denk. 3: `dn/dt ≅ (3/2) · n^(1/3) · μ^(−2/3) · ρ · B · v³`, `B = C_D·A/m`.
- Denk. 4: `dM/dt = n`.
- Denk. 5: iz boyunca hata, bağıl yoğunluk hatasının **çift integrali** ile orantılı.
- Denk. 6: rastgele yürüyüş türü yoğunluk hatasında varyans `t⁵` ile büyür; zamanda düzgün hatada (ör. balistik katsayı) `t³`.

Dergi sürümü: Emmert ve ark. 2017, Adv. Space Res. 59, 147-165, doi 10.1016/j.asr.2016.07.036 `[ÖZET]`. Özetten: "The mean motion and mean anomaly errors are proportional to the first and second integrals, respectively, of the density error"; beyaz gürültüde varyans `t³`, Brown hareketinde `t⁵`; geçerlilik koşulu perigee irtifa değişimi yaklaşık 0,2 ölçek yüksekliğinden az. Denk. 17-18 okunmadı. Kabul edilmiş makale sürümü açık (ScienceDirect "am" bağlantısı), normal tarayıcıda açılır.

**Türetme (bizim, Denk. 3'ten).** Dairesel yörüngede `n = v/a`, `μ = v²·a`. Yerine koyunca `dn/dt = (3/2)·ρ·B·v²/a = 3·a_s/a`, burada `a_s = ½·ρ·B·v²`. Sabit bağıl hata `ε` için `Δn = 3·a_s·ε·t/a`, `ΔM = (3/2)·a_s·ε·t²/a`, ve

```
δs = a·ΔM = (3/2) · a_s · ε · t²
```

Ana plandaki ifadeyle aynı. Sayı kontrolü: ρ = 4×10⁻¹², v = 7669 m/s, B = 0,00477 → a_s = 5,61×10⁻⁷ m/s²; ε = 0,2, t = 4 sa → **34,9 m**. Ana plandaki "yaklaşık 35 m" tutuyor.

**Teze nasıl yazılır.** Kalıcı yanlılıkta hata `t²`; tahmin hatası zamanla ilişkiliyse varyans `t³`-`t⁵` arası. Bizim durumumuz (1-4 saat, alçak enlem bandında kısmi düzeltme) kalıcı yanlılık sınırına yakın; `t²` üst kestirim olarak yeter.

## Sidera'nın bugünkü durumu `[YEREL]`

Depo: `D:\sidera`, commit `6dcb8f63` (5 Eki 2026, "Feat/attitude module (#17)"); çalışma ağacında 14 işlenmemiş değişiklik var.

- `src/sidera/physics/atmosphere/models.py`:
  - `AtmosphereModel` bir `Protocol`: `name`, `ellipsoid`, `evaluate(sample) -> AtmosphereState`, `provenance()`.
  - `AtmosphereSample`: jeodezik konum, `epoch_tdb_s`, isteğe bağlı `utc`.
  - `AtmosphereState`: zorunlu tek alan `density_kg_m3`.
  - Hazır sınıflar: `ExponentialAtmosphere`, `HarrisPriesterAtmosphere`, `NrlmsiseAtmosphere` (pymsis; sürüm "00", "2.0", "2.1"; `storm_mode`).
- `src/sidera/core/drag/aerodynamics.py:198`: sürüklenme modeli `atmosphere: AtmosphereModel` alıyor; yani protokolü sağlayan her sınıf takılabilir.
- `src/sidera/physics/atmosphere/space_weather.py`: `TimeSeriesSpaceWeatherProvider.from_csv`; indeksler dışarıdan veriliyor.
- JB2008 yok (kaynakta "jb2008/jacchia" arandı, yalnız atıf düzeyinde eşleşme).
- `cli/atmosphere_options.py` içinde tablo/kullanıcı tanımlı yoğunluk seçeneği yok; komut satırından değil, Python'dan kurulacak.
- Sanal ortam: Python 3.10.20, pymsis 0.13.0.

**Okunmayan:** tümleyicinin protokol sınıfını uçtan uca çalıştırdığı sınanmadı. Aşağıdaki adım 1 bunu kanıtlar.

Ana plandaki açık soruların yanıtı:

- "Sidera'da MSIS veya JB2008 var mı?" → MSIS var, JB2008 yok.
- "Keyfi yoğunluk fonksiyonuyla sürüklenme yayılımı doğrulanmış mı?" → Arayüz elveriyor; doğrulanmış bir örnek yok. Yazılacak.

**Güncelleme (sonradan):** Sidera'nın tez açısından tam envanteri `10_sidera_hazirlik_analizi.md` içinde. Buradaki iki soruya ek olarak üç tuzak çıktı; en önemlisi zaman ölçeği sabiti: `AtmosphericDrag` varsayılan olarak TDB−UTC = 69,184 s alıyor, bu 2017 öncesi için yanlış (2003'te 5 s fazla, yaklaşık 38 km iz boyunca). Zamana göre yoğunluk tablosu kullanacağımız için her koşuda açıkça verilmeli.

## Tek koşu sınaması yapıldı (6 Eki 2026) `[ÇALIŞTIRDIM]`

Betik ve çıktı: `kanit/sidera_tek_kosu.py`, `kanit/sidera_tek_kosu_cikti_2026-10-06.txt`. Sidera ortamında (`D:\sidera\.venv`), commit `6dcb8f63`.

Kurgu: 400 km, e = 0,0005, i = 87,3°, 4 saat, 60 s çıktı; nokta kütle çekimi (Sidera varsayılanı); CHAMP katsayıları (522 kg, C_D·A/m = 0,00477 m²/kg); sabit yoğunluk 4×10⁻¹² kg/m³ ve %20 fazlası, 20 satırlık bir protokol sınıfıyla.

| t (sa) | Ölçülen iz boyunca fark (m) | (3/2)·a·ε·t² (m) | Oran |
| --- | --- | --- | --- |
| 1 | 1,62 | 2,18 | 0,74 |
| 2 | 8,23 | 8,74 | 0,94 |
| 3 | 19,53 | 19,66 | 0,99 |
| 4 | 34,09 | 34,95 | 0,98 |

- **Soru 1 kapandı:** kullanıcı tanımlı atmosfer sınıfı Sidera'nın sürüklenme modeli üzerinden yayılımı sürüyor; `propagate_body_orbit(cfg, drag=AtmosphericDrag(atmosphere=...))` yolu çalışıyor.
- **Soru 2 kapandı:** 4 saatlik koşu **0,3 s** (ilk koşu ısınmayla 0,7-2,8 s); binlerce koşu rahat. Küresel harmonik çekimle süre ölçülmedi; fark modelden modele olduğu için nokta kütle yeterli olabilir.
- **Soru 3 kapandı:** 3-4 saatte formülle %1-3 içinde; 1 saatte %26 sapma periyodik terimlerden (küçük dışmerkezlik, radyal salınım 0,9-3 m). Ana plandaki "yaklaşık 35 m" sayısı yayılımla doğrulandı.
- **İşaret:** daha yoğun atmosferdeki uydu referansın **ilerisinde** çıkıyor (yörünge alçalır, ortalama hareket artar). Ana plandaki anlatım bu yönü belirtmiyordu; tezde "iz boyunca hata" işaretini bu şekilde tanımla.
- Zaman ölçeği sabiti bu koşuda önemsiz (yoğunluk zamana bağlı değil); tablo modelinde zorunlu (bkz. `10`).

## Yazılacak sınıf

`TabulatedTrackAtmosphere` (öneri; Sidera deposuna değil, bu projeye, Sidera'yı bağımlılık alarak):

- Girdi: zaman damgalı yoğunluk serisi (ivmeölçer yoğunluğu ya da model tahmini) ve bir yedek `AtmosphereModel`.
- `evaluate`: `sample.utc` için seriden doğrusal ara değer; boşlukta yedek modele düş, `metadata`'ya işaretle.
- İrtifa düzeltmesi: yayılan yörünge gerçek yörüngeden uzaklaştıkça `ρ(h) = ρ_seri · ρ_ref(h)/ρ_ref(h_seri)`. 4 saatte fark metreler mertebesinde olduğu için ihmal edilebilir; yine de uygula, etkisini bir kez ölç.
- `provenance`: seri dosyasının özeti, yedek model, ara değer yöntemi.

Üç yayılım, aynı başlangıç durumu ve sabit `C_D·A/m`:

| Koşu | Alçak enlem bandı (|MLAT| < 30°) | Bandın dışı |
| --- | --- | --- |
| Doğruluk | ivmeölçer yoğunluğu | ivmeölçer yoğunluğu |
| B3 | B3 tahmini | ivmeölçer yoğunluğu |
| M | M tahmini | ivmeölçer yoğunluğu |

Ana plan bandın dışında "referans yoğunluk" diyor. Öneri: dışarıda da ivmeölçer yoğunluğu; böylece fark yalnız alçak enlem tahmininden gelir ve iki modelin farkı temiz okunur. Operasyonel gerçekçilik için ikinci bir set (dışarıda referans model) duyarlılık olarak eklenebilir.

## İş adımları

1. ~~Ocak öncesi, yarım gün. Sabit yoğunluklu protokol sınıfı; 4 saat; formülle karşılaştırma.~~ **6 Eki 2026'da yapıldı** (yukarıda): 4 saatte 34,1 m, formül 34,95 m.
2. **Hafta 12.** `TabulatedTrackAtmosphere`; pilot fırtınalardan 5 olayda üç koşu.
3. Tüm test fırtınalarında, fırtına başına birkaç başlangıç anı (epok +0, +6, +12, +24 sa); 1, 2, 3, 4 saatte iz boyunca fark.
4. Üç balistik katsayı için tekrarla (aşağıda).
5. Rapor: fırtına başına `|δs_B3| − |δs_M|` ortancası ve dağılımı; şiddet sınıfına göre.

## Balistik katsayılar

| Nesne | Kütle | C_D·A/m (m²/kg) | Durum |
| --- | --- | --- | --- |
| CHAMP | 522 kg (30 kg yakıt dahil) | 0,00477 | Kütle [eoPortal](https://www.eoportal.org/satellite-missions/champ) `[OKUNDU]`; katsayı ana planda Gondelach ve Linares'ten, bu oturumda yeniden açılmadı |
| GRACE | 432 kg | hesaplanacak | Kütle [eoPortal](https://www.eoportal.org/satellite-missions/grace) `[OKUNDU]`; ön alan bulunamadı |
| 3U küp uydu | — | 0,0165 | Ana plandaki varsayım; kaynak yok `[DOĞRULANMADI]` |
| Starlink, en büyük alan | 260 kg, 15,45 m², C_D 2,2 | yaklaşık 0,13 | [Earth Planets Space 2024](https://link.springer.com/article/10.1186/s40623-024-02124-2) `[OKUNDU, anahtar pasajlar]` |

CHAMP ve GRACE için TU Delft ürünlerinin kendi panel modeli ve kütle geçmişi var; katsayıyı oradan türetmek daha tutarlı (bkz. `01_yogunluk_verisi.md`).

## Beklenen büyüklük

Ana plandaki hesap geçerli: alçak enlem hatası %20'den %18'e inerse yörünge ortalamasında yaklaşık %0,7; CHAMP için 4 saatte yaklaşık 1 m, en büyük alanlı nesne için yaklaşık 30 m. Bölüm "etki küçük, ama ölçüldü" diye yazılacak.

Kıyas için okunan sayılar:

- Emmert 2014 Şekil 2: 400 km dairesel, B = 0,1 m²/kg, 7 günde iz boyunca 1σ yaklaşık 180-200 km (şekilden okuma); güneş akısı tahmin hatası 7 günde %7, 1 saatte %0,52.
- ABD Savunma Bakanlığı yoğunluk doğruluk gereksinimi (aynı bildiride): 500 km altında ±%5.
- STORM-AI 2026: Mayıs 2024 fırtınasında JB2008'e göre kazanç %6,1 (bkz. `09_literatur.md`).
- Zhang ve ark. 2026 (özetten): yoğunluk tahminiyle 24 saatlik en büyük konum hatasında CHAMP için %24,6, TM02 için %16,3 azalma. Bizim bölümün doğrudan kıyas noktası; yöntemini (doğruluk referansı, C_D) tam metinden oku.
- Hejduk'un 2017 NASA sunumu ([NTRS 20170004369](https://ntrs.nasa.gov/api/citations/20170004369/downloads/20170004369.pdf)) `[OKUNDU, sonradan]`: geçmiş yakınlaşmalar yoğunluğa hata eklenerek yeniden işlenmiş; "density model accuracy matters significantly – But knowledge of model error can blunt effect substantially". Sayılar şekillerde; dergi makalesi (2018) açılamadı.

## Operasyonel gerekçe

[NASA Çarpışma Değerlendirme El Kitabı](https://www.nasa.gov/wp-content/uploads/2024/01/oce-51-nasa-spacecraft-conjunction-assessment.pdf) (NASA/SP-20230002470 Rev 1) `[OKUNDU, hedefli pasajlar]`:

- "Current USSPACECOM practice is to conduct three screenings per day."
- "the USSPACECOM screening process is performed only once every 8 hours ... it may take up to16 hours to screen the predicted trajectory."
- 500 km altı perigee için günde üç efemeris, 7 günlük.
- Ek N: kovaryanslarda yoğunluk tahmin hatası için "consider" parametresi; değerler HASDM'den, kamuya açık şekilde gizlenmiş.

ESA ([Automating collision avoidance](https://www.esa.int/Space_Safety/Space_Debris/Automating_collision_avoidance)) `[OKUNDU]`: uydu başına haftada yaklaşık iki uyarı ayrıntılı inceleme istiyor; eşik tipik olarak 1/10.000.

Starlink manevra sayıları yalnız ikincil kaynaklardan (FCC dosyası açılmadı): Haz-Kas 2025'te 148.696; Ara 2025-May 2026'da 207.152. Teze almadan önce SpaceX'in FCC yarı yıllık raporundan doğrula.

Kurgu: tarama çevrimi 8 saat; bir fırtına başladığında bir sonraki efemeris tesliminde kullanılacak yoğunluk, 1-4 saatlik bir tahmindir. Tez bu tahminin bilgi içeriğini ölçer, çalışan sistemi değil.

## Açık noktalar

- [ ] Emmert 2017 tam metin (Denk. 17-18); kabul edilmiş sürüm tarayıcıdan.
- [ ] Hejduk ve Snow 2018 (doi 10.1029/2017SW001720; Space Weather dergisi, AMOS değil) ve Anderson 2009: açılamadı.
- [x] Adım 1 koşusu (6 Eki 2026, `kanit/sidera_tek_kosu_cikti_2026-10-06.txt`).
- [ ] GRACE ön alanı ve C_D kaynağı.
- [ ] Fang 2022, Dang 2022, Berger 2023 (Şubat 2022 Starlink kaybı): açılamadı.
