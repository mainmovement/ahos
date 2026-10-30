"""A directory walk that stops. Measurements must not recurse without a cap."""
from __future__ import annotations

import os
import time
from pathlib import Path

SKIP_NAMES = frozenset({
    ".git",
    ".hg",
    ".next",
    ".venv",
    "__pycache__",
    "cache",
    "dist",
    "node_modules",
    "reports",
    "tmp",
    "vendor",
    "vendor_assets",
})


def find_files(
    root: Path,
    suffixes: tuple[str, ...],
    *,
    max_depth: int = 3,
    max_files: int = 50,
    max_entries: int = 2000,
    timeout_s: float = 5.0,
) -> dict:
    """Walk `root` without following links. Skip known large directories.

    Returns whatever it found when the depth, file, entry, or time cap is hit.
    """
    start = time.monotonic()
    if timeout_s <= 0:
        return {
            "files": [],
            "seen_entries": 0,
            "timed_out": True,
            "capped": False,
            "elapsed_s": 0.0,
        }
    deadline = start + timeout_s
    found: list[str] = []
    seen = 0
    timed_out = False
    capped = False

    def walk(directory: Path, depth: int) -> None:
        nonlocal seen, timed_out, capped
        if timed_out or capped or len(found) >= max_files:
            return
        try:
            entries = os.scandir(directory)
        except OSError:
            return
        with entries:
            for entry in entries:
                seen += 1
                if time.monotonic() >= deadline:
                    timed_out = True
                    return
                if seen >= max_entries or len(found) >= max_files:
                    capped = True
                    return
                try:
                    if entry.is_symlink():
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        if entry.name in SKIP_NAMES or entry.name.startswith("."):
                            continue
                        if depth < max_depth:
                            walk(Path(entry.path), depth + 1)
                        continue
                    if entry.is_file(follow_symlinks=False) and entry.name.endswith(suffixes):
                        found.append(entry.path)
                except OSError:
                    continue

    walk(Path(root), 0)
    return {
        "files": found,
        "seen_entries": seen,
        "timed_out": timed_out,
        "capped": capped,
        "elapsed_s": round(time.monotonic() - start, 4),
    }
