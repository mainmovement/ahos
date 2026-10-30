"""Load the committed MEGA9 registration. A byte change blocks scoring."""
from __future__ import annotations

import hashlib
from pathlib import Path

YAML_REL = Path("docs") / "prereg" / "MEGA9.yaml"
HASH_REL = Path("docs") / "prereg" / "MEGA9.sha256"


def file_hash(root: Path) -> str:
    raw = (Path(root) / YAML_REL).read_bytes()
    return hashlib.sha256(raw).hexdigest()


def registered_hash(root: Path) -> str:
    return (Path(root) / HASH_REL).read_text(encoding="utf-8").strip()


def hash_ok(root: Path) -> bool:
    return file_hash(root) == registered_hash(root)


def trial_counts(root: Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    current = None
    for line in (Path(root) / YAML_REL).read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("M9-") and stripped.endswith(":"):
            current = stripped[:-1]
        elif current and stripped.startswith("trial_count:"):
            counts[current] = int(stripped.split(":", 1)[1].strip())
            current = None
    return counts
