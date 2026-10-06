"""Deney aşamasını hazır bir tasarım matrisi üzerinde yeniden koş (veri seti kurmadan).

    PYTHONPATH=src .venv/Scripts/python.exe scripts/deney_tekrar.py results/pilot_20261006
        [--no-permutation]

Girdi klasöründeki design.parquet ve configs/pilot.toml ile run_experiment + gate_report
çalışır; çıktı <girdi>_deney_<HHMM>/ klasörüne yazılır (eski koşunun üstüne yazılmaz).
Kullanım yeri: model/merdiven kodunda değişiklik sonrası aynı veriyle karşılaştırma.
"""

from __future__ import annotations

import shutil
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

from polar_precursor.config import load_config
from polar_precursor.experiment.manifest import build_manifest, write_manifest
from polar_precursor.experiment.pipeline import run_experiment
from polar_precursor.experiment.report import gate_report

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str]) -> int:
    with_permutation = "--no-permutation" not in argv
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__)
        return 2
    source = Path(args[0])
    if not source.is_absolute():
        source = ROOT / source
    design = pd.read_parquet(source / "design.parquet")
    config = load_config(ROOT / "configs/pilot.toml")
    out = source.parent / f"{source.name}_deney_{datetime.now():%H%M}"
    out.mkdir(parents=True, exist_ok=True)
    groups = design["group"].nunique()
    print(f"tasarım {source.name}: {len(design)} satır, {groups} küme; çıktı {out}")
    result = run_experiment(design, config, with_permutation=with_permutation)
    result.cv.predictions.assign(fold=result.cv.fold).to_parquet(
        out / "predictions.parquet", index=False
    )
    result.per_storm.to_csv(out / "per_storm.csv")
    result.scores.to_csv(out / "scores.csv", index=False)
    result.peaks.to_csv(out / "peaks.csv")
    (out / "primary.txt").write_text(result.primary_line() + "\n", encoding="utf-8")
    report = gate_report(result, design, title=f"Gate report, rerun on {source.name}")
    (out / "report.md").write_text(report, encoding="utf-8")
    shutil.copy(source / "design.parquet", out / "design.parquet")
    for name in ("coverage.csv", "storms.csv", "clusters.csv"):
        if (source / name).exists():
            shutil.copy(source / name, out / name)
    manifest = build_manifest(
        config,
        root=ROOT,
        data_files=[source / "design.parquet"],
        extra={"rerun_of": str(source), "rows": int(len(design))},
    )
    write_manifest(out / "manifest.json", manifest)
    print(result.primary_line())
    print(f"rapor: {out / 'report.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
