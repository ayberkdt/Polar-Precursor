# results/ — koşu çıktıları

Her koşu kendi klasörüne yazar: `results/<yapilandirma>_<YYYYMMDD>/`. Klasör
`.gitignore` ile dışarıdadır; yalnız bu README depodadır. Git'e girecek olan,
kanıt niteliğindeki özet metinlerdir ve onlar `plans/kanit/` altına kopyalanır
(örnek: `plans/kanit/iskelet_testi_cikti_2026-10-06.txt`).

Bir koşu klasörünün içeriği:

| Dosya | Üreten | İçerik |
| --- | --- | --- |
| `manifest.json` | `polar_precursor.experiment.manifest.build_manifest` | git commit (+dirty), yapılandırma ve SHA-256 özeti, Python/numpy/pandas sürümleri, kullanılan veri dosyalarının SHA-256'ları, tohumlar |
| `design.parquet` | `polar_precursor.design.build_design` | tasarım matrisi: örnek başına hedef, girdiler, grup, sınıf, öngörü süresi kutusu |
| `predictions.parquet` | `polar_precursor.validation.cross_validate` | fırtına dışı kat tahminleri, model başına sütun; kat kimliği |
| `per_storm.csv` | `polar_precursor.metrics.per_storm_losses` | fırtına × model MSE tablosu, örnek sayısı, sınıf |
| `scores.csv` | `polar_precursor.metrics.report_table` | model × öngörü kutusu × sınıf: artık ortalaması/SD, RMSE, korelasyon, beceri |
| `peaks.csv` | `polar_precursor.metrics.peak_errors` | fırtına başına tepe genliği ve zamanlama hatası |
| `primary.txt` | `ExperimentResult.primary_line` | tek satır: göreli RMSE azalması, %95 aralık, permütasyon p, G |

Yeniden üretme kuralı: aynı `manifest.json` içindeki commit'e dönüp aynı
yapılandırma dosyasıyla koşmak aynı sayıları vermelidir (tohumlar
yapılandırmada; bootstrap ve permütasyon `numpy.random.default_rng(seed)`).
Sayı değişiyorsa önce `config_digest` ve veri özetleri karşılaştırılır.

Pilot (`configs/pilot.toml`) sonrası yalnız ön kayıt belgesinin 9. maddesi
("en küçük anlamlı etki") yazılır; başka hiçbir ayar değişmez (`plans/07`).
