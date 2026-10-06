"""Skeleton test on synthetic storms (plan 07): the chain must pass before real data.

Two checks, both from plan 07 "İskelet testi":

1. **False positive rate.** With the polar block independent of the target
   (``polar_gain = 0``), the primary test must not declare M better than B3:
   the bootstrap interval must not lie entirely above zero in more than 5 % of
   ``n_repeats`` repetitions (H1 is one-sided, plan 07 decision 11).
2. **Recovery.** With a known polar contribution (``polar_gain > 0``) the
   candidate must beat the reference: the interval must lie above zero in
   most repetitions and the mean point estimate must be positive.

Measured on 6 Oct 2026 (``plans/kanit/iskelet_testi_cikti_2026-10-06.txt``):
under the null the interval excludes zero only on the *negative* side (M is
slightly worse than B3 because it estimates eight coefficients that are truly
zero; the nested-model penalty of Clark and West that the main plan
anticipates). The one-sided reading above is therefore the right criterion;
the two-sided exclusion rate is still reported for the record.

Run as ``python -m polar_precursor.experiment.skeleton`` to write the evidence
file; the unit test runs a small version.
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from polar_precursor.config import ExperimentConfig
from polar_precursor.experiment.pipeline import run_experiment
from polar_precursor.synthetic import SyntheticConfig, synthetic_design


@dataclass(frozen=True, slots=True)
class SkeletonResult:
    polar_gain: float
    n_repeats: int
    seed: int
    point_estimates: np.ndarray
    ci_low: np.ndarray
    ci_high: np.ndarray
    seconds: float

    @property
    def fraction_excluding_zero(self) -> float:
        """Two-sided: interval entirely above or entirely below zero."""
        return float(np.mean((self.ci_low > 0.0) | (self.ci_high < 0.0)))

    @property
    def fraction_positive_significant(self) -> float:
        """One-sided, the H1 direction: interval entirely above zero (M better)."""
        return float(np.mean(self.ci_low > 0.0))

    @property
    def fraction_negative_significant(self) -> float:
        """Interval entirely below zero (M worse than B3)."""
        return float(np.mean(self.ci_high < 0.0))

    def line(self) -> str:
        return (
            f"polar_gain {self.polar_gain:g}: {self.n_repeats} repeats, seed {self.seed}; "
            f"point estimate mean {100 * self.point_estimates.mean():+.2f}% "
            f"(SD {100 * self.point_estimates.std(ddof=1):.2f}%, min "
            f"{100 * self.point_estimates.min():+.2f}%, max "
            f"{100 * self.point_estimates.max():+.2f}%); CI above 0 (M better) in "
            f"{100 * self.fraction_positive_significant:.1f}%, below 0 (M worse) in "
            f"{100 * self.fraction_negative_significant:.1f}%; {self.seconds:.1f} s"
        )


def repeat_skeleton(
    config: ExperimentConfig,
    synthetic: SyntheticConfig,
    *,
    n_repeats: int,
    seed: int,
    bootstrap_resamples: int = 2_000,
) -> SkeletonResult:
    """Run the pipeline (without permutation) on ``n_repeats`` synthetic draws."""
    points = np.empty(n_repeats)
    low = np.empty(n_repeats)
    high = np.empty(n_repeats)
    started = time.perf_counter()
    for i in range(n_repeats):
        design = synthetic_design(synthetic, seed=seed + i)
        result = run_experiment(
            design, config, with_permutation=False, bootstrap_resamples=bootstrap_resamples
        )
        points[i] = result.bootstrap.relative_rmse_reduction
        low[i] = result.bootstrap.ci_low
        high[i] = result.bootstrap.ci_high
    return SkeletonResult(
        synthetic.polar_gain, n_repeats, seed, points, low, high, time.perf_counter() - started
    )


def skeleton_passes(
    null: SkeletonResult,
    signal: SkeletonResult,
    *,
    max_false_positive: float = 0.05,
    min_recovery: float = 0.8,
) -> tuple[bool, str]:
    """Verdict and a one-line report; false positives are counted in the H1 direction."""
    false_positive = null.fraction_positive_significant
    checks = [
        (
            false_positive <= max_false_positive,
            f"false positive rate (CI above 0 under the null) {100 * false_positive:.1f}% "
            f"<= {100 * max_false_positive:.0f}%",
        ),
        (
            signal.fraction_positive_significant >= min_recovery,
            f"recovery {100 * signal.fraction_positive_significant:.1f}% "
            f">= {100 * min_recovery:.0f}%",
        ),
        (signal.point_estimates.mean() > 0.0, "mean recovered gain positive"),
    ]
    verdict = all(ok for ok, _ in checks)
    report = "; ".join(("PASS " if ok else "FAIL ") + text for ok, text in checks)
    return verdict, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--repeats", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20270207)
    parser.add_argument("--polar-gain", type=float, default=0.3)
    parser.add_argument("--storms", type=int, default=30)
    parser.add_argument("--samples", type=int, default=40)
    parser.add_argument("--bootstrap", type=int, default=2_000)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    config = ExperimentConfig(
        name="skeleton", ladder=("B0", "B1", "B2", "D", "B3", "B3k", "B3t", "M")
    )
    base = SyntheticConfig(n_storms=args.storms, samples_per_storm=args.samples)
    null = repeat_skeleton(
        config,
        replace(base, polar_gain=0.0),
        n_repeats=args.repeats,
        seed=args.seed,
        bootstrap_resamples=args.bootstrap,
    )
    signal = repeat_skeleton(
        config,
        replace(base, polar_gain=args.polar_gain),
        n_repeats=args.repeats,
        seed=args.seed,
        bootstrap_resamples=args.bootstrap,
    )
    verdict, report = skeleton_passes(null, signal)
    lines = [
        f"skeleton test: {args.storms} storms x {args.samples} samples, ladder {config.ladder}",
        f"cv outer {config.cv.outer_folds} inner {config.cv.inner_folds}, "
        f"alphas {config.ridge.alphas}, bootstrap {args.bootstrap} resamples per repeat",
        f"synthetic: {base}",
        "null:   " + null.line(),
        "signal: " + signal.line(),
        ("PASS" if verdict else "FAIL") + ": " + report,
    ]
    text = "\n".join(lines)
    print(text)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    return 0 if verdict else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


__all__ = ["SkeletonResult", "main", "repeat_skeleton", "skeleton_passes"]
