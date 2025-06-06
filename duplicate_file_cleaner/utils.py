"""Utility functions for detecting and removing duplicate files."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Tuple, Iterable


def _file_hash(path: Path, chunk_size: int = 8192) -> str:
    """Return SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_duplicates(directory: str, extensions: Iterable[str] | None = None) -> List[List[Path]]:
    """Find exact duplicate files under *directory*.

    Parameters
    ----------
    directory: str
        Directory to search for duplicates.
    extensions: Iterable[str] | None
        Optional collection of file extensions to include (case-insensitive).

    Returns
    -------
    List[List[Path]]
        Groups of duplicate paths sorted by modification time.
    """
    base = Path(directory)
    allowed: set[str] | None = None
    if extensions is not None:
        allowed = {e.lower() if e.startswith('.') else f'.{e.lower()}' for e in extensions}
    hashes: Dict[Tuple[int, str], List[Path]] = {}
    for root, _, files in os.walk(base):
        for name in files:
            path = Path(root) / name
            if allowed is not None and path.suffix.lower() not in allowed:
                continue
            try:
                size = path.stat().st_size
                digest = _file_hash(path)
            except (OSError, PermissionError):
                continue
            key = (size, digest)
            hashes.setdefault(key, []).append(path)
    duplicates: List[List[Path]] = []
    for paths in hashes.values():
        if len(paths) > 1:
            paths.sort(key=lambda p: p.stat().st_mtime)
            duplicates.append(paths)
    return duplicates


def delete_files(files: List[Path], log_file: Path) -> int:
    """Delete *files* and log actions to *log_file*.

    Returns total bytes freed.
    """
    freed = 0
    with log_file.open("a") as log:
        for f in files:
            try:
                size = f.stat().st_size
                f.unlink()
                freed += size
                log.write(f"Deleted {f}\n")
            except FileNotFoundError:
                log.write(f"Missing {f}\n")
    return freed
