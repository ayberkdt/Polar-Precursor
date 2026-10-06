# 07 — İstatistik tasarım, pilot ve dur/devam kapısı

Hazırlanma: 5 Ekim 2026. Ana plan: `../00_ana_plan.md`, "İstatistik tasarım" ve "Dur/devam kapısı". Bu belge ana plandaki tasarımı yinelemez; bu oturumdaki bulguların tasarıma etkisini ve uygulanacak adımları yazar. İstatistik kaynakları (Cameron ve Miller, Clark ve West, Cawley ve Talbot) bu oturumda yeniden açılmadı; ana plandaki atıflar geçerli sayıldı, doğrulanmadı.

## Bulguların tasarıma etkisi

| Bulgu | Kaynak | Tasarımda değişen |
| --- | --- | --- |
| 217 fırtınanın 90'ı "zayıf" (SYM-H ≥ −50 nT) | `05` | Birincil havuzda fırtınaların %41'i küçük sinyalli. Birincil ölçüt fırtına başına eşit ağırlıklı olursa sonuç zayıf fırtınalarca belirlenir. **Karar gerekli** (aşağıda) |
| Uydu başına kapsam farklı; GRACE 2011 sonrası yılda 55-105 gün eksik | `01` | Etkin fırtına sayısı 217'nin altında olacak. Güç tablosunu gerçek sayıyla yeniden hesapla |
| H3'ün yönü literatürde tartışmalı (Liu: süper fırtınada kısa gecikme; Wang 2020: büyük fırtınada uzun) | `06` | H3'ü tek yönlü yazma; iki yönlü test, gerekçesiyle |
| Kendi geçmişini girdi yapan bir model yayınlanmış (Zhang 2026) | `09` | H4 "ilk gösterim" değil; "fırtına gruplu doğrulamayla 1-4 saatte ne kadar" diye yazılır. Kapıdaki "H4 güçlü → devam" kolunun yenilik değeri düştü |
| Gerçek zamanlı SYM-H yok | `02` | A katmanında SYM-H yerine ap30 + saatlik Dst (öneri). B3'ün gücünü ve dolayısıyla M'nin kazancını etkiler; ön kayıtta sabitle |
| CHAMP 2005'te 230 gün veri | `01` | Pilot "yalnız CHAMP 2002-2005" tanımı: 2005 fırtınalarının kapsamını önce ölç |
| Sıfır epok elle seçilmiş; aynı olayda 6 dk ayrışma | `05` | Epok duyarlılık testi (±30 dk) ikincil analizlere eklendi |
| "ap = 4" ile anahtar kapatma özdeş | `03` | Referans modeli için duyarlılık koşusu gereksiz; bir satır azaldı |
| Liu 2010 modeli tek fırtınada gösterilmiş | `06` | D basamağının yanına yayınlanmış taban olarak eklenir |

**Sonradan eklenen satır (ölçüldü):** OMNI'de en büyük iki fırtınanın ana evresinde güneş rüzgarı verisi yok (`02`). Birincil test "sürücü kapsamı yeterli" örneklerle sınırlanırsa aşırı sınıf fiilen düşer. Ön kayıtta karar verilmeli: sürücüsüz örnekler birincil testte mi (sürücüsüz B3 türeviyle), ayrı bir ikincil analizde mi. Öneri: ayrı ikincil analiz; birincil test temiz kalsın.

## Ön kayıt belgesinde sabitlenecek kararlar

Danışmana gönderilecek tek sayfanın maddeleri. Her biri için bu belgede bir öneri var; karar senin.

1. **Fırtına kümesi.** Richardson-Cane sürüm 5.1 (30 Tem 2026), 2001-05-01 - 2015-12-31, uydu kapsamı eşiğini geçenler. Öneri: tüm sınıflar katalogda, **birincil test en düşük SYM-H < −50 nT olanlarda** (orta ve üstü; kaynakta 127 olay), zayıf sınıf ikincil. Gerekçe: zayıf olaylarda ne kutup ne alçak enlem anlamlı bir fırtına tepkisi veriyor (zayıf sınıfın "en yükseğe süre" değeri 61,75 sa: belirgin bir tepe yok); onları birincil havuza koymak etkiyi seyreltir. Karşı görüş: eşiği sonuçtan önce koymazsan seçim yanlılığı olur; o yüzden şimdi yazılmalı.
2. **Ağırlık.** Fırtına başına tek `d_s`, eşit ağırlık (ana plan). Alternatif: fırtına başına örnek sayısıyla ağırlık. Öneri: eşit ağırlık birincil.
3. **Uydular.** Öneri: CHAMP ve GRACE-A; GRACE-B yok; GRACE-A 2007-2009 birincil testin dışında.
4. **Öngörü süresi havuzu.** 60-270 dk (bkz. `04`); +60 dakikadan kısa hedefler dışarıda.
5. **A katmanı.** SYM-H yok; ap30, saatlik Dst (bkz. `02`).
6. **Referans.** NRLMSIS 2.1, ap = 4, gözlenen F10.7.
7. **Birincil ölçüt.** `d_s = MSE_B3,s − MSE_M,s`; göreli RMSE azalması; küme bootstrap %95 aralığı, 10.000 yineleme, tohum yazılı.
8. **Doğrulayıcı test.** Kutup girdi bloğunu fırtınalar arasında, şiddet sınıfı ve öngörü süresi kutusu içinde karıştır; 1000 permütasyon; her birinde M yeniden uydurulur.
9. **En küçük anlamlı etki.** Pilottan sonra, ana analizden önce yazılacak.
10. **Model sınıfı.** Ridge birincil. Ceza katsayısı iç döngüde, fırtına gruplu.
11. **Hipotez yönleri.** H1 tek yönlü (M daha iyi); H2 "kazanç 105-195 dk kutularında en yüksek"; H3 iki yönlü; H4 tek yönlü.

## Çapraz doğrulama iskeleti

- Grup: fırtına kümesi kimliği (`05`, adım 6). Aynı kümenin iki uydusu aynı grupta.
- Dış döngü: `GroupKFold`, 10 kat. Katları yıla göre dengeleme: güneş çevrimi evresi kata sızmasın diye katları rastgele değil, fırtınaları epok sırasına dizip dönüşümlü ata (öneri).
- Tampon: iki grubun pencereleri arasında 57 saatten az varsa aynı kümede birleştirilmiş olmalı; iskelette doğrulama olarak denetle.
- İç döngü: 5 kat, yine gruplu; yalnız ceza katsayısı.
- Ölçekleme ve eksik değer doldurma her katın eğitim kısmında uydurulur.
- Çıktı: örnek başına her modelin dış kat tahmini; fırtına başına MSE tablosu.

**İskelet testi (hafta 4).** Sentetik veriyle iki sınama:

1. Kutup girdisi hedeften bağımsız üretildiğinde bootstrap aralığı sıfırı içermeli; 200 tekrarın en fazla %5'inde dışlamalı (yanlış pozitif oranı).
2. Hedefe bilinen büyüklükte kutup katkısı eklendiğinde kazanç geri bulunmalı.

Bu sınama geçmeden gerçek veride birincil test koşulmaz.

## Güç

Ana plandaki bağıntı: saptanabilir ortalama fark ≈ 2,8 × SD / √G. Fırtına sayısına göre (hesap):

| G | Saptanabilir fark |
| --- | --- |
| 30 (pilot) | 0,51 SD |
| 100 | 0,28 SD |
| 127 (orta ve üstü, kapsam kaybı öncesi) | 0,25 SD |
| 150 | 0,23 SD |
| 200 | 0,20 SD |

Gerçek G, katalog ve kapsam raporundan sonra belli olacak (hafta 2 sonu). SD pilottan.

## Pilot

Ana plan: 30 fırtına, şiddet sınıflarına orantılı, yalnız CHAMP, 2002-2005.

Öneriler:

- **Orantılı yerine tabakalı.** Orantılı seçimde 30'un 12'si zayıf, 1'i aşırı olur. SD'yi sınıf başına görmek için: zayıf 6, orta 10, güçlü 8, şiddetli 4, aşırı 2. Tohum yazılı.
- Dönem 2001-05 - 2005-12 (CHAMP 2001'de de var; 355 gün). 2005 fırtınaları için önce kapsam.
- Pilot fırtınaları ana analizde kalır (ana plan); pilottan sonra yalnız ön kayıttaki 9. madde yazılır, başka hiçbir şey değişmez.

**Hat doğrulaması (kapıdan önce).** Üst üste bindirilmiş epok: 3° QD enlem × 90 dk kutular, `log10(ρ410/ρ_sakin,410)`. Beklenen (bildiriden): yüksek enlem ilk kutuda; ekvator 3 saat içinde; yüksek enlem tepe yaklaşık 6. saatte; soğuma yaklaşık 21. saatte. Aşırı fırtınalar için ayrıca: ekvator yaklaşık 1,5 saatte.

Kabul ölçütü (öneri, nitel): yukarıdaki dört zamanlamadan en az üçü ±1 kutu içinde. Sayısal eşleşme beklenmez (farklı yoğunluk ürünü, farklı referans model, farklı fırtına kümesi).

## Kapı

Ana plandaki karar tablosu geçerli. Ekler:

- "Kazanç %1'in altında, H4 güçlü → devam, ağırlık kayar" kolu için: Zhang 2026 tam metni okunmuş olmalı. Aynı şeyi yapıyorsa bu kol "dur"a yaklaşır; danışmanla konuş.
- Kapı raporuna eklenecekler: fırtına başına `d_s` dağılımı (sınıfa göre), kısmi korelasyon (öngörü süresi kutusu başına), B3t'nin iki tanımıyla sonuç, Liu-2010 tabanının puanı.
- Kapı tarihi 7 Şubat 2027.

## Raporlama şablonu

Her model × öngörü süresi kutusu × sınıf için: log-oran artığının ortalaması ve standart sapması; RMSE; korelasyon; kalıcılığa ve B3'e göre beceri puanı. Fırtına başına: tepe genliği hatası, tepe zamanlama hatası. Birincil sonuç tek satır: göreli RMSE azalması, %95 aralık, permütasyon p değeri, G.

## Açık noktalar

- [ ] Ön kayıt belgesinin yazımı (Ocak öncesi).
- [ ] İstatistik kaynaklarının (özellikle az kümeli bootstrap ve iç içe model testi) tam metinden teyidi.
- [ ] Gerçek G (hafta 2 sonu).
