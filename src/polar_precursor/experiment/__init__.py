"""End-to-end pipeline and run manifest.

The skeleton test lives in ``polar_precursor.experiment.skeleton`` and is run
as a module (``python -m polar_precursor.experiment.skeleton``); it is not
re-exported here so that the module run does not import itself twice.
"""

from polar_precursor.experiment.manifest import build_manifest, git_commit, write_manifest
from polar_precursor.experiment.pipeline import ExperimentResult, run_experiment

__all__ = [
    "ExperimentResult",
    "build_manifest",
    "git_commit",
    "run_experiment",
    "write_manifest",
]
