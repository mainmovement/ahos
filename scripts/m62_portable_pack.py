#!/usr/bin/env python3
"""Stage an M62 portable folder. Destination is an argument, never a fixed drive."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.portable.pack import build_bundle


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Stage a paper-only portable AHOS folder")
    ap.add_argument("--dest", required=True, help="empty directory outside the repo")
    ap.add_argument("--src", default=str(ROOT))
    args = ap.parse_args(argv)
    report = build_bundle(Path(args.src), Path(args.dest))
    print(
        f"copied={len(report.copied)} skipped_secrets={len(report.skipped_secrets)} "
        f"health_ok={report.health_ok} paper_only={report.paper_only}"
    )
    return 0 if report.health_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
