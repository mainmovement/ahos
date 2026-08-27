#!/usr/bin/env python3
"""Read-only prediction→outcome lifecycle census.

Usage:
  python scripts/prediction_lifecycle_status.py
  python scripts/prediction_lifecycle_status.py --json-out reports/lifecycle_status.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.learning.prediction_lifecycle import lifecycle_status  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args(argv)
    report = lifecycle_status()
    text = json.dumps(report, indent=2, ensure_ascii=False, default=str)
    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.json_out}")
    print(text)
    # Honest exit: 0 always for status; data gaps are in the JSON notes.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
