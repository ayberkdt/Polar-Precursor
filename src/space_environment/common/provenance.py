"""File identity for run records."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: str | Path, *, chunk_bytes: int = 1 << 20) -> str:
    """Hex SHA-256 of a file, read in chunks."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_bytes), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_label(path: str | Path) -> str:
    """``"<file name> | sha256=<digest>"``, the form Sidera providers record."""
    file_path = Path(path)
    return f"{file_path.name} | sha256={sha256_file(file_path)}"
