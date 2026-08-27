#!/usr/bin/env python3
"""Generate the Lane-A integrity baseline (`config/lane_a_freeze.sha256`).

WHY
---
Lane A (discovery + paper_trading) is the frozen scientific surface: once an
experiment is running, silently editing these files invalidates every result
derived from them. `test_lane_a_frozen_files_hash_integrity` guards that.

The original baseline manifest lived at `../ahos_snap_w15_after.txt` — OUTSIDE
the repository — so it did not survive `git clone` and the drift test could
never run for anyone but its author. This script re-anchors the baseline INSIDE
the repo so the guarantee is portable.

USAGE
-----
    python scripts/freeze_lane_a.py            # verify against the baseline
    python scripts/freeze_lane_a.py --write    # (re-)anchor the baseline

Re-anchoring is a DELIBERATE governance act: it declares "the current Lane-A
surface is the new scientific reference". Do it only when a Lane-A change has
been reviewed and approved, and say so in the commit message.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "config" / "lane_a_freeze.sha256"

# The frozen Lane-A surface: implementation + the schema/registry that define
# its semantics. Test files are excluded (tests may grow without invalidating
# recorded observations); caches are excluded.
#
# INTENTIONAL EXCLUSION: paper_trading/strategies.json is NOT frozen here.
# Strategy cards may evolve under research governance without rewriting the
# Lane-A scientific surface hash. Schemas + engine .py remain frozen.
FROZEN_GLOBS = [
    "discovery/*.py",
    "paper_trading/*.py",
    "discovery/schema_sqlite.sql",
    "discovery/providers.yaml",
    "paper_trading/schema.sql",
    "paper_trading/schema_v2.sql",
    "paper_trading/schema_v3.sql",
]


def frozen_files(root: Path | None = None) -> list[Path]:
    root = Path(root) if root is not None else ROOT
    seen: set[Path] = set()
    for pattern in FROZEN_GLOBS:
        for p in sorted(root.glob(pattern)):
            if p.is_file() and "__pycache__" not in p.parts:
                seen.add(p)
    return sorted(seen)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_manifest(root: Path | None = None) -> dict[str, str]:
    root = Path(root) if root is not None else ROOT
    return {p.relative_to(root).as_posix(): digest(p) for p in frozen_files(root=root)}


def load_baseline(root: Path | None = None) -> dict[str, str]:
    root = Path(root) if root is not None else ROOT
    baseline = root / BASELINE.relative_to(ROOT)
    if not baseline.exists():
        return {}
    out: dict[str, str] = {}
    for line in baseline.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        sha, rel = line.split(None, 1)
        out[rel.strip()] = sha
    return out


def write_baseline(root: Path | None = None) -> int:
    root = Path(root) if root is not None else ROOT
    baseline = root / BASELINE.relative_to(ROOT)
    manifest = current_manifest(root=root)
    lines = [
        "# AHOS Lane-A Integrity Baseline",
        "# sha256  relative/path",
        "#",
        "# Lane A is the FROZEN scientific surface (discovery + paper_trading).",
        "# Any drift here invalidates observations recorded under the old code.",
        "# Regenerate ONLY as a reviewed governance act:",
        "#     python scripts/freeze_lane_a.py --write",
        "#",
    ]
    lines += [f"{sha}  {rel}" for rel, sha in sorted(manifest.items())]
    baseline.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(manifest)} pinned files -> {baseline.relative_to(root)}")
    return len(manifest)


def verify(root: Path | None = None) -> tuple[list[str], list[str], list[str]]:
    base, cur = load_baseline(root=root), current_manifest(root=root)
    drift = sorted(p for p in base.keys() & cur.keys() if base[p] != cur[p])
    missing = sorted(base.keys() - cur.keys())
    untracked = sorted(cur.keys() - base.keys())
    return drift, missing, untracked


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS Lane-A freeze manifest")
    ap.add_argument("--write", action="store_true", help="(re-)anchor the baseline")
    args = ap.parse_args(argv)

    if args.write:
        write_baseline()
        return 0

    if not BASELINE.exists():
        print(f"ERROR: no baseline at {BASELINE.relative_to(ROOT)}")
        print("Create it with: python scripts/freeze_lane_a.py --write")
        return 1

    drift, missing, untracked = verify()
    for p in drift:
        print(f"DRIFT     {p}")
    for p in missing:
        print(f"MISSING   {p}")
    for p in untracked:
        print(f"UNTRACKED {p}")
    if not (drift or missing):
        print(f"Lane-A integrity OK ({len(load_baseline())} files pinned)")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
