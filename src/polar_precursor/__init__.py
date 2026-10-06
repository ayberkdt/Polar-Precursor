"""Polar Precursor thesis line: model ladder, storm-grouped validation, statistics.

This package is the research code of the thesis and stays in this repository.
It consumes ``space_environment`` (readers, physics rules, feature and sample
builders, which are destined for Sidera) and adds what only the thesis needs:

``config``       experiment configuration (TOML) with the pre-registration knobs
``design``       column convention, the model ladder B0-M, design-matrix builder
``models``       ridge regression (closed form, standardised, no third-party ML)
``metrics``      residual summaries, RMSE, correlation, skill, per-storm losses
``validation``   storm-grouped nested cross-validation with a buffer check
``statistics``   cluster bootstrap, stratified permutation test, power
``synthetic``    synthetic storms with a known polar contribution
``experiment``   end-to-end pipeline, skeleton test, run manifest

Layering (enforced by import-linter): experiment → statistics → validation →
models | metrics | synthetic → design → config. ``space_environment`` never
imports this package.
"""

__all__: list[str] = []
