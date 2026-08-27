#!/usr/bin/env python3
"""Backfill Lane-A observation_state from existing production_observations.

Uses ONLY real collector rows already on disk. Does not invent prices,
outcomes, or hits. Idempotent.

Usage:
  python scripts/backfill_lane_a_from_production.py
  python scripts/backfill_lane_a_from_production.py --limit 50
  python scripts/backfill_lane_a_from_production.py --status-only
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.learning.prediction_lifecycle import (  # noqa: E402
    backfill_from_production_observations,
    lifecycle_status,
)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--status-only", action="store_true")
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args(argv)

    if args.status_only:
        report = lifecycle_status()
    else:
        result = backfill_from_production_observations(limit=args.limit)
        report = {
            "backfill": result.as_dict(),
            "status_after": lifecycle_status(),
        }
        print(
            f"backfill: attempted={result.attempted} registered={result.registered} "
            f"obs_written={result.observations_written} skipped={result.skipped} "
            f"errors={len(result.errors)}"
        )

    text = json.dumps(report, indent=2, ensure_ascii=False, default=str)
    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.json_out}")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
