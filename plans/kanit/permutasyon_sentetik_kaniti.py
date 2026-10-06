"""Permutasyon testinin sentetik veride davranisi (6 Eki 2026).
    PYTHONPATH=src .venv/Scripts/python.exe plans/kanit/permutasyon_sentetik_kaniti.py

Sorular: (1) Sifir durumunda (polar_gain = 0) p degeri buyuk mu; gozlenen istatistik
sifir dagiliminin icinde mi? (2) Bilinen katki (polar_gain = 0.3) varken p kucuk mu?
(3) Bootstrap'in sifir durumundaki eksi yanliligini (ic ice model cezasi) permutasyon
dagilimi da tasiyor mu (sifir dagiliminin ortalamasi eksi mi)? (4) Sure.
Iskelet testi (iskelet_testi_cikti_2026-10-06.txt) permutasyonu kapsamaz; bu betik tamamlar.
"""

from __future__ import annotations

import time
from dataclasses import replace

from polar_precursor.config import ExperimentConfig, PrimaryTest
from polar_precursor.experiment.pipeline import run_experiment
from polar_precursor.synthetic import SyntheticConfig, synthetic_design

config = ExperimentConfig(
    name="permutation-check",
    test=PrimaryTest(bootstrap_resamples=2_000, permutation_resamples=200),
)
base = SyntheticConfig(n_storms=30, samples_per_storm=40)
print(f"config: cv {config.cv}, ridge {config.ridge}, test {config.test}")
print(f"synthetic: {base}")
for gain in (0.0, 0.3):
    for seed in (1, 2, 3):
        started = time.perf_counter()
        design = synthetic_design(replace(base, polar_gain=gain), seed=seed)
        result = run_experiment(design, config, with_permutation=True)
        assert result.permutation is not None
        null = result.permutation.null
        print(
            f"polar_gain {gain:g} seed {seed}: {result.bootstrap.line()}\n"
            f"    {result.permutation.line()}; null min {100 * null.min():+.2f}% "
            f"max {100 * null.max():+.2f}%; alphas(M) {result.cv.alphas['M']}; "
            f"{time.perf_counter() - started:.0f} s"
        )
