"""End-to-end run on a design frame: ladder → grouped CV → scores → tests.

``run_experiment`` is the single entry point used by the pilot, the main
analysis and the synthetic skeleton. It refuses to run when the inter-group
buffer is violated (two storms closer than the longest feature memory must be
one cluster), and it returns every table the reporting template asks for.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from polar_precursor.config import ExperimentConfig
from polar_precursor.design.ladder import ladder
from polar_precursor.metrics.scores import peak_errors, per_storm_losses, report_table
from polar_precursor.statistics.bootstrap import BootstrapResult, cluster_bootstrap
from polar_precursor.statistics.permutation import PermutationResult, permutation_test
from polar_precursor.validation.crossval import CvResult, cross_validate
from polar_precursor.validation.folds import BufferViolation, check_group_buffer


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    config: ExperimentConfig
    cv: CvResult
    per_storm: pd.DataFrame
    scores: pd.DataFrame
    peaks: pd.DataFrame
    bootstrap: BootstrapResult
    permutation: PermutationResult | None
    buffer_violations: tuple[BufferViolation, ...]

    def primary_line(self) -> str:
        line = self.bootstrap.line()
        if self.permutation is not None:
            line += f"; {self.permutation.line()}"
        return line


def run_experiment(
    design: pd.DataFrame,
    config: ExperimentConfig,
    *,
    with_permutation: bool = True,
    allow_buffer_violations: bool = False,
    bootstrap_resamples: int | None = None,
    permutation_resamples: int | None = None,
) -> ExperimentResult:
    violations = tuple(check_group_buffer(design, buffer_h=config.cv.buffer_h))
    if violations and not allow_buffer_violations:
        first = violations[0]
        raise ValueError(
            f"{len(violations)} group pairs closer than {config.cv.buffer_h} h "
            f"(e.g. {first.earlier_group} → {first.later_group}: {first.gap_h:.1f} h); "
            "merge them into one cluster before running."
        )
    specs = ladder(config.ladder)
    cv = cross_validate(design, specs, config)
    per_storm = per_storm_losses(design, cv.predictions)
    scores = report_table(
        design,
        cv.predictions,
        reference=config.test.reference_model,
        persistence="B1" if "B1" in config.ladder else config.ladder[0],
    )
    peaks = peak_errors(design, cv.predictions, config.test.candidate_model)
    bootstrap = cluster_bootstrap(
        per_storm,
        reference=config.test.reference_model,
        candidate=config.test.candidate_model,
        n_resamples=config.test.bootstrap_resamples
        if bootstrap_resamples is None
        else bootstrap_resamples,
        seed=config.test.bootstrap_seed,
        confidence_level=config.test.confidence_level,
        weight=config.test.storm_weight,
    )
    permutation = (
        permutation_test(design, cv, config, n_resamples=permutation_resamples)
        if with_permutation
        else None
    )
    return ExperimentResult(
        config, cv, per_storm, scores, peaks, bootstrap, permutation, violations
    )


__all__ = ["ExperimentResult", "run_experiment"]
