# Polar Precursor — Durum Raporu

Tarih: 6 Ekim 2026, gece güncellemesi. Depo: https://github.com/ayberkdt/Polar-Precursor (son commit `614f2f7`).
Her sayının kaynağı `plans/kanit/` altındaki çıktı dosyalarıdır; aşağıda ilgili dosya adı parantezde verilir.

## 1. Tezin sorusu

Yüksek enlem (kutup) termosfer yoğunluğu, alçak enlem yoğunluğunu 1-4 saat önceden kestirmeye, güneş rüzgarı sürücülerinin ve uydunun kendi geçmişinin ötesinde katkı veriyor mu? Veri: CHAMP ve GRACE ivmeölçer yoğunlukları, 2001-2015 CME fırtınaları.

## 2. Bugüne kadar yapılanlar

### 2.1 Altyapı: `space_environment` paketi (Sidera'ya taşınacak)

- Okuyucular: GFZ Kp/ap/F10.7 ve Hp30; OMNI 1 dk ve 5 dk; Kyoto Dst ve ACE (HAPI); SET JB2008 indeksleri; Zenodo ısıtma/ΔT; SILSO; ESA/TU Delft CDF yoğunluk. Hepsi gerçek veri kesitleriyle test ediliyor.
- Fizik kuralları: NRLMSIS indeks kuralları ve sakin/ölçülen sağlayıcılar, JB2008 girdi gecikmeleri (pyatmos ile birebir doğrulandı), bağlaşım fonksiyonları, hafıza integrali, şok ve fırtına başlangıç kuralları, L1 gecikmesi (ACE ile ölçüldü), QD manyetik koordinatlar (apexpy).
- Analiz: Richardson-Cane kataloğundan fırtına tablosu (SYM-H sınıfı, pencere, küme), sürücü/indeks/geometri öznitelikleri, geçiş bölütleme ve (kutup geçişi, hedef) örnek kurucu, sızıntı denetimi.
- Referans yoğunluk: NRLMSIS 2.1, Ap = 4 tüm yuvalarda, pymsis ile vektörel; ağ erişimi yok. 10 s üründe 60 s düğümle içdeğerleme hatası en çok 0,0015 (`uctan_uca_2003_10_29_cikti.txt`).

### 2.2 Deney katmanı: `polar_precursor` paketi (tezde kalır)

- Model merdiveni B0 B1 B2 D B3 B3k B3t B3t2 M, kapalı biçim ridge; sütun sözleşmesi (sektöre göre alçak enlem gecikmeleri dahil); tasarım matrisi kurucu.
- Fırtına gruplu, epok sıralı, iç içe çapraz doğrulama; 57 saat tampon denetimi.
- Küme bootstrap (fırtına başına d_s, göreli RMSE azalması), sınıf × öngörü kutusu tabakalı permütasyon, öngörü kutusu başına Holm, H4 ve kontrol karşılaştırmaları, güç.
- Sentetik fırtına üreteci ve plan 07 iskelet testi: 200 tekrar, sıfır durumunda yanlış pozitif %0, bilinen katkı %100 geri bulundu (`iskelet_testi_cikti_2026-10-06.txt`). Bulgu: iç içe model cezası yüzünden bootstrap M aleyhine muhafazakâr; permütasyon bunu düzeltiyor.
- Fırtına penceresi veri seti kurucu (günlük CDF → tasarım, parquet önbellek, kapsam tablosu), kapı raporu üreteci, koşu kaydı (commit, yapılandırma özeti, veri SHA-256).
- Ön kayıt düğmeleri `configs/pilot.toml` (plan 07'nin önerileri; karar değil).

### 2.3 Depo

README, `uv.lock`, CI iş akışı (ruff, mypy, import-linter, pytest), `data/README.md`, `results/README.md`, 14 plan belgesi. Son kapı koşusu: 125 test geçti, tüm denetimler temiz (`space_environment_testler_2026-10-06l.txt`). Commit'ler Ayberk adıyla.

### 2.4 Veri (1. ve 2. kademe, 6 Ekim)

| Veri | Hacim | Doğrulama |
| --- | --- | --- |
| OMNI 1 dk 2001-2015 | 15 × 158 MB | her yıl kayıt sayısı tam, 2003 test kesitiyle bayt-birebir |
| CHAMP fırtına pencereleri 2001-2010 | 532 gün, 288 MB | 43 gün üründe yok (çoğu 2005 ve görev sonu), hata 0 |
| GRACE-A fırtına pencereleri 2002-2015 | 748 gün, 404 MB | 101 gün üründe yok (2002 başı ve 2011-2015 boşlukları), hata 0 |
| GFZ Hp30 tam seri, Kyoto Dst 2001-2005 | 45 MB | başlık ve satır sayısı doğrulandı |

Kayıt: `indirme_kaydi_2026-10-06.txt` (her dosyanın SHA-256'sı).

### 2.5 Fırtına kataloğu 2001-2015

334 ICME (Richardson-Cane + OMNI SYM-H): 2001-2005'te 148 (aşırı 10, şiddetli 14), 2006-2015'te 186 (aşırı 0, şiddetli 5, zayıf 102). Aşırı fırtınaların tamamı 23. çevrimde; 24. çevrim zayıf.

## 3. Pilot sonucu (CHAMP 2001-2005, 30 fırtına kümesi, 20 525 örnek)

Kaynak: `pilot_v3_sektorlu_rapor_2026-10-06.md`; yorum: `plans/14_pilot_2001_2005.md`.

| Karşılaştırma | Göreli RMSE azalması | %95 aralık | Anlam |
| --- | --- | --- | --- |
| M vs B3 (ana hipotez H1) | +6,0 % | +3,3 .. +9,9 | kutup geçişleri katkı veriyor; fırtınaların %90'ında iyileşme; permütasyon p = 0,001 |
| M vs B3t (tazelik kontrolü, geçişten önceki orta enlem) | +2,9 % | +0,8 .. +5,8 | eşik %3'ün kılpayı altında |
| M vs B3t2 (geçişten sonraki, daha taze orta enlem) | +3,6 % | +0,6 .. +7,3 | daha taze ölçüm daha az yararlı: tazelik tek başına açıklamıyor |
| M vs B3k (kahin sürücü) | +17 % | +1,6 .. +26 | tek aşırı fırtına katı belirliyor; ekstrapolasyon |
| B3 vs D (H4) | +56 % | +47 .. +60 | uydunun kendi geçmişi, yalnız sürücülerden çok daha değerli |

Merdiven sıralı: kalıcılık 0,1345 > B2 0,1288 > B3 0,1118 > B3t 0,1065 > M 0,1027 (RMSE, log-oran).

Öngörü kutusu başına (Holm düzeltmeli): 105-150 dk +8,7 %, 150-195 +6,8 %, 195-240 +7,7 %, 240-270 +4,1 % anlamlı; **60-105 dk anlamsız**. Kazanç 2-4 saat sonrasında, ilk saatte yok; kutuptan alçak enleme gecikmeyle tutarlı (H2).

Sınıf başına: kazanç aşırı ve şiddetli fırtınalarda en büyük, zayıf fırtınalarda sıfır.

Fırtınadan fırtınaya d_s SD'si 0,00192; ölçülen etki ≈ 0,68 SD. 30 fırtına 0,51 SD'yi, 150 fırtına 0,23 SD'yi saptar.

### Kapı okuması

Ana plan tablosu: M, B3'ü %3 eşiğinin üstünde geçiyor; B3t'yi anlamlı ama eşiğin kılpayı altında geçiyor. Sonuç: **devam; soru keskinleşiyor** ("kutba özgü mü, tazelik mi"). B3t'nin ikinci tanımı ana analizde şart.

### Statü

**Keşif.** Ön kayıt yazılmadan, tek uyduyla, 30 kümeyle, pilot tanımı yolda iki kez düzeltilerek (sektör sütunları; merdiven öneki) alındı. Tez iddiası değil; kapı kararı ve "en küçük anlamlı etki" girdisi. Pilot fırtınaları ana analizde havuzda kalır.

## 3b. Kapsam raporu (tüm veri, `kapsam_raporu_2026-10-06.md`)

197 benzersiz fırtına kümesi (2001-2015). Birincil havuz (küme sınıfı orta ve üstü): katalogda 119, en az bir uyduda örnekli **110**, iki uyduda birden 44. CHAMP 110 kümeden 104'ü örnekli (57 434 örnek), GRACE-A 197'den 160'ı (80 264 örnek). 110 fırtına 0,27 SD'yi saptar; pilot etkisi 0,68 SD. Dengesizlik: aşırı sınıfın tamamı ve şiddetlilerin çoğu 2001-2005'te; 2011-2015 zayıf ve orta ağırlıklı.

## 4. Yolda yakalanan hatalar

- İlk pilot koşusunda B2 kalıcılıktan kötüydü: doğrusal model "hedefle aynı sektördeki son geçiş"i seçemiyor; gündüz/gece farkı büyük. Sektöre göre gecikme sütunları eklendi.
- İkinci koşuda yeni sütunlar merdivene girmedi (önek hatası); üçüncü koşu düzeltilmiş.
- Küme sınıfı örneğin düştüğü ICME satırından alınıyordu; iki aşırı küme "orta/şiddetli" görünüyordu. Küme sınıfı = en şiddetli üye.
- OMNI 2003 indirmesinde iki süreç aynı dosyaya yazdı; silinip yeniden indirildi, kesitle doğrulandı.
- C: diski doldu; %TEMP% temizlendi (5 GB).
- Kapsam koşusunda (tüm veri) dört hata daha: CDF'de konumu eksik kayıtlar (referans artık düğüm dışı bırakıp içdeğerliyor); fırtına önbellek kimliğinin bloklar arasında çakışması (kimlik artık rahatsızlık zamanı; pilot etkilenmedi); **F10.7 radyo patlaması günleri** (2001-2015'te 12 gün, 938 sfu'ya kadar; NRLMSIS NaN veriyordu ve 81 günlük ortalamayı ≈5 sfu kaydırıyordu; tarama kuralı eklendi, pilot 1-4 taramasız koştu); bellek yetersizliği (başka oturumların süreçleri; betik blok başına ayrı sürece alındı).

## 5. Sırada

Senin kararın gereken:

1. **Ön kayıt belgesi**: taslak yazıldı (`plans/15_on_kayit_taslagi.md`, 17 madde, her birinde öneri ve ölçülmüş gerekçe); senin imzan bekleniyor. Sonra `configs/main.toml` üretilir ve kod etiketlenir.
2. ~~2. kademe veri~~ indi ve doğrulandı; ~~kapsam raporu~~ çıktı: birincil havuz (orta ve üstü) 110 fırtına kümesi örnekli, 138 bin örnek (`plans/kanit/kapsam_raporu_2026-10-06.md`). Kararın: uydu kapsam eşiği (%70 önerisi).
3. Lisans ve GitHub açıklaması.

Kod tarafında kalan: Liu-2010 taban puanı, gradient boosting basamağı (ikincil), epok duyarlılığı (±30 dk), sürücüsüz örnekler ikincil analizi, Sidera ortamında referans çapraz kontrolü. B3t ikinci tanımı yapıldı.

## 6. Takvim

Ana planın 13 haftalık takvimine göre bugün 3. haftanın kapısındayız; mühendislik tarafının kabaca üçte ikisi, bilimsel tarafın beşte biri tamam. Kapı tarihi planda 7 Şubat 2027; bu rapor itibarıyla kapı erken ve "devam" ile geçildi.
