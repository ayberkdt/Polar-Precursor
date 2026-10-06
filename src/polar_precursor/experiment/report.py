"""Gate report: the tables plan 07 lists, rendered as Markdown from one run.

Sections: primary result line; pooled ladder scores; secondary comparisons
(H4, controls, ladder steps); per-lead-bin primary test with Holm; d_s by
storm class; peak errors; power given the measured SD of d_s; buffer
violations. Numbers are not interpreted here; the gate decision table of the
main plan is applied by hand.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd

from polar_precursor.design.ladder import INTENSITY, LEAD_BIN
from polar_precursor.experiment.pipeline import ExperimentResult
from polar_precursor.statistics.power import power_table
from polar_precursor.statistics.secondary import (
    comparison_table,
    h2_gain_peaks_mid_lead,
    lead_bin_tests,
    loss_difference_by_class,
)


def _markdown_table(frame: pd.DataFrame, *, floats: str = "{:.4f}") -> str:
    if frame.empty:
        return "_(empty)_"
    cells = frame.copy()
    for column in cells.columns:
        if pd.api.types.is_float_dtype(cells[column]):
            cells[column] = cells[column].map(lambda v: "" if pd.isna(v) else floats.format(v))
    header = "| " + " | ".join(str(c) for c in cells.columns) + " |"
    rule = "|" + "|".join(" --- " for _ in cells.columns) + "|"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in cells.itertuples(index=False)]
    return "\n".join([header, rule, *body])


def gate_report(
    result: ExperimentResult,
    design: pd.DataFrame,
    *,
    title: str = "Gate report",
    power_counts: Sequence[int] = (30, 100, 127, 150, 200),
    secondary_resamples: int | None = None,
) -> str:
    config = result.config
    reference = config.test.reference_model
    candidate = config.test.candidate_model
    n_resamples = (
        config.test.bootstrap_resamples if secondary_resamples is None else secondary_resamples
    )
    seed = config.test.bootstrap_seed
    per_storm = result.per_storm
    d = (per_storm[reference] - per_storm[candidate]).to_numpy(dtype=np.float64)
    d = d[np.isfinite(d)]
    sd_d = float(np.std(d, ddof=1)) if len(d) > 1 else float("nan")

    pooled = result.scores[result.scores[LEAD_BIN] == "all"].drop(columns=[LEAD_BIN, INTENSITY])
    comparisons = comparison_table(
        per_storm,
        n_resamples=n_resamples,
        seed=seed,
        confidence_level=config.test.confidence_level,
        weight=config.test.storm_weight,
    )
    lead = lead_bin_tests(
        design,
        result.cv.predictions,
        reference=reference,
        candidate=candidate,
        n_resamples=n_resamples,
        seed=seed,
        confidence_level=config.test.confidence_level,
        weight=config.test.storm_weight,
    )
    by_class = loss_difference_by_class(per_storm, reference, candidate)
    peaks = result.peaks
    power = power_table(power_counts, sd_loss_difference=sd_d)

    lines = [
        f"# {title}",
        "",
        f"Configuration `{config.name}` (digest `{config.digest()[:12]}`), "
        f"ladder {list(config.ladder)}, G = {len(per_storm)} storms, {len(design)} samples.",
        "",
        "## Primary result",
        "",
        result.primary_line(),
        "",
        f"Storm-to-storm SD of d_s = MSE_{reference} − MSE_{candidate}: {sd_d:.5f} "
        f"(input to the minimum-effect decision, plan 07 item 9).",
        "",
        "## Ladder, lead times pooled",
        "",
        _markdown_table(pooled),
        "",
        "## Secondary comparisons (cluster bootstrap, one-sided p)",
        "",
        _markdown_table(comparisons),
        "",
        "## Primary comparison per lead-time bin (Holm-adjusted)",
        "",
        _markdown_table(lead),
        "",
        "H2 (gain highest in the 105-195 min bins): "
        f"{'yes' if h2_gain_peaks_mid_lead(lead) else 'no'} (descriptive).",
        "",
        "## d_s by storm class",
        "",
        _markdown_table(by_class),
        "",
        f"## Peak errors of {candidate} per storm",
        "",
        f"amplitude error mean {peaks['amplitude_error'].mean():+.4f} "
        f"(SD {peaks['amplitude_error'].std(ddof=1):.4f}); "
        f"timing error median {peaks['timing_error_min'].median():+.0f} min, "
        f"IQR {peaks['timing_error_min'].quantile(0.25):+.0f}.."
        f"{peaks['timing_error_min'].quantile(0.75):+.0f} min.",
        "",
        "## Power (2.8 × SD / √G with the measured SD)",
        "",
        _markdown_table(power),
        "",
        "## Buffer check",
        "",
        "no violations"
        if not result.buffer_violations
        else "\n".join(
            f"- groups {v.earlier_group} → {v.later_group}: {v.gap_h:.1f} h"
            for v in result.buffer_violations
        ),
        "",
    ]
    return "\n".join(lines)


__all__ = ["gate_report"]
