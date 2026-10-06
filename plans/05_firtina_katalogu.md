# 05 — Fırtına kataloğu ve sıfır epok

Hazırlanma: 5 Ekim 2026. Ana plan: `../00_ana_plan.md`, "Fırtına kataloğu" ve "Örneklem büyüklüğü".

**Etiketler.** `[OKUNDU]` kaynak bu oturumda araştırma ajanı tarafından açıldı (tam metin). `[ÖZET]` yalnız özet/üst veri. `[DOĞRULANMADI]` açılamadı. Tasarım önerileri "öneri" diye işaretli; kaynaktan gelmiyor.

## Ana plana göre değişenler

1. **168 sayısı JGR makalesinin sayısı değil.** arXiv 1710.07743 bir sempozyum bildirisi (168 fırtına, Mayıs 2001 - Eylül 2011). Aynı ekibin JGR 2017 makalesi (doi 10.1002/2017JA024006) özetinde **159 fırtına, Eylül 2001 - Eylül 2011** diyor `[ÖZET]`. Hedef sayı açıkça seçilmeli; öneri: 217'lik 2019 tanımı hedef, 168/159 yalnız hat doğrulamasında kıyas.
2. **Liste hiçbir yerde yayınlanmamış** (bildiri, 2019 GRL, 2019 Space Weather ön baskısı, NTRS, Zenodo araması). Tek olasılık JGR makalesinin Wiley ek dosyası; açılamadı `[DOĞRULANMADI]`.
3. **Sıfır epok elle seçilmiş.** "by inspecting the OMNI data visually, as the time in which the IMF Bz turns abruptly southward" (bildiri §4). Algoritma yok. Otomatik kural bizim katkımız olacak ve teze yazılacak.
4. **217 birebir üretilemeyebilir.** Richardson-Cane sayfası 23 Temmuz 2026'da gözden geçirilmiş; 2001-2015 için bugün **334 ICME satırı** var. 2019 makaleleri eski bir sürümü ve belirtilmemiş bir eleme kuralını kullandı.
5. **Uydu başına fırtına sayısı eşit değil.** 2019 Space Weather ön baskısı metni: CHAMP 151, GRACE 213, ikisinde birden 147, toplam 217. Aynı makalenin Şekil 1 göstergesi 153 / 210 diyor; kaynak kendi içinde tutarsız. Yalnız GRACE-A kullanılmış.

## Kaynak kataloglar

| Katalog | Erişim | Durum |
| --- | --- | --- |
| Richardson ve Cane ICME | [Harvard Dataverse, doi 10.7910/DVN/C2MHTH](https://doi.org/10.7910/DVN/C2MHTH): `icmetable2.xlsx` (82,5 kB), sürüm 5.1, 30 Tem 2026, **CC0** | `[OKUNDU]` Birincil kaynak |
| Aynısı, HTML | [icmetable2.htm](https://izw1.caltech.edu/ACE/ASC/DATA/level3/icmetable2.htm), 1996/05/27 - 2026/07/03 | `[OKUNDU]` |
| HELIO4CAST ICMECAT v2.3 | [helioforecast.space/icmecat](https://helioforecast.space/icmecat), csv/json; 1 AU'da Wind | `[OKUNDU]` Yayında kullanılırsa ortak yazarlık için iletişim isteniyor; yalnız çapraz kontrol için kullan |
| CfA şok veritabanı | [lweb.cfa.harvard.edu/shocks](https://lweb.cfa.harvard.edu/shocks/), Wind 1995-2024, ACE 1998-2014, yalnız HTML | `[OKUNDU, dizin]` Şok bayrağı için |
| SSC listesi (Ebre/ISGI) | [obsebre.es](https://www.obsebre.es/en/variations/rapid), `ssc_[YIL]_d.txt`, CC BY-NC 4.0 | `[OKUNDU, özetleyici]` Yıllık dosya açılmadı |
| Walach fırtına listesi 1981-2022 | [doi 10.17635/lancaster/researchdata/659](https://research.lancaster-university.uk/en/datasets/geomagnetic-storm-list-1981-2022/), CC BY | `[OKUNDU, açılış sayfası]` Eşik dosya adına göre −80 nT; zayıf ve orta sınıfı (217'nin 168'i) kaçırır |
| Pedersen ve ark. 2024 | doi 10.1029/2024JA032656: 755 fırtına, 1996-2023, sürücü etiketli | `[ÖZET]` Nerede barındırıldığı bilinmiyor |
| Jian SIR listesi | [PDF](https://izw1.caltech.edu/ACE/ASC/DATA/level3/SIR_List_1995_2009_Jian.pdf), 1995-2009 | `[DOĞRULANMADI]` İçerik açılmadı; kapsam dışı (CIR) |

**Richardson-Cane sütunları** `[OKUNDU]`: Disturbance Y/M/D (UT) (a); ICME Plasma/Field Start, End (b); Comp. Start, End (c); MC Start, End (d); BDE? (e); BIF? (f); Qual. (g); dV (h); V_ICME (i); V_max (j); B (k); MC? (l); **Dst (nT) (m)**; V_transit (n); LASCO CME (o).

Dikkat: (a) sütunu **ani başlangıç (SSC) / şok zamanı**, ana evre başlangıcı değil. Bz dönüşü bundan tipik olarak bir saatten az, bazı olaylarda 6 saate kadar sonra (bildiri s. 6).

2001-2015 yıllık satır sayıları (HTML'den ayrıştırma): 48, 26, 22, 21, 31, 13, 2, 3, 11, 15, 32, 35, 25, 20, 30.

## Şiddet sınıfları

Zesta ve Oliveira 2019 (GRL 46, doi 10.1029/2019GL085120) Tablo 1 `[OKUNDU]`. Sınır işaretleri için Oliveira ve Zesta 2019 (Space Weather, arXiv 1910.09622) biçimini kullan; GRL'deki katı eşitsizlikler sınır değerlerini tanımsız bırakıyor.

| Sınıf | En düşük SYM-H (nT) | Fırtına | En yüksek değere süre (sa) | %25'e dönüş (sa) |
| --- | --- | --- | --- | --- |
| Zayıf | SYM-H ≥ −50 | 90 | 61,75 | 71,75 |
| Orta | −100 ≤ SYM-H < −50 | 78 | 10,25 | 46,00 |
| Güçlü | −150 ≤ SYM-H < −100 | 28 | 14,50 | 37,00 |
| Şiddetli | −250 ≤ SYM-H < −150 | 14 | 13,75 | 31,00 |
| Aşırı | SYM-H < −250 | 7 | 9,50 | 22,50 |

- Süreler −50° ≤ MLAT ≤ 50° ortalaması için (Şekil 3).
- Makalenin notu: "This definition of storm intensity intervals is arbitrary."
- Şiddetli sınıfta, toparlanma evresinde ikinci fırtına olan iki olay dışlanmış.
- Zayıf sınıfın 61,75 saati Şekil 4'teki noktayla (yaklaşık 44 sa, şekilden okuma) uyuşmuyor görünüyor.

**Etki.** Fırtınaların %41'i (90/217) "zayıf": SYM-H −50 nT'ye bile inmiyor. Bu olaylarda sinyal küçük olacak; birincil testin havuzunda ağırlıkları büyük. Güç hesabını yaparken bunu gör; şiddet sınıfına göre tabakalı raporlama zorunlu.

## Doğrulama seti: yedi aşırı fırtına

Zesta ve Oliveira 2019 Tablo 2 `[OKUNDU]`. Yayınlanmış tek başlangıç zamanları bunlar.

| Tarih | Başlangıç (UT) | En düşük Bz (nT) | En düşük SYM-H (nT) |
| --- | --- | --- | --- |
| 6 Kas 2001 | 02:05 | −78,97 | −320 |
| 29 Eki 2003 | 07:04 | −62,09 | −390 |
| 30 Eki 2003 | 20:13 | −35,99 | −432 |
| 20 Kas 2003 | 11:24 | −52,97 | −490 |
| 7 Kas 2004 | 20:14 | −50,49 | −394 |
| 9 Kas 2004 | 19:25 | −34,14 | −282 |
| 15 May 2005 | 06:01 | −46,58 | −305 |

Not (sonradan eklendi): 15 May 2005 olayı CHAMP veri boşluğunun (1 Mar - 6 Tem 2005) içinde; CHAMP için kullanılamaz, GRACE-A'da var. Epok kuralının doğrulaması OMNI'ye dayandığı için bundan etkilenmez. Pilot "yalnız CHAMP" ise aşırı sınıftan seçilebilecek olay sayısı 6'ya iner.

Ek kıyas: 24 Ağu 2005, çarpma 06:13 UT, Bz dönüşü bildiride 09:09, Space Weather ön baskısında 09:15. Aynı ekip aynı olayda 6 dakika ayrışıyor; elle seçimin belirsizliği bu mertebede.

**Uyarı (sonradan eklendi, ölçüldü):** bu tablodaki 29 ve 30 Eki 2003 başlangıçları OMNI ile doğrulanamaz; o anlarda OMNI'de IMF verisi yok (bkz. `02`). Yazarların başka bir kaynak kullandığı anlaşılıyor (çıkarım). Kuralın OMNI'yle sınanabileceği olay sayısı en fazla 5 aşırı fırtına + 24 Ağu 2005; onların OMNI kapsamı da henüz bilinmiyor.

Kuralın kodu yazıldı: `space_environment.storms.onset.find_southward_turning`. Üç sonuç ayırıyor (bulundu / dönüş yok / veri yetersiz); 29 Eki 2003 için "veri yetersiz" döndürüyor. Parametreler henüz ayarlanmadı.

## Otomatik sıfır epok kuralı (öneri)

Kaynaktan gelmiyor; pilotta sabitlenecek ve teze yazılacak.

1. Tohum: Richardson-Cane (a) sütunundaki zaman, `t_a`.
2. OMNI 1 dakikalık Bz (GSM) serisinde `[t_a − 1 sa, t_a + 12 sa]` aralığında ara.
3. Aday: Bz'nin negatife geçtiği ve sonraki `T` dakikanın en az `%p`'sinde negatif kaldığı, ortalaması `−B0` nT'nin altında olan ilk an. Başlangıç değerleri: `T = 30`, `p = 80`, `B0 = 3`.
4. Aday yoksa (kuzeye yönelimli ICME) olayı "Bz dönüşü yok" diye işaretle; zayıf sınıfın önemli kısmı buraya düşebilir. Bu olaylar için yedek epok `t_a`.
5. OMNI boşluğu aday pencerenin %20'sinden fazlaysa olayı "epok belirsiz" diye işaretle.
6. Parametreleri yalnız yukarıdaki sekiz olayla ayarla. Kabul ölçütü: sekizinin de ±15 dakika içinde tutması. Tutmayanları raporla, kuralı olaya özel eğme.

İkinci epok olarak `t_a` (şok/SSC) da saklanır; JGR 2017 özeti iki epoku birlikte kullandığını söylüyor.

Duyarlılık: ana sonuç, epok ±30 dakika kaydırılarak yeniden hesaplanır. Öznitelikler mutlak zamanla kurulduğu için tahmin modelleri epoka doğrudan bağlı değil; epok yalnız pencereyi, yanlılık terimini ve ayrıştırmaları belirler.

## Epok kuralı: yayınlanmış zamanlarla karşılaştırma (6 Eki 2026, ölçüldü)

Betik ve çıktı: `kanit/epok_kurali_ayar.py`, `kanit/epok_kurali_ayar_cikti_2026-10-06.txt`. Veri: OMNI 1 dakikalık aylık dosyalar (Kas 2001, Kas 2003, Kas 2004, May 2005, Ağu 2005), tohum Richardson-Cane (a) sütunu.

**Kural 1 (ilk sürekli güneye dönüş; yukarıdaki öneri)** yazarların seçimini tutturmuyor: 20 Kas 2003'te 4,4 saat, 24 Ağu 2005'te 2,9 saat erken. Yazarlar zayıf güneye sapmaları değil, derin güney aralığına giden **keskin** dönüşü seçmiş.

**Kural 2 (`find_main_phase_onset`)**: pencerede Bz'nin en düşük değerinin %70'ine ilk ulaşıldığı andan geriye, negatif örnekler boyunca (10 dakikaya kadar boşluk köprülenir, kuzey örnek köprülenmez) yürü; son negatif olmayan örnekten sonraki ilk negatif örnek başlangıçtır.

| Olay | Tohum (R&C) | Yayınlanan | Kural 2 | Fark |
| --- | --- | --- | --- | --- |
| 6 Kas 2001 | 01:52 | 02:05 | — | veri yetersiz (pencere kapsamı %20; **OMNI'de yayınlanan an boşlukta**) |
| 20 Kas 2003 | 08:03 | 11:24 | 11:31 | +7 dk |
| 7 Kas 2004 | 18:27 | 20:14 | 20:14 | 0 |
| 9 Kas 2004 | 18:25 | 19:25 | 19:26 | +1 dk |
| 15 May 2005 | 02:38 | 06:01 | 05:54 | −7 dk |
| 24 Ağu 2005 | 06:13 | 09:09 | 09:10 | +1 dk |

- Beş sınanabilir olayın beşi 7 dakika içinde; yazarların kendi iki makalesi arasındaki 6 dakikalık fark mertebesinde.
- Göreli derinlik parametresi bu beş olayda seçildi (0,5'te bir olay 43 dk, 1,0'da bir olay 164 dk sapıyor). **Bu bir ayarlamadır, doğrulama değil.** Bağımsız doğrulama için katalog kurulduğunda zayıf/orta sınıftan rastgele 10 olay elle incelenip kuralla karşılaştırılmalı; sonucu teze yaz.
- **Yedi aşırı fırtınanın üçünde (6 Kas 2001, 29 ve 30 Eki 2003) OMNI'de başlangıç anı boş.** Yazarların doğrudan uydu verisi (ACE) kullandığı anlaşılıyor (çıkarım). Bu olaylar için ya ACE manyetik alan verisi alınır ya da yayınlanan zaman elle girilir ve işaretlenir.
- Kural, pencere kapsamı %80'in altındaysa "veri yetersiz" döndürür; 29 Eki 2003 için 6 saatlik pencerede de böyle davranıyor (test).

Bir sonraki karar: kural 2 varsayılan epok olur; kural 1 ve Richardson-Cane şok zamanı duyarlılık epokları olarak saklanır.

## Katalog kurma adımları

1. `icmetable2.xlsx` indir (82,5 kB), özetini ve sürümünü (5.1) kaydet.
2. 2001-05-01 ile 2015-12-31 arası satırları al (beklenen: 334 civarı; farklıysa dur, nedenini bul).
3. Her satır için OMNI'den en düşük SYM-H'yi `[t_a, ICME bitişi + 24 sa]` aralığında hesapla; sınıf ata. Katalogdaki Dst sütununu yalnız çapraz kontrol için tut.
4. Sıfır epok kuralını uygula.
5. Pencere: epoktan 24 saat önce, 72 saat sonra (ana plan). Kıyas için bilgi: bildiri −24/+96, GRL 2019 −12/+72 kullanmış.
6. Örtüşen pencereleri tek kümede birleştir; küme kimliği çapraz doğrulamadaki grup olur.
7. Uydu verisi kapsamı: pencerede geçerli yoğunluk oranı eşiğin altındaysa o uydu için olayı at (eşik pilotta).
8. Çıktı: `katalog.parquet` (olay kimliği, küme kimliği, `t_a`, epok, epok bayrağı, en düşük SYM-H, sınıf, ICME sınırları, uydu kapsamı) ve sınıf başına sayım tablosu.
9. Karşılaştır: sınıf sayıları 90/78/28/14/7 ile ne kadar örtüşüyor? Fark beklenir; büyüklüğünü ve olası nedenini (katalog sürümü, eleme kuralı) raporla.

**Durum (6 Eki 2026, yazıldı ve ölçüldü; `storms/catalog.py`, `kanit/space_environment_genisletme_cikti_2026-10-06.txt`):**

- Adım 1-2: xlsx okuyucu 644 olay okuyor; 2001-2015'te **tam 334** (beklenen "334 civarı" tuttu). Hücrelerdeki ek harfler (`S`, `P`, `Q`, `H`, `W`, `(A)`) atılmıyor, `*_note` alanlarında duruyor; anlamları katalog sayfasından henüz okunmadı. Bir satırda (309, 14 Oca 2007) rahatsızlık ICME başlangıcından sonra; kabul ediliyor.
- Adım 3: en düşük SYM-H penceresi `[t_a, ICME bitişi + 24 sa]`, **ama bir sonraki olayın rahatsızlık anında kesiliyor**. Kesilmeden 28 Ekim 2003 olayı 29 Ekim'in, 29 Ekim olayı 30 Ekim'in minimumunu alıyordu. Kesilince: 28 Eki → −58 nT (orta; R&C Dst −32), 29 Eki → −391 nT 30 Eki 01:48 (aşırı; R&C Dst −353). SYM-H kapsamı %80'in altındaysa minimum ve sınıf boş bırakılıyor.
- Adım 4: kural 2 uygulanıyor; 28 Eki için rahatsızlıktan 18 dk sonra, 29-30 Eki için "veri yetersiz".
- Adım 6: küme kuralı = pencereler örtüşüyor ya da arası 24 saatten azsa aynı küme (28-30 Ekim tek küme; 20 Kasım ayrı).
- Ek sütunlar: ilk 24 saatte Bz, hız, yoğunluk kapsam oranları (29 Eki: %21; 30 Eki: %0).
- Adım 5, 7, 8, 9 yıllık OMNI ve yoğunluk verisi gelince.

**Kararlar (danışmana sorulacak):**

- [ ] Yazarlardan (D. Oliveira, E. Zesta) 217'lik listeyi istemek. Kısa bir e-posta; yanıt gelirse hafta 2 yükünün yarısı kalkar ve hat doğrulaması birebir olur.
- [ ] JGR 2017 ek dosyasına üniversite erişimiyle bak.
- [ ] Zayıf sınıfı (90 olay) birincil teste almak ya da ayrı tutmak. Ön kayıt belgesine yazılmalı.

## Bildiri ile doğrulama adımında kullanılacak ayrıntılar `[OKUNDU]`

- Koordinat: MLAT ve MLT; hangi manyetik sistem olduğu yazmıyor.
- Kutu: üst üste bindirme grafiğinde 3° × 1,5 saat (bir yörünge); örnek olayda 5° × 5 dakika. GRL 2019: 3° × 15 dakika.
- Bantlar: yüksek enlem yaklaşık ±63°-±90°; orta enlem ±30°-60°; ekvator için sayı verilmemiş.
- Beklenen şekil: yüksek enlem ilk 1,5 saatte; "within t = 3.0 hours, perturbations reach the equatorial regions"; yüksek enlem en yoğun dördüncü yörüngede (6 sa); orta/alçak enlemde soğuma yaklaşık 21. saatte; ortalama en düşük SYM-H −42 nT, başlangıçtan yaklaşık 12 saat sonra.
- 2019 normalizasyonu: sakin aralıklar |SYM-H| < 30 nT; ρ_gözlem/ρ_JB08 oranına 15. dereceden polinom uydurulup uydu başına düzeltme çarpanı üretilmiş.
