#!/usr/bin/env python3
"""Stage M62 portable bundle to an empty folder on G: (or any drive). No secrets."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.portable.pack import build_bundle


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Stage AHOS portable bundle (M62)")
    ap.add_argument(
        "--dest",
        type=Path,
        default=ROOT.parent / "ahos_portable_staging",
        help="empty destination directory (default: ../ahos_portable_staging)",
    )
    args = ap.parse_args(argv)
    dest = args.dest.resolve()
    if dest.exists() and any(dest.iterdir()):
        print(f"refusing non-empty dest: {dest}", file=sys.stderr)
        return 2
    report = build_bundle(ROOT, dest)
    print(json.dumps(asdict(report), indent=2, ensure_ascii=False))
    return 0 if report.health_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
