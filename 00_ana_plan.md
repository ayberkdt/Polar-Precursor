# Kutuptan Erken Uyarı: Tez Araştırma Planı

Oct 5, 2026 · @ApollonDt

## Özet

Plan ayakta, ama inceleme altı kararı değiştirdi ve bir riski büyüttü. Bu testi yapan bir yayın bulunamadı; taramayı yapan ajanın kendi güven tahmini %70-75.

Bu doküman altı ayrı literatür ve veri taramasına dayanıyor. Her iddia, sayfası gerçekten açılmış bir kaynağa bağlı. Açılamayan makaleler ve benim kendi akıl yürütmem ayrı işaretli. Sayılar otomatik sayfa okuyucudan geçti; teze almadan önce PDF'lerden kontrol et.

**Değişen kararlar**

| Konu | İlk plan | Yeni karar | Neden |
| --- | --- | --- | --- |
| Normalizasyon | log(ölçüm / model) | Fırtına terimi kapatılmış model + fırtına öncesi yanlılık düzeltmesi | Modelin kendi fırtına tepkisi oranı kirletir |
| Fırtına sayısı | 168 (2001-2011) | 217'ye kadar (2001-2015) | Zesta ve Oliveira 2019 aynı yöntemi 2015'e uzatmış |
| B3 taban modeli | Bağlaşım fonksiyonu + indeksler | İki katmanlı sürücü seti, 57 saate kadar hafıza | Yayınlanmış ML modelleri bu hafızayı kullanıyor |
| Kontrol | Yok | Tazelik kontrolü ve kahin sürücü tabanı | Kutup ölçümü ekvator ölçümünden 23 dakika daha taze |
| İstatistik | Bootstrap güven aralığı | Fırtına başına eşli kayıp farkı + permütasyon testi | İç içe modeller ve fırtına içi otokorelasyon |
| Yörünge bölümü | Kazancı konum hatasına çevir | Aynı, ama beklenti düşürüldü | Kaba hesap metre mertebesi veriyor |

**En kritik üç bulgu**

1. **Pencere, en önemli fırtınalarda daralıyor.** Aşırı fırtınalarda ekvator yaklaşık 1,5 saatte tepki veriyor ([Zesta ve Oliveira 2019](https://ntrs.nasa.gov/api/citations/20200000388/downloads/20200000388.pdf)). Erken uyarının en değerli olduğu olaylarda öngörü süresi en kısa.
2. **Güçlü bir ikincil sonuç var.** Okunan uydu izi ML modellerinin hiçbiri uydunun kendi yakın geçmiş yoğunluğunu girdi olarak kullanmıyor. B2 ve B3'ün bu modellere karşı 1-4 saatlik başarımı, ana hipotez sıfır çıksa bile raporlanabilir.
3. **Sürücü tabanı gerçekten güçlü.** L1 ölçümü 15-60 dakika önde, alçak enlem gecikmesi 3-6 saat. Sürücüler 1-4 saatlik ufku meşru biçimde besliyor; kutup yoğunluğu bunun üstüne çıkmak zorunda.

## Araştırma sorusu ve hipotezler

Soru: bir uydunun yüksek enlemde ölçtüğü yoğunluk anomalisi, 1-4 saat sonraki alçak enlem yoğunluğunu, sürücüler ve alçak enlemin kendi geçmişi bilinirken ek olarak ne kadar iyi tahmin ettirir?

**Hipotezler**

- **H1 (ana):** M modeli, B3'e göre fırtına dışı örneklemde daha düşük hata verir.
- **H2:** Kazanç öngörü süresine bağlıdır ve Weimer gecikme haritalarının öngördüğü pencerede (kabaca 2-4 saat) en yüksektir.
- **H3:** Kazanç fırtına şiddetiyle azalır, çünkü güçlü fırtınalarda yayılma hızlanır.
- **H4 (ikincil):** Uydunun kendi yakın geçmişini kullanan B3, yalnız sürücü kullanan bir modele göre 1-4 saatte belirgin daha iyidir.

H3 ve H4 benim eklemem. H3, Zesta ve Oliveira 2019 ile Liu 2010'un bulgularından çıkıyor. H4, ana hipotez sıfır çıksa da tezi taşıyan sonuç.

**Önceden sabitlenecek ölçütler**

Veriye bakmadan önce yazılı hale getir ve danışmana gönder. Eşik değerini pilot çalışmadan sonra, ana analizden önce sabitle.

- **Birincil ölçüt:** log-oran artığının göreli RMSE azalması, M ile B3 arasında, dört öngörü süresi havuzlanmış.
- **Olumlu sonuç:** fırtına düzeyinde %95 güven aralığı sıfırı dışlar ve permütasyon testi p < 0,05 verir.
- **Sıfır sonuç:** güven aralığı sıfırı içerir ve üst sınırı, pilottan belirlenen en küçük anlamlı etkinin altındadır. Bu durumda sonuç “kutup yoğunluğu sürücülerin ötesinde bilgi taşımıyor” olur ve üst sınırıyla raporlanır.
- **Belirsiz sonuç:** güven aralığı sıfırı içerir ama geniştir. Bunu açıkça “güç yetersiz” diye yaz, sıfır sonuç gibi sunma.

**Tezin iddia etmediği şey**

Bu yoğunluk ürünleri sonradan işlenmiş veridir. Tez bilgi içeriğini ölçer; çalışan bir uyarı sistemi göstermez.

## Literatür konumu

Gecikmeler iyi belgelenmiş, ama hep ısıtmadan yoğunluğa gecikme ya da üst üste bindirilmiş epok tasviri olarak. Ölçülmüş kutup yoğunluğunu alçak enlem için tahmin girdisi yapıp taban modellere karşı puanlayan bir çalışma bulunamadı.

**Fizik: gecikme ölçümleri**

| Çalışma | Veri | Bulgu | Okunma |
| --- | --- | --- | --- |
| [Oliveira ve ark. 2017](https://arxiv.org/pdf/1710.07743) | 168 CME fırtınası, 2001-2011, CHAMP ve GRACE | Yüksek enlem 1,5 saat içinde, ekvator 3 saat içinde | Tam metin |
| [Zesta ve Oliveira 2019](https://ntrs.nasa.gov/api/citations/20200000388/downloads/20200000388.pdf) | 217 CME fırtınası, 2001-2015 | Isınma süresi 5-6 saat, aşırı fırtınada 9,5 saat; aşırı fırtınada ekvator yaklaşık 1,5 saatte | Tam metin |
| [Weimer ve ark. 2023](https://spacewx.com/wp-content/uploads/2023/06/Space-Weather-2023-Weimer-Global-Variations-in-the-Time-Delays-Between-Polar-Ionospheric-Heating-and-the-Neutral.pdf) | CHAMP ve GRACE, modellenmiş Poynting akısı | 60° üstünde 60 dakikadan az, 30° altında 180-300 dakika | Tam metin |
| [Liu ve ark. 2010](https://angeo.copernicus.org/articles/28/1633/2010/) | 30 fırtına, CHAMP 2002-2005 | Birleşme elektrik alanına gecikme 0-4,5 saat; doğrusal tahmin modeli | Özet |
| [Sutton ve ark. 2009](https://api.crossref.org/works/10.1029/2008JA013667) | CHAMP, 400 km | Alçak enlemde 3-4 saat, yüksek enlemde 2 saatten az | Yalnız özet |
| [Bruinsma ve Forbes 2007](https://api.crossref.org/works/10.1029/2007GL030243) | CHAMP | Ekvatora doğru hız kuzeyden 730 m/s, güneyden 460 m/s | Yalnız özet |

Weimer'ın gecikmeleri, yay şoku ile iyonosfer arasındaki 20-35 dakikayı içeriyor. Makalenin DOI'si 10.1029/2022SW003410.

**En yakın öncüller**

- **Weimer 2023:** gecikme yapısını haritalamış, ama modellenmiş ısıtma vekilinden yoğunluğa. Önerdiği kullanım, haritaları EXTEMPLAR gibi ampirik modellere koymak.
- **[Sutton 2018](https://api.crossref.org/works/10.1002/2017SW001785):** CHAMP verisini asimile edip GRACE üzerinde doğrulamış. Yoğunluk ölçümünün başka yere bilgi taşıdığını gösteriyor, ama fizik modeli içinden, enlem ayrımı ve gecikme çözünürlüğü olmadan.
- **[TIDA/CTIPe 2022](https://www.swsc-journal.org/articles/swsc/full_html/2022/01/swsc210059/swsc210059.html):** üç fırtınada ensemble Kalman asimilasyonu. Cadılar Bayramı fırtınasında hata %150'nin üstünden yaklaşık %27'ye iniyor, ama yalnız 30 dakikalık öngörüde ve enlem analizi yok.

Weimer 2023'e atıf yapan üç çalışma listelendi; hiçbiri yoğunluktan yoğunluğa gecikmeli tahmin yapmıyor. Liste eksik olabilir, çünkü atıf veritabanlarının çoğu erişimi reddetti.

**Yapılmamış olan**

- Ölçülmüş kutup veya auroral yoğunluğu alçak enlem için regresör olarak kullanmak.
- 1-4 saatlik öngörüde örneklem dışı başarımı puanlamak.
- Sürücü, otoregresyon ve ampirik model tabanlarının üstündeki artışı göstermek.
- Bu artışın fırtınadan fırtınaya değişkenliğini vermek.

**Yeniliğe en büyük tehdit**

Kutup yoğunluğu, L1'de zaten ölçülen bir sürücüye bir saatten kısa sürede tepki veriyor. Bu yüzden sürücü tabanının üstündeki artış küçük çıkabilir. Tez bu sonuca dayanacak biçimde kurulmalı.

**Elle okunması gerekenler (üniversite erişimiyle)**

- [ ] Sutton, Forbes ve Knipp 2009, tam metin
- [ ] Wang ve ark. 2022, LSTM ile fırtına yoğunluğu: [bağlantı](https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2021SW002950). En öncelikli; içeriği hiç doğrulanamadı.
- [ ] Bruinsma ve Forbes 2009 ve 2010 TAD makaleleri
- [ ] Weimer ve ark. 2020, EXTEMPLAR
- [ ] Weimer 2023'e atıf yapanların tam listesi (Google Scholar)

## Veri kaynakları ve erişim

Gereken her veri açık kaynaklarda var, ama yoğunluk dosyalarının indirme adresi buradan doğrulanamadı. İlk iş, TU Delft veya ESA sunucusundan bir dosyayı elle indirip sütunları kontrol etmek.

**Yoğunluk verisi**

| Uydu | Kapsam | Başlangıç irtifası | Eğim | Yerel zaman kayması |
| --- | --- | --- | --- | --- |
| CHAMP | 29 Tem 2000 - 4 Eyl 2010 | \~461 km | 87,3° | 5,44 dk/gün |
| GRACE-A | 4 Nis 2002 - 31 Eki 2017 | \~506 km | 89,0° | 4,47 dk/gün |
| GRACE-B | 4 Nis 2002 - 22 May 2017 | \~506 km | 89,0° | 4,47 dk/gün |
| GRACE-FO C | 29 May 2018'den itibaren | \~507 km | 88,9° | 4,53 dk/gün |

Kaynak: [Siemes ve ark. 2023](https://www.swsc-journal.org/articles/swsc/pdf/2023/01/swsc230004.pdf). Ürün sürümü V2, 10 saniye aralıklı. İki düğüm geçişiyle tüm yerel zamanlar CHAMP için yaklaşık 132, GRACE için 161 günde taranıyor (kayma hızından hesap).

- **TU Delft:** [thermosphere.tudelft.nl](https://thermosphere.tudelft.nl/). FTP sunucusu 13 Aralık 2025'te web sunucusuyla değiştirilmiş. Yeni dizin adresleri ve lisans metni doğrulanamadı.
- **ESA Swarm sunucusu (CDF):** [CHAMP ürün sayfası](https://swarmhandbook.earth.esa.int/catalogue/CH_DNS_ACC_2_), dizin `swarm-diss.eo.esa.int` altında Multimission. Dizin listesi okunamadı.
- **Dosyadaki alanlar:** zaman (UTC), irtifa, coğrafi enlem ve boylam, yerel güneş zamanı, yoğunluk, yörünge ortalaması yoğunluk, geçerlilik bayrağı.
- **Dosyada olmayanlar:** manyetik enlem, enlem argümanı, irtifaya normalize yoğunluk, model yoğunluğu. Dördünü de sen hesaplayacaksın.

**Sağlayıcının belirttiği kalite uyarıları**

- 450 km üstünde ve düşük güneş aktivitesinde radyasyon basıncı belirgin; GRACE ömrünün çoğunu bu rejimde geçirdi.
- GRACE ivmeölçerinin ısıl kontrolü Nisan 2011'de kapatıldı; sonrası özel yanlılık modellemesi gerektiriyor.
- GRACE-D ivmeölçeri fırlatmadan kısa süre sonra bozuldu; GRACE-FO yoğunluğu yalnız C uydusundan.
- Aralık 2008'de GRACE irtifasında helyum baskın hale geldi ve yarımküreler zıt tepki verdi ([Thayer ve ark. 2012](https://colab.ws/articles/10.1029/2012ja017832), özet). 2007-2009 GRACE verisinde işaret sorunu bekle.

**Alternatif veri seti**

[Zenodo 4602380](https://zenodo.org/records/4602380): başlığına göre CHAMP ve GRACE-A yoğunlukları, HASDM ve JB2008 tahminleriyle birlikte. İçeriği açılamadı. Doğruysa JB2008'i kendin çalıştırma yükünü kaldırır; ilk hafta kontrol et.

**Güneş rüzgarı ve indeksler**

| Veri | Kaynak | Not |
| --- | --- | --- |
| Güneş rüzgarı ve IMF, 1 ve 5 dakika | [OMNI yüksek çözünürlük](https://spdf.gsfc.nasa.gov/pub/data/omni/high_res_omni/) | 1981-2026, yıllık ASCII; yay şoku burnuna zaman kaydırılmış |
| AE, AL, AU, SYM-H, ASY-H, PC(N) | Aynı OMNI dosyaları | Ayrı indirme gerekmez |
| Kp, ap, F10.7 | [GFZ](https://kp.gfz.de/en/data) | 1932'den itibaren, JSON API var |
| Dst | [Kyoto WDC](https://wdc.kugi.kyoto-u.ac.jp/dstdir/index.html) | 2020'ye kadar kesin değerler |
| JB2008 güneş indeksleri | [SOLFSMY.TXT](https://sol.spacenvironment.net/JB2008/indices/SOLFSMY.TXT) | F10, S10, M10, Y10, 1997'den itibaren; DTCFILE doğrulanmadı |

OMNI belgesine göre faz cephesi belirlenemeyen yerlerde verinin yaklaşık %4-5'i kayıp ([belge](https://omniweb.gsfc.nasa.gov/html/HROdocum.html)). 2001-2011'e özel boşluk oranı verilmemiş; kendin ölç.

**Python araçları**

| Paket | Sürüm (tarih) | İşlev |
| --- | --- | --- |
| [pymsis](https://pypi.org/project/pymsis/) | 0.13.0 (Eyl 2026) | NRLMSISE-00, MSIS 2.0, 2.1 |
| [pyatmos](https://pypi.org/project/pyatmos/) | 1.2.7 (Kas 2024) | JB2008; yaklaşık iki yıldır sürüm yok |
| [apexpy](https://pypi.org/project/apexpy/) | 2.1.1 (Haz 2026) | Quasi-dipole koordinat, manyetik yerel zaman |
| [aacgmv2](https://pypi.org/project/aacgmv2/) | 2.7.1 (Nis 2026) | AACGM koordinat |
| [cdflib](https://pypi.org/project/cdflib/) | 1.3.14 (Eyl 2026) | CDF okuma |
| [pyspedas](https://pypi.org/project/pyspedas/) | 2.1.5 (Eyl 2026) | OMNI indirme |

## Değişken tanımları ve ön işleme

Normalizasyon planın en çok değişen kısmı: referans model fırtına terimi kapatılmış olarak çalıştırılmalı, yoksa modelin kendi fırtına tepkisi hedef değişkene karışır.

**Normalizasyon: literatürde yapılan**

- **Oliveira 2017:** yoğunluğu JB2008 oranıyla 410 km'ye taşıyor, sonra Dst düzeltmesi sıfırlanmış JB2008'e bölüyor. Analiz edilen büyüklük log10(ρ410 / ρsakin,410).
- **[Bruinsma ve ark. 2021](https://www.swsc-journal.org/articles/swsc/full_html/2021/01/swsc200061/swsc200061.html):** yörünge boyunca gözlem/model oranı kullanıyor, modeli fırtına öncesi evreden bir ölçek katsayısıyla düzeltiyor, 600 km altı ölçekleri yumuşatıyor.

**Önerdiğim tanım (benim tasarımım)**

```latex
y(t) = \ln\frac{\rho_{obs}(t)}{\rho_{ref}(t)} - b_s
```

- ρref: uydunun konumunda, jeomanyetik girdisi sakin değere sabitlenmiş ampirik model. pymsis ile başla; JB2008 ikinci tercih, çünkü Python sarmalayıcısı güncel değil.
- bs: fırtına başına yanlılık, başlangıçtan önceki 24 saatin ortalamasından. Bu, CHAMP ile GRACE arasındaki sabit kaymayı da alır.
- Oran yörünge boyunca alınırsa ayrı irtifa normalizasyonu gerekmez. Oliveira ile karşılaştırma yapacağın doğrulama adımında 410 km'ye taşımayı da uygula.

**Enlem bantları ve koordinat**

| Değişken | Tanım | Gerekçe |
| --- | --- | --- |
| Hedef | Manyetik enlem 30° altı, geçiş ortalaması, her yerel zaman sektörü ayrı | Weimer'da 30° altı gecikme 180-300 dakika |
| Kutup girdisi | Manyetik enlem 63° üstü, geçiş ortalaması, kuzey ve güney ayrı | Oliveira'nın yüksek enlem tanımı |
| Tazelik kontrolü | Manyetik enlem 40°-55°, aynı geçişten | Aşağıdaki model bölümüne bak |
| Cusp bayrağı | Kutup geçişi 10-14 manyetik yerel zamanındaysa 1 | Cusp anomalisi 12 MLT merkezli, ±2 saat genişlikte ([GFZ](https://www.gfz.de/en/section/geomagnetism/topics/ionosphere-and-upper-atmosphere/high-latitude-thermospheric-density)) |

Manyetik koordinat için apexpy (quasi-dipole). Oliveira'nın hangi manyetik koordinatı kullandığı doğrulanamadı; 3° manyetik enlem kutuları kullandığı kesin.

**Zamanlama geometrisi**

CHAMP'in periyodu 93,55 dakika. Bir kutup geçişi tahmin anı sayılırsa sonraki ekvator geçişleri yaklaşık +23, +70, +117, +164, +211 ve +257 dakikada. Ardışık geçişler 12 saat arayla iki yerel zaman sektörüne düşer. Her tahmin örneği bir (kutup geçişi, hedef geçiş) çiftidir.

**Geçiş bölütleme adımları**

1. Geçerlilik bayrağı 1 olan kayıtları at.
2. Her kayıt için manyetik enlem ve manyetik yerel zaman hesapla.
3. Yörüngeyi enlem işaret değişimlerinden yükselen ve alçalan yarım geçişlere böl.
4. Her bant için geçiş ortalamasını al; banttaki geçerli kayıt oranı %70'in altındaysa geçişi eksik say.
5. Her geçişe zaman damgası olarak bant ortasının zamanını ver.

%70 eşiği benim önerim; pilotta eksik veri oranına bakıp sabitle.

**Fırtına kataloğu**

- Oliveira'nın listesi tablo veya ek olarak yayınlanmamış. Yeniden kurman gerekiyor.
- Kaynak: [Richardson ve Cane ICME kataloğu](https://izw1.caltech.edu/ACE/ASC/DATA/level3/icmetable2.htm), Dst minimum sütunuyla.
- Sıfır epok: Oliveira'da güneye keskin Bz dönüşü. Otomatik bir kural yaz ve kuralı teze koy.
- Şiddet sınıfları: Zesta ve Oliveira'nın SYM-H sınıfları (90 zayıf, 78 orta, 28 güçlü, 14 şiddetli, 7 aşırı).
- CIR fırtınaları için [Jian listesi](https://izw1.caltech.edu/ACE/ASC/DATA/level3/SIR_List_1995_2009_Jian.pdf) var. İlk aşamada yalnız CME fırtınalarıyla kal; CIR'ları genişletme olarak bırak.
- Fırtına penceresi: başlangıçtan 24 saat önce ile 72 saat sonra. Örtüşen fırtınaları tek küme say.

**Örneklem büyüklüğü**

| Dönem | Uydu | CME fırtınası |
| --- | --- | --- |
| May 2001 - Eyl 2011 | CHAMP (2010'a kadar) ve GRACE | 168 |
| May 2001 - Ara 2015 | 2010 sonrası yalnız GRACE | 217 |

Fırtına başına yaklaşık 90 hedef geçiş düşer (3 gün × 15,4 yörünge × 2 sektör). Bağımsız birim fırtınadır; etkin örneklem 150-200 arasıdır, 15.000 değil.

## Model merdiveni ve sürücü seti

Merdiven beş basamaktan sekize çıktı: iki kontrol modeli ve bir yalnız sürücü modeli eklendi. Tezin ana sonucu M ile B3 arasındaki fark; kontroller bu farkın başka bir şeyden kaynaklanmadığını gösterir.

**Merdiven**

| Model | Girdi | Yanıtladığı soru |
| --- | --- | --- |
| B0 | Yalnız referans model (y = 0) | Taban hata ne kadar? |
| B1 | Kalıcılık: aynı sektörün son alçak enlem değeri | En basit tahmin ne veriyor? |
| B2 | Alçak enlem geçmişi, son 4 geçiş, iki sektör | Otoregresyon ne katıyor? |
| D | Yalnız sürücüler, yoğunluk geçmişi yok | Yayınlanmış ML modellerinin eşdeğeri |
| B3 | B2 + sürücüler (tahmin anına kadar) | Ana taban |
| B3k | B3 + sürücüler hedef anına kadar (kahin) | Sürücü bilgisinin üst sınırı |
| B3t | B3 + orta enlem (40°-55°) yoğunluğu, aynı geçişten | Tazelik kontrolü |
| M | B3 + kutup yoğunluğu, kuzey ve güney, son 4 geçiş | Ana hipotez |

**İki kontrolün gerekçesi (benim akıl yürütmem)**

- **Tazelik:** kutup geçişi, son ekvator geçişinden yaklaşık 23 dakika sonra gerçekleşir. M'nin kazancı yalnızca daha taze bir ölçümden gelebilir. B3t aynı tazelikte ama kutup dışı bir ölçüm ekler. M, B3t'yi geçmiyorsa bilgi kutba özgü değildir.
- **Kahin sürücü:** B3k'ya hedef anına kadarki güneş rüzgarı verilir. Gerçekte bu bilgi yoktur. M, B3k'yı da geçerse sonuç çok güçlüdür; geçemezse kutup yoğunluğu en fazla gelecekteki sürücü bilgisinin yerini tutuyordur.

**Sürücü seti, A katmanı: gerçek zamanlı erişilebilir**

- L1 hız, yoğunluk, By, Bz. Bunlardan Newell bağlaşım fonksiyonu ve birleşme elektrik alanı.
- Bağlaşımın gecikmeli ortalamaları: 0-1, 1-2, 2-3, 3-4,5 ve 4,5-6 saat. Weimer'ın 180-350 dakikalık alçak enlem gecikmelerini ve Liu'nun 4,5 saatini kapsar.
- Sızıntılı integratörler: Liu'nun 3 saatlik ağırlıklı integrali ve Weimer tarzı üstel sönümlü ısınma terimi. Zaman sabitlerini yalnız eğitim verisinde uydur.
- SYM-H geçmişi, Licata kutularıyla: 0-3, 3-6, 6-9, 9-12, 12-33, 33-57 saat. Nitrik oksit soğumasının ve ön koşullanmanın vekili.
- ap veya Hp30, F10.7 ve 81 günlük ortalaması, yılın günü, yerel zaman, irtifa.
- Şok bayrağı: dinamik basınçta sıçrama. Şok öncülü fırtınalarda nitrik oksit akısı kabaca ikiye katlanıyor ve yoğunluk yaklaşık 24 saat içinde sert düşüyor ([Knipp ve ark. 2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5562409/)).

**B katmanı: sonradan işlenmiş, ek olarak**

- W05 toplam Poynting akısı, kuzey ve güney (Weimer 2023 ve CHAMP-ML'de kullanılan).
- Kesin SYM-H, ASY-H, AE, AL ve PC(N).
- S10, M10, Y10.

Ana analizi A katmanıyla yap; B katmanını duyarlılık testi olarak ekle. W05'in açık bir Python uygulaması olup olmadığını doğrulamadım.

```latex
\frac{d\Phi_{MP}}{dt} = v^{4/3}\, B_T^{2/3}\, \sin^{8/3}(\theta/2)
```

Newell formülü ikincil bir kaynaktan doğrulandı ([arXiv 1805.10699](https://arxiv.org/pdf/1805.10699)); Newell 2007'nin kendisi açılamadı. Bağlaşım fonksiyonlarını yoğunluğa karşı sıralayan bir çalışma bulunamadı; hangisinin daha iyi olduğunu veride sen göreceksin.

**Karşılaştırma ölçütleri: yayınlanmış ML modelleri**

| Model | Ufuk | Kendi yoğunluğu girdi mi | Bölme | Fırtına başarımı |
| --- | --- | --- | --- | --- |
| [CHAMP-ML](https://arxiv.org/html/2206.05824) | Anlık | Hayır | Haftalık döner | Genel test hatası \~%11,6 |
| [Karman](https://nora.nerc.ac.uk/id/eprint/536861/1/Space%20Weather%20-%202024%20-%20Acciarini%20-%20Improving%20Thermospheric%20Density%20Predictions%20in%20Low%E2%80%90Earth%20Orbit%20With%20Machine%20Learning.pdf) | Anlık | Hayır | Aylık blok | Ap 50 üstü: %13,5 (JB2008 %20,4) |
| [AETHER-P3](https://arxiv.org/html/2608.00352) | 6 saat | Hayır | 3-6 saat tampon | Aşırı koşulda \~%28 hata |
| [Transformer 2025](https://arxiv.org/html/2511.06105v1) | 3 gün | Hayır | Rastgele 80/20 | Fırtına ayrıştırması yok |

B3'ün 1-4 saatlik fırtına başarımı için doğrudan yayınlanmış bir karşılaştırma yok. En yakını AETHER-P3. Ampirik modeller için Bruinsma 2021: DTM2013 standart sapması %25,5, korelasyon 0,85 (13 fırtına).

**Model sınıfı**

1. Ridge regresyon, her basamak için. Katsayılar yorumlanabilir.
2. Gradient boosting, aynı girdilerle. Doğrusal olmayan etkileşimleri yakalar.
3. Derin dizi modeli yok. Etkin örneklem 150-200 fırtına.

Her öngörü süresi için ayrı model eğit, ya da öngörü süresini girdi yapıp tek model eğit. İkisini pilotta karşılaştır, birini seç, sabitle.

## İstatistik tasarım

Birincil test, fırtına başına eşli kayıp farkı üzerinde küme bootstrap'idir; doğrulayıcı test, kutup girdisini fırtınalar arasında karıştıran permütasyondur. Test seçimi ve güç hesabı araştırma ajanının ve benim yargım; dayandığı referanslar aşağıda.

**Çapraz doğrulama**

- Fırtına bazında grupla (scikit-learn `GroupKFold`). Aynı fırtına hem eğitimde hem testte olamaz ([scikit-learn](https://scikit-learn.org/stable/modules/cross_validation.html)).
- Örtüşen fırtınaları ve aynı fırtınanın iki uydusunu tek grup say.
- Gruplar arasında en az 57 saat tampon bırak; en uzun öznitelik hafızası bu.
- Hiperparametre ayarı iç içe: iç ve dış döngüde fırtına gruplu. Ölçekleyicileri her katmanın içinde uydur. Değerlendirme verisinde ayar yapmak seçim yanlılığı üretir ([Cawley ve Talbot 2010](https://jmlr.csail.mit.edu/beta/papers/v11/cawley10a.html)).

**Birincil test**

```latex
d_s = \mathrm{MSE}_{B3,s} - \mathrm{MSE}_{M,s}
```

- Her fırtına s için tek değer; iki modelin tahminleri fırtına dışı katmandan.
- Göreli RMSE azalması için %95 güven aralığı: fırtınaları yerine koyarak 10.000 kez yeniden örnekle ([Cameron ve Miller 2015](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015_February.pdf)). Az küme sorunu 20-50 kümenin altında başlar; 150 fırtına rahat.

**Doğrulayıcı test**

Kutup girdi bloğunu fırtınalar arasında karıştır (şiddet sınıfı ve öngörü süresi eşleştirilerek), modeli yeniden uydur, gözlenen kazancı sıfır dağılımıyla karşılaştır. Bu, fırtına içi otokorelasyonu ve iç içe model sorununu birlikte çözer: büyük model, gerçekte sıfır olan parametreleri tahmin ettiği için hatası şişer ([Clark ve West](https://ideas.repec.org/p/fip/fedkrw/rwp05-05.html)).

Diebold-Mariano ve Clark-West testlerini yalnız ikincil olarak ver. Tek bir kesintisiz zaman serisi varsayarlar; fırtınalar arası boşluklarla uyumsuzdurlar.

**Güç (tahmin, kaynaklı değil)**

Eşli testte %80 güç ve iki yönlü 0,05 düzeyinde saptanabilir ortalama fark yaklaşık 2,8 × SD / √G.

| Fırtına sayısı | Saptanabilir fark | SD %10 ise | SD %25 ise |
| --- | --- | --- | --- |
| 30 (pilot) | 0,51 SD | \~%5 MSE | \~%13 MSE |
| 150 | 0,23 SD | \~%2,3 MSE | \~%5,7 MSE |
| 200 | 0,20 SD | \~%2,0 MSE | \~%5,0 MSE |

Göreli RMSE azalması kabaca MSE azalmasının yarısıdır. Belirleyici olan fırtınadan fırtınaya değişkenliktir (SD), 15.000 örnek değil. SD'yi pilotta ölç, eşiği ondan sonra sabitle.

**Çoklu test**

Birincil test tektir: dört öngörü süresi havuzlanmış. Öngörü süresi başına dört ayrı test ikincildir ve Holm düzeltmesi alır. Ayrıştırmaların tamamı keşif amaçlı diye etiketlenir.

**Ayrıştırmalar (keşif amaçlı)**

- Öngörü süresi: +70, +117, +164, +211, +257 dakika.
- Fırtına evresi: Bruinsma 2021'deki gibi Dst minimumuna göre dört evre.
- Şiddet sınıfı: beş SYM-H sınıfı. Aşırı sınıfta yalnız 7 fırtına var; bu sınıf için istatistik iddia kurulamaz.
- Hedefin yerel zamanı: gündüz ve gece. Weimer'da gündüz tarafı daha erken tepki veriyor.
- Kutup geçişinin yerel zamanı ve cusp bayrağı.
- Mevsim ve yarımküre.
- Uydu: CHAMP ve GRACE ayrı.

**Raporlanacak ölçüler**

Tek ölçü yetmez ([Liemohn ve ark. 2021](https://deepblue.lib.umich.edu/handle/2027.42/171097)). Her model için:

- Log-oran artığının ortalaması ve standart sapması (Bruinsma 2021 uylaması).
- RMSE ve korelasyon.
- Beceri puanı, 1 − MSE/MSEref, hem kalıcılığa hem B3'e göre.
- Fırtına başına tepe genliği hatası ve tepe zamanlama hatası.

**Bilgi kuramı eki (isteğe bağlı)**

Koşullu karşılıklı bilgi, karıştırıcıyı dışarıda tutarak bağımlılığı ölçer; güneş rüzgarı çalışmalarında kullanılmış ([Wing ve ark. 2016](https://ecamporeale.github.io/papers/wing2016.pdf)). Buradaki karşılığı: kutup yoğunluğu ile gelecekteki alçak enlem yoğunluğu arasındaki bilgi, sürücüler ve geçmiş verilmişken. Termosfer yoğunluğuna uygulanmış bir örnek bulunamadı. Zaman kalırsa ekle, planın parçası yapma.

## Dur/devam kapısı

Kapı üçüncü haftanın sonunda, 30 fırtınalık bir pilotla kurulur. Dikkat: 30 fırtına yalnız büyük etkiyi saptar (yaklaşık 0,5 SD). Kapının asıl işi karar vermek kadar, fırtınalar arası değişkenliği ölçüp ana analizin eşiğini sabitlemektir. Bu bölümün tamamı benim tasarımım.

**Pilot fırtınaların seçimi**

- 30 fırtına, şiddet sınıflarına orantılı, rastgele ve tohumu kayıtlı.
- Yalnız CHAMP, 2002-2005. Güneş aktivitesi yüksek, veri kalitesi en iyi.
- Pilot fırtınaları ana analizde de kullanılır, ama eşik belirlendikten sonra model tasarımına dokunulmaz.

**Önce hat doğrulaması**

Kapıdan önce Oliveira 2017'nin sonucunu yeniden üret: üst üste bindirilmiş epok analizinde yüksek enlem ilk 1,5 saatte, ekvator 3 saat içinde yükselmeli. Çıkmıyorsa sorun veri hattındadır; kapı testine geçme.

**Kapıda hesaplanacaklar**

1. B2, B3, B3t ve M'yi ridge regresyonla, A katmanı sürücülerle, fırtına dışı katmanlarda uydur.
2. Fırtına başına kayıp farkını ve standart sapmasını hesapla.
3. Kısmi korelasyon: sürücüler ve alçak enlem geçmişi regresyonla çıkarıldıktan sonra, kutup anomalisi artığı ile hedef artığı arasında, öngörü süresi başına.
4. B3'ün D'ye göre kazancı (ikincil hipotez H4).

**Karar kuralları**

| Pilot sonucu | Karar |
| --- | --- |
| M, B3'ü ve B3t'yi göreli RMSE'de en az %3 geçiyor | Devam. Ana analiz plandaki gibi. |
| M, B3'ü geçiyor ama B3t'yi geçmiyor | Devam, soru değişir: bilgi kutba özgü değil, taze ölçümün değeri. |
| Kazanç %1'in altında, H4 güçlü | Devam, ağırlık kayar: tez “kendi geçmişini kullanan kısa ufuklu tahmin” üzerine kurulur, kutup sonucu sıfır sonuç bölümü olur. |
| Kazanç %1'in altında, H4 de zayıf | Dur. Danışmanla konuş; yedek konuya geç. |
| Hat doğrulaması başarısız | Bir hafta hata ayıkla; düzelmezse dur. |

%3 ve %1 eşikleri benim önerim, bir kaynaktan gelmiyor. Pilot SD'sini görünce güncelle, ama ana analizden önce ve yazılı olarak.

**Yedek konu**

Kapı kapanırsa Şubat başında 10 hafta kalır. Kurulmuş veri hattı boşa gitmez: fırtına hata ayrıştırması ve ortak mod fikirleri aynı yoğunluk ve sürücü verisini kullanır.

## Çapraz uydu testi ve yörünge etkisi

Yörünge bölümünün sonucu küçük çıkacak: kaba hesap, CHAMP sınıfı bir uydu için 4 saatte metre mertebesinde kazanç veriyor. Bölüm tezi uzay mühendisliğine bağlamak için gerekli, ama katkının kendisi değil.

**Çapraz uydu testi**

CHAMP'in kutup ölçümüyle GRACE'in alçak enlem yoğunluğunu tahmin et; ve tersini. Örtüşme dönemi Nisan 2002 - Eylül 2010.

- İki uydu farklı yerel zaman düzlemlerinde ve düzlemler arasındaki açı zamanla değişiyor (kayma hızları 5,44 ve 4,47 dk/gün). Kazancı düzlem ayrıklığına göre çiz.
- İrtifa farkı genliği değiştirir: bir çalışmada GRACE'in fırtına genliği CHAMP'inkinin yaklaşık %30'u ([Liu ve ark. 2011](https://angeo.copernicus.org/articles/29/443/2011/), özet). Log-oran ve fırtına öncesi düzeltme sabit kaymayı alır, genlik ölçeğini almaz. Uydu çiftine özel bir ölçek katsayısını modelde serbest bırak.
- Bu test operasyonel senaryoya en yakın olandır: bir uydunun ölçümü başka bir uyduya yarıyor mu?

**Yoğunluk hatasından konum hatasına: birinci mertebe ilişki**

```latex
\delta s \approx \tfrac{3}{2}\, a_{drag}\, \varepsilon\, t^{2}, \qquad a_{drag} = \tfrac{1}{2}\,\rho\, v^{2}\, \frac{C_D A}{m}
```

Bu ifade kendi türetmemiz; bunu açıkça yazan bir kaynak bulunamadı. Teze koymadan önce Emmert 2017'den doğrula. Hata yalnız τ süresince sürüp sonra düzelirse, sonrasında büyüme doğrusaldır: δs ≈ 3·a·ε·τ·(t − τ/2).

**Örnek sayılar (kendi hesabımız, örnekleyici)**

Varsayım: yoğunluk 4×10⁻¹² kg/m³ (güneş maksimumuna yakın, 400 km), hız 7669 m/s, tüm yörüngede %20 yoğunluk hatası.

| Nesne | CdA/m (m²/kg) | 4 saatte | 24 saatte |
| --- | --- | --- | --- |
| CHAMP | 0,00477 | \~35 m | \~1,3 km |
| 3U küp uydu | 0,0165 (varsayım) | \~120 m | \~4,3 km |
| Yüksek alan/kütle, üst sınır | 0,131 | \~0,96 km | \~34 km |

CHAMP katsayısı [Gondelach ve Linares](https://arxiv.org/pdf/1910.00695)'ten. Son satır, Şubat 2022'de kaybedilen Starlink partisi için bir makalenin varsaydığı değerler (260 kg, 15,45 m²); operasyonel düşük sürüklenme yönelimini temsil etmez.

**Tezin kazancı bu tabloya nasıl ölçeklenir**

- Tahmin yalnız alçak enlem bandını kapsıyor. Kutupsal yörüngede uydu zamanının %33'ünü, 53° eğimde %43'ünü 30° enlem altında geçirir (kendi türetmemiz).
- Kazanç, hatanın tamamı değil, azalan kısmıdır. Örnek: alçak enlem hatası %20'den %18'e inerse, yörünge ortalamasında eşdeğer hata azalması yaklaşık %0,7 olur.
- Bu, CHAMP için 4 saatte yaklaşık 1 metre, üst sınır nesnesi için yaklaşık 30 metre demek.

**Değerlendirme protokolü**

1. Doğruluk referansı: CHAMP'in gerçek yörüngesi boyunca ivmeölçer yoğunluğuyla Sidera'da yayılım.
2. Tahmin koşuları: aynı başlangıç, alçak enlem bandında B3 ve M tahmini, bandın dışında referans yoğunluk.
3. Sürüklenme katsayısını sabit tut. Katsayıyı uydurmak yoğunluk yanlılığını emer ve daha iyi modelin faydasını gizler ([NEOSST2 bildirisi](https://conference.sdo.esoc.esa.int/proceedings/neosst2/paper/90/NEOSST2-paper90.pdf)).
4. İz boyunca hatayı 1, 2, 3 ve 4 saatte raporla; üç balistik katsayı için tekrarla.
5. Yoğunluk hatasının zamansal korelasyonunu koru. Bir çalışmada iz boyunca belirsizlik, korelasyonsuz örneklemede 96 m, korelasyonlu örneklemede 951-4898 m çıkmış ([arXiv 2210.16992](https://arxiv.org/pdf/2210.16992)).

Açılan makalelerin hiçbiri ivmeölçer yoğunluğunu doğruluk referansı alarak yayılım yapmıyor; en yakınları hassas yörüngeyi referans alıyor.

**Operasyonel gerekçe nasıl kurulmalı**

Saat ölçekli yoğunluk tahmininin operasyonel değerini doğrudan savunan bir makale bulunamadı. 1-7 günlük çarpışma taraması üzerinden savunma; geç güncelleme ve otonom manevra zaman çizelgeleri üzerinden savun:

- Starlink otonom manevra yapıyor; acil yörünge değişikliği için 8 saat önceden bildirim öngörülüyor ([NASA-SpaceX anlaşması](https://www.nasa.gov/sites/default/files/atoms/files/nasa-spacex_starlink_agreement_final.pdf)).
- Kaçınma manevrasının planlanıp yürütülmesi birkaç saat sürüyor; olayların yaklaşık %2'si son 24 saatte saptanıyor ([ESOC](https://ilrs.gsfc.nasa.gov/lw21/docs/2018/papers/SessionSD3_Funke_paper.pdf)).
- Aşırı bir fırtınanın başlangıcından sonraki 72 saatte GRACE 55 m alçaldı, arka planın 11 katı ([Oliveira ve ark. 2021](https://www.frontiersin.org/journals/astronomy-and-space-sciences/articles/10.3389/fspas.2021.764144/full)).

## Takvim

Araştırma penceresi 18 Ocak - 18 Nisan 2027, 13 hafta; yazım 19 Nisan - 1 Haziran. Kapı kararı 7 Şubat'ta. Takvim benim önerim; dönem içi ders yükünü bilmediğim için haftalık süreleri sen ayarla.

**Ocak öncesi hazırlık (SciTech tesliminden sonra, toplam birkaç gün)**

- [ ] TU Delft veya ESA sunucusundan bir aylık CHAMP dosyası indir, sütunları doğrula
- [ ] Zenodo 4602380'in içeriğine bak
- [ ] Elle okunacak beş makaleyi oku (Literatür bölümündeki liste)
- [ ] Emmert 2017'yi oku; yörünge bölümündeki formülü doğrula
- [ ] Hipotezleri ve ölçütleri bir sayfada yaz, danışmana gönder
- [ ] Sidera'da keyfi yoğunluk fonksiyonuyla sürüklenme yayılımının çalıştığını tek bir koşuyla sına

**Haftalık iş paketleri**

| Hafta | Başlangıç | İş | Çıktı |
| --- | --- | --- | --- |
| 1 | 18 Oca | Yoğunluk ve OMNI indirme, CDF okuma, manyetik koordinat, geçiş bölütleme | Geçiş tablosu (uydu, zaman, bant, ortalama) |
| 2 | 25 Oca | Referans model, fırtına kataloğu, fırtına öncesi düzeltme | Normalize hedef ve girdi serileri |
| 3 | 1 Şub | Oliveira sonucunu yeniden üretme; 30 fırtınalık pilot | Kapı raporu, sabitlenmiş eşik |
| 4 | 8 Şub | B0, B1, B2; doğrulama iskeleti | Fırtına gruplu çapraz doğrulama kodu |
| 5 | 15 Şub | Sürücü öznitelikleri, A katmanı; D ve B3 | Öznitelik tablosu |
| 6 | 22 Şub | B3 ayarı, sızıntılı integratör sabitleri, B3k | B3'ün nihai hali, H4 sonucu |
| 7 | 1 Mar | M ve B3t; birincil test | Ana sonuç ve güven aralığı |
| 8 | 8 Mar | Permütasyon testi; B katmanı duyarlılığı | Doğrulayıcı test sonucu |
| 9 | 15 Mar | Çapraz uydu testi | Düzlem ayrıklığına göre kazanç eğrisi |
| 10 | 22 Mar | Ayrıştırmalar | Evre, şiddet, yerel zaman tabloları |
| 11 | 29 Mar | Gradient boosting, yalnız sinyal varsa; yoksa tampon | Doğrusal olmayan karşılaştırma |
| 12 | 5 Nis | Yörünge yayılım protokolü | Konum hatası tablosu |
| 13 | 12 Nis | Tampon ve şekiller | Tez şekillerinin taslakları |

**Kapsam dışı (plana ekleme)**

- CIR fırtınaları, GRACE-FO, Swarm.
- Derin dizi modelleri.
- Gerçek zamanlı sistem prototipi.
- Asimilasyon modelleriyle karşılaştırma.

Kapsam genişletme eğilimine karşı kural: 11. haftadan önce bu listeden hiçbir şey açılmaz.

**En sıkışık yerler**

- Hafta 1-2: dosyada olmayan dört alanı hesaplamak ve fırtına kataloğunu yeniden kurmak. İkisi de göründüğünden uzun sürebilir.
- Hafta 5-6: B3. Planın en çok emek isteyen kısmı; üç haftaya taşarsa 11. haftanın tamponu buraya gider.

## Riskler, açık sorular ve doğrulanamayan noktalar

En büyük risk sıfır sonuçtur ve ihtimali düşük değil; plan buna göre iki ayaklı kuruldu (H1 ve H4). Bu ihtimale bir sayı veremem; elimde onu tahmin edecek veri yok.

**Riskler**

| Risk | Neden ciddi | Karşı önlem |
| --- | --- | --- |
| Kutup yoğunluğu sürücülerin ötesinde bilgi taşımıyor | Kutup, L1'de ölçülen sürücüye bir saatten kısa sürede tepki veriyor | H4 ikincil sonuç; sıfır sonucun üst sınırla raporlanması |
| Güçlü fırtınalarda pencere kapanıyor | Aşırı fırtınada ekvator \~1,5 saatte tepki veriyor | Şiddet sınıfına göre ayrıştırma; H3 olarak önceden yazılı |
| Uydu ısınan bölgeyi ıskalıyor | Isıtma yerel, uydu tek yerel zaman düzleminde | Kutup geçişinin yerel zamanına göre ayrıştırma; kuzey ve güney ayrı girdi |
| Cusp anomalisi kutup girdisini kirletiyor | 12 MLT çevresinde fırtınadan bağımsız yoğunluk artışı | Cusp bayrağı; bayraklı geçişler dışlanarak duyarlılık testi |
| Referans modelin fırtına tepkisi hedefe sızıyor | Oran yapay olarak düzleşir | Jeomanyetik girdisi sabitlenmiş referans |
| GRACE verisi güneş minimumunda güvenilmez | Helyum ve radyasyon basıncı | 2007-2009 GRACE'i ana analizden çıkar, duyarlılık testi yap |
| Sızıntı | Fırtına içi otokorelasyon, 57 saatlik öznitelik hafızası | Fırtına gruplu bölme, tampon, iç içe ayar |
| Yörünge etkisi önemsiz çıkıyor | Kaba hesap metre mertebesi veriyor | Bölümü dürüstçe küçük sayılarla yaz; katkıyı yoğunluk tahminine dayandır |
| Danışman uyumu | Konu veri ve istatistik ağırlıklı, kontrol değil | Yörünge bölümü; ön kayıt belgesini erken paylaş |
| Bir başkası aynı testi yayınlıyor | Alan hareketli; 2025-2026'da beşten fazla ilgili ML makalesi | Ocak'ta ve Mart'ta atıf taramasını tekrarla |

**Açık sorular (cevabı sende veya danışmanda)**

- [ ] Sidera'da MSIS veya JB2008 var mı, yoksa pymsis mi kullanılacak?
- [ ] Sidera keyfi bir yoğunluk fonksiyonuyla sürüklenme yayılımını doğrulanmış biçimde yapıyor mu?
- [ ] İTÜ bitirme kuralları kamuya açık veriyle yapılan analiz ağırlıklı bir tezi kabul ediyor mu?
- [ ] Jüride yörünge mekaniği veya uzay havası bilen biri olabilir mi?

**Doğrulanamayan noktalar**

- TU Delft'in yeni indirme adresi, dosya adlandırması, ASCII sütun düzeni ve lisansı.
- ESA sunucusunun dizin listesi; uydu başına veri boşlukları.
- Zenodo 4602380'in içeriği; JB2008 DTCFILE'ın erişilebilirliği.
- CHAMP ve GRACE'in 2011 sonundaki irtifaları (yalnız başlangıç irtifaları bulundu).
- Sutton 2009, Wang 2022, Bruinsma ve Forbes 2009/2010, EXTEMPLAR 2020 tam metinleri.
- Emmert 2017, Anderson 2009/2013, Hejduk ve Snow 2018: yörünge hatası literatürünün ana makaleleri, hiçbiri açılamadı.
- Newell 2007'nin yoğunlukla korelasyon değerleri; Kan-Lee formülünün üssü.
- Oliveira'nın kullandığı manyetik koordinat sistemi.
- Weimer 2023'e atıf yapanların tam listesi; konferans literatürü (AMOS, AAS, AGU özetleri) taranmadı.

**Bu dokümanın sınırı**

Kaynak sayfaları otomatik bir okuyucu üzerinden özetlendi. Tabloya giren sayıları teze almadan önce asıl PDF'ten kontrol et; özellikle Bruinsma 2021 ve 2024 standart sapmaları farklı tanımlarla hesaplanmış, birbiriyle karşılaştırılamaz.

## Kaynaklar

Yalnız sayfası açılmış kaynaklar listelendi. “Özet” notu, tam metnin okunamadığını gösterir.

**Fizik ve gecikmeler**

- [Oliveira ve ark. 2017, 168 fırtınalık epok analizi](https://arxiv.org/pdf/1710.07743)
- [Zesta ve Oliveira 2019, ısınma ve soğuma süreleri](https://ntrs.nasa.gov/api/citations/20200000388/downloads/20200000388.pdf)
- [Weimer ve ark. 2023, gecikme haritaları](https://spacewx.com/wp-content/uploads/2023/06/Space-Weather-2023-Weimer-Global-Variations-in-the-Time-Delays-Between-Polar-Ionospheric-Heating-and-the-Neutral.pdf)
- [Liu ve ark. 2010](https://angeo.copernicus.org/articles/28/1633/2010/) (özet) ve [Liu ve ark. 2011](https://angeo.copernicus.org/articles/29/443/2011/) (özet)
- [Sutton, Forbes ve Knipp 2009](https://api.crossref.org/works/10.1029/2008JA013667) (özet)
- [Bruinsma ve Forbes 2007](https://api.crossref.org/works/10.1029/2007GL030243) (özet)
- [Knipp ve ark. 2017, nitrik oksit soğuması](https://pmc.ncbi.nlm.nih.gov/articles/PMC5562409/)
- [Thayer ve ark. 2012, helyum](https://colab.ws/articles/10.1029/2012ja017832) (özet)
- [GFZ, yüksek enlem yoğunluk anomalisi](https://www.gfz.de/en/section/geomagnetism/topics/ionosphere-and-upper-atmosphere/high-latitude-thermospheric-density)

**Asimilasyon ve ML modelleri**

- [Sutton 2018](https://api.crossref.org/works/10.1002/2017SW001785) (özet)
- [TIDA/CTIPe 2022](https://www.swsc-journal.org/articles/swsc/full_html/2022/01/swsc210059/swsc210059.html)
- [CHAMP-ML](https://arxiv.org/html/2206.05824) ve [MSIS-UQ](https://arxiv.org/pdf/2208.11619)
- [Karman, Acciarini ve ark. 2024](https://nora.nerc.ac.uk/id/eprint/536861/1/Space%20Weather%20-%202024%20-%20Acciarini%20-%20Improving%20Thermospheric%20Density%20Predictions%20in%20Low%E2%80%90Earth%20Orbit%20With%20Machine%20Learning.pdf)
- [AETHER-P3, 2026](https://arxiv.org/html/2608.00352)
- [Transformer çoklu uydu tahmini, 2025](https://arxiv.org/html/2511.06105v1)
- [EXTEMPLAR-ML, Licata 2021](https://vtechworks.lib.vt.edu/server/api/core/bitstreams/6b34ab04-f8b4-4c61-b3b9-bd71208bcad9/content)

**Model değerlendirme**

- [Bruinsma ve ark. 2021, 13 fırtına](https://www.swsc-journal.org/articles/swsc/full_html/2021/01/swsc200061/swsc200061.html)
- [Bruinsma ve Laurens 2024, 152 fırtına](https://www.swsc-journal.org/articles/swsc/full_html/2024/01/swsc240020/swsc240020.html)
- [Oliveira ve ark. 2021, aşırı fırtınalarda JB2008 ve HASDM](https://www.frontiersin.org/journals/astronomy-and-space-sciences/articles/10.3389/fspas.2021.764144/full)
- [Liemohn ve ark. 2021, ölçüler](https://deepblue.lib.umich.edu/handle/2027.42/171097) (özet)

**Veri ve araçlar**

- [Siemes ve ark. 2023, yoğunluk veri setleri](https://www.swsc-journal.org/articles/swsc/pdf/2023/01/swsc230004.pdf)
- [TU Delft termosfer verisi](https://thermosphere.tudelft.nl/)
- [ESA Swarm el kitabı, CHAMP yoğunluk ürünü](https://swarmhandbook.earth.esa.int/catalogue/CH_DNS_ACC_2_)
- [OMNI yüksek çözünürlük dizini](https://spdf.gsfc.nasa.gov/pub/data/omni/high_res_omni/) ve [belgesi](https://omniweb.gsfc.nasa.gov/html/HROdocum.html)
- [GFZ Kp, ap, F10.7](https://kp.gfz.de/en/data)
- [Kyoto Dst](https://wdc.kugi.kyoto-u.ac.jp/dstdir/index.html)
- [Richardson ve Cane ICME kataloğu](https://izw1.caltech.edu/ACE/ASC/DATA/level3/icmetable2.htm)
- [SWPC gerçek zamanlı güneş rüzgarı](https://www.spaceweather.gov/products/solar-wind)

**İstatistik**

- [scikit-learn, gruplu çapraz doğrulama](https://scikit-learn.org/stable/modules/cross_validation.html)
- [Cameron ve Miller 2015, küme bootstrap](https://cameron.econ.ucdavis.edu/research/Cameron_Miller_JHR_2015_February.pdf)
- [Clark ve West, iç içe modeller](https://ideas.repec.org/p/fip/fedkrw/rwp05-05.html) (özet)
- [Cawley ve Talbot 2010](https://jmlr.csail.mit.edu/beta/papers/v11/cawley10a.html) (özet)
- [Wing ve ark. 2016, transfer entropisi](https://ecamporeale.github.io/papers/wing2016.pdf)

**Yörünge etkisi**

- [Gondelach ve Linares 2020](https://arxiv.org/pdf/1910.00695)
- [Yörünge belirsizliği ve ML yoğunluk modelleri](https://arxiv.org/pdf/2210.16992)
- [NEOSST2 bildirisi 90](https://conference.sdo.esoc.esa.int/proceedings/neosst2/paper/90/NEOSST2-paper90.pdf)
- [ESA SDC8 bildirisi 25](https://conference.sdo.esoc.esa.int/proceedings/sdc8/paper/25/SDC8-paper25.pdf)
- [NASA-SpaceX anlaşması](https://www.nasa.gov/sites/default/files/atoms/files/nasa-spacex_starlink_agreement_final.pdf)
- [ESOC, çarpışma kaçınma operasyonları](https://ilrs.gsfc.nasa.gov/lw21/docs/2018/papers/SessionSD3_Funke_paper.pdf)
