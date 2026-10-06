"""Experiment configuration: the pre-registration knobs, frozen in one TOML file.

Every number that plan 07 lists as a decision lives here, not in code. The
defaults below are the *proposals* of ``plans/07_istatistik_pilot_ve_kapi.md``
(section "Ön kayıt belgesinde sabitlenecek kararlar") and are marked as such;
the pre-registration document replaces them by editing ``configs/pilot.toml``.
"""

from __future__ import annotations

import hashlib
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:  # pragma: no cover - exercised only on Python 3.10
    import tomli as tomllib


@dataclass(frozen=True, slots=True)
class StormSelection:
    """Which storms enter the primary test (plan 07, decisions 1 and 3)."""

    period_start: str = "2001-05-01"
    period_end: str = "2015-12-31"
    primary_max_symh_nt: float = -50.0  # primary pool: min SYM-H below this (moderate and up)
    satellites: tuple[str, ...] = ("CHAMP", "GRACE-A")
    min_symh_coverage: float = 0.8


@dataclass(frozen=True, slots=True)
class SampleSelection:
    """Lead-time pool and input depth (plan 07 decision 4; plan 04)."""

    lead_window_min: tuple[float, float] = (60.0, 270.0)
    lead_bin_edges_min: tuple[float, ...] = (60.0, 105.0, 150.0, 195.0, 240.0, 270.0)
    inputs_low: int = 4
    inputs_polar: int = 4


@dataclass(frozen=True, slots=True)
class CrossValidation:
    """Storm-grouped nested CV (plan 07, "Çapraz doğrulama iskeleti")."""

    outer_folds: int = 10
    inner_folds: int = 5
    buffer_h: float = 57.0  # longest feature memory; groups closer than this must be one cluster
    assignment: str = "round_robin"  # groups sorted by epoch, dealt to folds in turn


@dataclass(frozen=True, slots=True)
class RidgeSettings:
    """Model class (plan 07 decision 10): ridge, penalty tuned in the inner loop."""

    alphas: tuple[float, ...] = (0.01, 0.1, 1.0, 10.0, 100.0, 1000.0)
    standardise: bool = True
    impute: str = "train_mean"


@dataclass(frozen=True, slots=True)
class PrimaryTest:
    """Primary metric and confirmatory test (plan 07 decisions 2, 7, 8, 11)."""

    reference_model: str = "B3"
    candidate_model: str = "M"
    storm_weight: str = "equal"  # or "samples"
    bootstrap_resamples: int = 10_000
    bootstrap_seed: int = 20270207
    confidence_level: float = 0.95
    permutation_resamples: int = 1_000
    permutation_seed: int = 20270207
    permutation_strata: tuple[str, ...] = ("intensity", "lead_bin")
    one_sided: bool = True  # H1: M better than B3


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    name: str = "pilot"
    description: str = ""
    ladder: tuple[str, ...] = ("B0", "B1", "B2", "D", "B3", "B3k", "B3t", "B3t2", "M")
    storms: StormSelection = field(default_factory=StormSelection)
    samples: SampleSelection = field(default_factory=SampleSelection)
    cv: CrossValidation = field(default_factory=CrossValidation)
    ridge: RidgeSettings = field(default_factory=RidgeSettings)
    test: PrimaryTest = field(default_factory=PrimaryTest)

    def __post_init__(self) -> None:
        if (
            self.test.reference_model not in self.ladder
            or self.test.candidate_model not in self.ladder
        ):
            raise ValueError("reference and candidate models must be in the ladder.")
        if self.cv.outer_folds < 2 or self.cv.inner_folds < 2:
            raise ValueError("folds must be at least 2.")
        if not 0.0 < self.test.confidence_level < 1.0:
            raise ValueError("confidence_level must lie in (0, 1).")
        if self.test.storm_weight not in ("equal", "samples"):
            raise ValueError("storm_weight must be 'equal' or 'samples'.")
        edges = self.samples.lead_bin_edges_min
        if list(edges) != sorted(set(edges)) or len(edges) < 2:
            raise ValueError("lead_bin_edges_min must be strictly increasing.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def digest(self) -> str:
        """SHA-256 of the canonical field dump; identifies a configuration in manifests."""
        text = repr(sorted(_flatten(self.to_dict()).items()))
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _flatten(mapping: dict[str, Any], prefix: str = "") -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in mapping.items():
        name = f"{prefix}{key}"
        if isinstance(value, dict):
            flat.update(_flatten(value, f"{name}."))
        else:
            flat[name] = tuple(value) if isinstance(value, list) else value
    return flat


def _section(data: dict[str, Any], name: str, cls: type) -> Any:
    raw = dict(data.get(name, {}))
    for key, value in raw.items():
        if isinstance(value, list):
            raw[key] = tuple(value)
    try:
        return cls(**raw)
    except TypeError as error:
        raise ValueError(f"[{name}]: {error}") from error


def load_config(path: str | Path) -> ExperimentConfig:
    """Read an experiment TOML file (see ``configs/pilot.toml``)."""
    file_path = Path(path)
    with file_path.open("rb") as handle:
        data = tomllib.load(handle)
    top = {key: value for key, value in data.items() if not isinstance(value, dict)}
    known = {"name", "description", "ladder"}
    unknown = set(top) - known
    if unknown:
        raise ValueError(f"{file_path.name}: unknown top-level keys {sorted(unknown)}.")
    if "ladder" in top:
        top["ladder"] = tuple(top["ladder"])
    return ExperimentConfig(
        **top,
        storms=_section(data, "storms", StormSelection),
        samples=_section(data, "samples", SampleSelection),
        cv=_section(data, "cv", CrossValidation),
        ridge=_section(data, "ridge", RidgeSettings),
        test=_section(data, "test", PrimaryTest),
    )


__all__ = [
    "CrossValidation",
    "ExperimentConfig",
    "PrimaryTest",
    "RidgeSettings",
    "SampleSelection",
    "StormSelection",
    "load_config",
]
