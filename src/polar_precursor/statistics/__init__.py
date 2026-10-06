"""Primary and confirmatory tests, power bookkeeping."""

from polar_precursor.statistics.bootstrap import (
    BootstrapResult,
    cluster_bootstrap,
    paired_losses,
    relative_rmse_reduction,
)
from polar_precursor.statistics.permutation import (
    PermutationResult,
    permutation_test,
    permute_polar_block,
)
from polar_precursor.statistics.power import (
    POWER_FACTOR,
    detectable_difference_sd,
    power_table,
    required_storms,
)
from polar_precursor.statistics.secondary import (
    PAIRS_SECONDARY,
    PairResult,
    compare_pair,
    comparison_table,
    h2_gain_peaks_mid_lead,
    holm_adjust,
    lead_bin_tests,
    loss_difference_by_class,
    per_storm_losses_by,
)

__all__ = [
    "PAIRS_SECONDARY",
    "POWER_FACTOR",
    "PairResult",
    "compare_pair",
    "comparison_table",
    "h2_gain_peaks_mid_lead",
    "holm_adjust",
    "lead_bin_tests",
    "loss_difference_by_class",
    "per_storm_losses_by",
    "BootstrapResult",
    "PermutationResult",
    "cluster_bootstrap",
    "detectable_difference_sd",
    "paired_losses",
    "permutation_test",
    "permute_polar_block",
    "power_table",
    "relative_rmse_reduction",
    "required_storms",
]
