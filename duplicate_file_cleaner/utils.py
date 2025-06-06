"""Utility functions for detecting and removing duplicate files."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Dict, List, Tuple, Iterable, Optional

import sqlite3
from datetime import datetime


def _file_hash(path: Path, chunk_size: int = 8192) -> str:
    """Return SHA256 hash of a file."""
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


HISTORY_DB = Path.home() / ".duplicate_cleaner_history.db"


def find_duplicates(
    directory: str,
    extensions: Iterable[str] | None = None,
    max_dirs: Optional[int] = None,
) -> List[List[Path]]:
    """Find exact duplicate files under *directory*.

    Parameters
    ----------
    directory: str
        Directory to search for duplicates.
    extensions: Iterable[str] | None
        Optional collection of file extensions to include (case-insensitive).
    max_dirs: int | None
        Optional limit on the number of directories to walk. This allows
        scanning in phases and prevents long blocking operations.

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
    for idx, (root, _, files) in enumerate(os.walk(base)):
        if max_dirs is not None and idx >= max_dirs:
            break
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
    deleted: List[str] = []
    with log_file.open("a") as log:
        for f in files:
            try:
                size = f.stat().st_size
                f.unlink()
                freed += size
                deleted.append(str(f))
                log.write(f"Deleted {f}\n")
            except FileNotFoundError:
                log.write(f"Missing {f}\n")
    if deleted:
        _record_history(deleted, freed, HISTORY_DB)
    return freed


def _record_history(files: List[str], freed: int, db_path: Path = HISTORY_DB) -> None:
    """Record deletion history in an SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, paths TEXT, bytes_freed INTEGER)"
    )
    ts = datetime.utcnow().isoformat()
    conn.execute(
        "INSERT INTO history (timestamp, paths, bytes_freed) VALUES (?, ?, ?)",
        (ts, "\n".join(files), freed),
    )
    conn.commit()
    conn.close()


def get_history(limit: int | None = None, db_path: Path = HISTORY_DB) -> List[tuple[str, str, int]]:
    """Return cleanup history from the SQLite database."""
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, paths TEXT, bytes_freed INTEGER)"
    )
    cur = conn.cursor()
    query = "SELECT timestamp, paths, bytes_freed FROM history ORDER BY id DESC"
    if limit is not None:
        cur.execute(query + " LIMIT ?", (limit,))
    else:
        cur.execute(query)
    rows = cur.fetchall()
    conn.close()
    return rows
