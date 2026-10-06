# 04 — Manyetik koordinat, geçiş bölütleme ve hedef değişken

Hazırlanma: 5 Ekim 2026. Ana plan: `../00_ana_plan.md`, "Enlem bantları ve koordinat", "Zamanlama geometrisi", "Geçiş bölütleme adımları".

**Etiketler.** `[ÖLÇÜLDÜ]` bu makinede komutla okundu. `[OKUNDU]` kaynak açıldı. `[HESAP]` bu belgede türetildi. `[DOĞRULANMADI]` sınanmadı.

## Ana plana göre değişenler

1. **apexpy ve aacgmv2'nin Windows tekerleği yok.** PyPI dosya listesi `[ÖLÇÜLDÜ]`: apexpy 2.1.1 ve aacgmv2 2.7.1 için yalnız birer macOS tekerleği ve kaynak paketi var. İkisi de bu makinede derleme gerektirir. apexpy için derleme aynı gün denendi ve çalıştı (aşağıda); risk kapandı.
2. **Zamanlama geometrisi sabit değil.** CHAMP periyodu görev boyunca yaklaşık 93,3 dakikadan 89,6 dakikaya iniyor `[HESAP]`. Ana plandaki +23, +70, +117… dakikalar yalnız 2001 için. Öngörü süreleri geçiş zamanlarından hesaplanmalı, sabit sayı girilmemeli.
3. **Oliveira'nın manyetik koordinat sistemi makalede yazmıyor** (bildiri ve 2019 makaleleri "MLAT/MLT" diyor). Quasi-dipole seçimi bizim; teze yaz.

## Manyetik koordinat

**Seçim: quasi-dipole (QD) enlem ve manyetik yerel zaman, apexpy ile.**

apexpy arayüzü ([kaynak](https://raw.githubusercontent.com/aburrell/apexpy/main/apexpy/apex.py)) `[OKUNDU]`:

- `Apex(date=None, refh=0, datafile=None, fortranlib=None)`; `set_epoch(year)`.
- `geo2qd(glat, glon, height)`; `mlon2mlt(mlon, dtime, ssheight=318550)`; `convert(lat, lon, source, dest, height=0, datetime=None)`.
- Dizi girdisi alıyor. "IGRF-14 with coefficients from 1900 to 2030."
- Bir `Apex` nesnesi tek epok; alan yavaş değiştiği için aylık epok yeter.

**Kurulum yolları** (sırayla dene):

| # | Yol | Durum |
| --- | --- | --- |
| 1 | Windows'ta kaynak derleme. gfortran bu makinede var: `C:\Strawberry\c\bin\gfortran.exe` `[ÖLÇÜLDÜ]`. apexpy belgesi MinGW'yi Microsoft C++ derleme araçlarından sonra kurmayı ve `pip install apexpy --no-build-isolation --no-cache` komutunu öneriyor `[OKUNDU]` | Sınanmadı. Strawberry Perl'in gfortran'ı ile Python'un derleyici uyumu belirsiz |
| 2 | Docker'da Linux kabı. Docker Desktop kurulu görünüyor (WSL dağıtım listesinde `docker-desktop`) `[ÖLÇÜLDÜ]`. `python:3.12` + `gfortran` + `pip install apexpy`; proje dizinini bağla; koordinatları bir kez hesapla, parquet'e yaz | Sınanmadı. En güvenilir yol; koordinat hesabı tek seferlik bir toplu iş |
| 3 | conda-forge | Paket bulunamadı (404) `[OKUNDU]`; `conda search -c conda-forge apexpy` ile bir kez bak |
| 4 | Kendi QD yaklaşımı (IGRF dipol + düzeltme) | Yapma. Doğrulama yükü getirir |

**Güncelleme (aynı gün, sonradan): yol 1 çalıştı** `[ÖLÇÜLDÜ]`. Kayıt: `kanit/apexpy_kurulum_2026-10-05.txt`. Doğrudan `pip install` ve `--no-build-isolation` tek başına başarısız oldu (`Include dir ...\include does not exist`); uv'nin kurduğu sanal ortamda `include` dizini yok. Çalışan tarif:

1. `PATH`'in başına `C:\Strawberry\c\bin`.
2. `uv venv <ortam> --python 3.12`.
3. `uv pip install numpy meson-python meson ninja`.
4. Taban Python'un `include` dizinini `<ortam>\include` olarak kopyala.
5. `uv pip install apexpy --no-build-isolation` (derleme 30 saniye).

Deneme ortamı `D:\tmp\pp_apex_test` içinde duruyor; proje ortamı kurulunca silinebilir. Docker'a gerek kalmadı.

**Doğrulama.** Çalışma sınaması yapıldı (`Apex(2003.8)`, 400 km): (60° K, 15° D) → QD enlem 56,59°; (0°, 0°) → −11,61°; (80° K, 72° B) → 87,33°. Değerler makul, ama bağımsız bir hesaplayıcıyla karşılaştırılmadı; bunu bir kez yap.

**Hesap yükü.** Ölçülen hız yaklaşık **534.000 nokta/s** (100.000 rastgele nokta, tek çağrı). 71 milyon nokta yaklaşık 2-3 dakika; seyreltmeye gerek yok. Her ay için ayrı epok kur.

## Bantlar

| Değişken | Tanım | Dayanak |
| --- | --- | --- |
| Hedef | \|QD enlem\| < 30°, geçiş ortalaması | Weimer 2023: 30° altı 180-300 dk; Liu 2010: ±30° yaklaşık 3 sa |
| Kutup girdisi | \|QD enlem\| > 63°, kuzey ve güney ayrı | Oliveira: "approximately between ±63° an ±90°" |
| Tazelik kontrolü | 40° < \|QD enlem\| < 55° | Ana plan (tasarım) |
| Cusp bayrağı | Kutup geçişinde 10-14 MLT'den geçen kayıt oranı | Ana plan |

Notlar:

- **Hedef bandın tek ortalaması, kuzey ve güney alçak enlemi karıştırır.** Liu 2010 ve Weimer gecikmeyi yerel zamana bağlıyor, yarımküreye değil; tek ortalama savunulabilir. Yine de pilotta ±30°'yi (0-30° K) ve (0-30° G) diye ikiye bölüp bak: gezen bozulma kuzeyden 730, güneyden 460 m/s ile geliyorsa (Bruinsma ve Forbes 2007, tek olay) iki yarı farklı zamanda tepki verir.
- **Kutup bandı geniş.** Bir geçişte uydu 63°'nin üstünde yaklaşık 14 dakika kalır `[HESAP: 2×27°/360°×93 dk]`; ısıtma auroral ovalde (65-75°) yoğun. Ek öznitelik: banttaki en yüksek değer ve ortalama birlikte. İkisini de pilotta dene, birini seç.
- **Yörünge eğimi.** CHAMP 87,3°: her yörüngede QD kutbuna ulaşmaz; en yüksek QD enlem boylama göre değişir. Geçiş başına "ulaşılan en yüksek |QD enlem|" sütunu tut.
- Geçiş ortalaması `y`'nin (log-oran) ortalamasıdır, yoğunluğun değil.

## Geçiş bölütleme

1. Bayrağı 0 olmayan kayıtları at (`validity_flag`: 0 nominal, 1 anormal; bkz. `01`).
2. QD enlem, QD boylam, MLT ekle.
3. Yörüngeyi coğrafi enlemin yerel en büyük ve en küçük noktalarından yarım yörüngelere böl (yükselen, alçalan). Her yarım yörünge tek bir yerel zaman sektöründe.
4. Her yarım yörüngede bant parçalarını bul: kutup K, orta K, alçak, orta G, kutup G. Kutup parçası iki yarım yörüngeye yayılır; kutup geçişini "63°'yi aşıp tekrar 63°'nin altına inene kadar" tek parça say.
5. Parça başına: başlangıç, bitiş, orta zaman; ortalama ve en yüksek `y`; geçerli kayıt oranı; ortalama irtifa; ortalama MLT ve yerel güneş zamanı; ulaşılan en yüksek |QD enlem|; cusp oranı.
6. Geçerli kayıt oranı eşiğin altındaysa parçayı eksik say. Eşik başlangıcı %70 (ana plan); pilotta sabitle.
7. Çıktı: `passes.parquet` (uydu, parça kimliği, yörünge numarası, bant, yarımküre, sektör, zamanlar, istatistikler).

**Durum (6 Eki 2026, yazıldı ve ölçüldü; `analysis/passes.py`, `physics/magnetic_coordinates.py`, `kanit/gecis_bolutleme_kaniti_cikti_2026-10-06.txt`):** adım 1-7 kodlandı. 29 Eki 2003 CHAMP gününde (10 s, 8640 kayıt) coğrafi enlemle **31 alçak, 16+16 kutup, 31+31 orta** parça; alçak enlem orta zamanları 46-46,5 dk arayla; parçalar çakışmıyor; hepsi tam. apexpy proje ortamına kuruldu (`magnetic` extra), QD enlem ve MLT eklendi; QD bantlarıyla sayımlar ve cusp oranı kanıt dosyasında. Örnek kurucu (`build_samples`) kutup geçişi bitişi = t0, 60-270 dk ilerideki alçak parçalar hedef, girdiler son 4 alçak / 4 kutup (K ve G ayrı) / 1 orta; sızıntı denetimi kod içinde. Aşağıdaki üç birim testi `tests/test_passes.py` içinde geçiyor. QD bantlarıyla aynı gün: alçak enlem aralıkları 42,6-50 dk (QD ekvatoru eğik), kutup geçişinde cusp oranı ortanca 0,31; 3 saatlik log-yoğunluk ortalamaları kutup kuzeyde 06 UT diliminde +0,69 (iki kat) sıçrarken alçak enlemde sıçrama 09 UT diliminde (+0,46): bu günde kutup yaklaşık 3 saat önde. Tek gün, önizleme.

**Birim testleri.**

- Bir günde yaklaşık 15,4 yörünge → 31 alçak enlem parçası, 15-16 kuzey ve 15-16 güney kutup parçası.
- Ardışık alçak enlem parçalarının orta zamanları arasında yaklaşık yarım periyot (45-47 dk).
- Parçaların zaman aralıkları çakışmaz.

## Zamanlama geometrisi `[HESAP]`

Dairesel yörünge periyodu, `T = 2π·sqrt(a³/μ)`, Dünya yarıçapı 6371 km:

| Uydu, dönem | İrtifa (km) | Periyot (dk) |
| --- | --- | --- |
| CHAMP, 2001 | 443 | 93,3 |
| CHAMP, 2008 | 340 | 91,2 |
| CHAMP, Eyl 2010 | 260 | 89,6 |
| GRACE, 2006-2009 | 480 | 94,1 |
| GRACE, 2015 | 392 | 92,3 |

İrtifalar `01_yogunluk_verisi.md` içindeki örneklemelerden.

- Kutup geçişinin bitişinden (63°'nin altına iniş) sonraki ilk alçak enlem parçasının ortasına yaklaşık 16 dakika; sonrakiler yaklaşık yarım periyot arayla, sırayla iki karşıt yerel zaman sektöründe.
- Aynı sektöre dönüş bir tam periyot.

**Örnek kurma kuralı.**

- Tahmin anı `t0`: bir kutup geçişinin bitişi (kuzey ya da güney).
- Hedefler: `t0`'dan sonra orta zamanı `[t0 + 60 dk, t0 + 270 dk]` içinde olan alçak enlem parçaları. Öngörü süresi `Δ = t_hedef − t0`, sürekli değişken.
- Öngörü süresi kutuları (raporlama için): 60-105, 105-150, 150-195, 195-270 dk. Ana plandaki dört havuz bunlar; ilk ekvator geçişi (yaklaşık +16 dk) ve +60 dakikadan kısa hedefler birincil testin dışında (tazelik etkisi baskın), ikincil olarak raporlanır.
- B2/B3 girdisi: `t0`'dan önce tamamlanmış son 4 alçak enlem parçası (iki sektörden ikişer).
- M girdisi: `t0`'da biten kutup geçişi dahil son 4 kutup geçişi (kuzey ve güney ayrı sütunlar).
- B3t girdisi: `t0`'dan önceki son orta enlem parçası. **Tazelik eşleştirmesi:** orta enlem parçası kutup geçişinden hemen önce biter (birkaç dakika daha eski). Kutup geçişinden sonraki orta enlem parçası ise `t0`'dan sonradır ve kullanılamaz. Yani B3t, M'den birkaç dakika daha "bayat"; fark küçük ama ters yönde değil. Alternatif: `t0`'ı orta enlem parçasının bitişine kaydıran ikinci bir B3t (M'den daha taze); ikisinin arasında kalmak M'nin kazancını sıkıştırır. Pilotta ikisini de hesapla.
- Her örnek bir (kutup geçişi, hedef parça) çifti; aynı hedef birden çok `t0` için görünebilir. Fırtına içi bağımlılık zaten fırtına düzeyinde kümeleme ile ele alınıyor.

**Sızıntı testi.** Her örnek için tüm girdi parçalarının bitiş zamanı ≤ `t0` ve hedef parçanın başlangıcı > `t0`; ihlal sayısı sıfır olmalı. Kod içinde doğrulama olarak kalsın.

## Hedef değişken

`y = ln(ρ_gözlem / ρ_ref) − b_s` (bkz. `03_atmosfer_modeli.md`).

- `b_s`: fırtına ve uydu başına, sıfır epoktan önceki 24 saatte tüm bantların `ln(ρ_gözlem/ρ_ref)` ortalaması. Öneri: bant başına ayrı `b_s` (alçak, orta, kutup). Model yanlılığı enleme bağlıysa tek bir sabit kutup girdisine sahte bir sabit ekler; ridge kesme terimi bunu emer ama fırtınadan fırtınaya değişen kısmını emmez.
- Fırtına öncesi 24 saatte başka bir fırtınanın toparlanma evresi varsa `b_s` kirlenir. Örtüşen fırtınalar tek kümede; küme için `b_s` ilk fırtınanın öncesinden alınır.
- Öncesi 24 saatte geçerli veri %50'den azsa pencereyi 48 saate uzat; yine yoksa fırtınayı at ve say.

## Açık noktalar

- [x] apexpy kurulumu ve hızı (5 Eki 2026, yukarıda).
- [ ] QD değerlerinin bağımsız bir hesaplayıcıyla karşılaştırılması.
- [ ] Kutup girdisi: ortalama mı, en yüksek mi (pilot).
- [ ] Hedef bandı yarımküreye bölmek gerekli mi (pilot).
- [ ] B3t'nin iki tanımı (pilot).
