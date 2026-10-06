"""Run manifest: what code, configuration, environment and data produced a result."""

from __future__ import annotations

import json
import platform
import subprocess
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from polar_precursor.config import ExperimentConfig
from space_environment.common.provenance import sha256_file


def git_commit(root: Path) -> str | None:
    """HEAD commit of ``root``'s repository, with ``+dirty`` when the tree has changes."""
    try:
        head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return head + ("+dirty" if status.strip() else "")


def build_manifest(
    config: ExperimentConfig,
    *,
    root: Path,
    data_files: Iterable[Path] = (),
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    files = {str(path): sha256_file(path) for path in data_files}
    manifest: dict[str, Any] = {
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": git_commit(root),
        "config_name": config.name,
        "config_digest": config.digest(),
        "config": config.to_dict(),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
        },
        "data_files_sha256": files,
    }
    if extra:
        manifest.update(extra)
    return manifest


def write_manifest(path: Path, manifest: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, default=str), encoding="utf-8")


__all__ = ["build_manifest", "git_commit", "write_manifest"]
