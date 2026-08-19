#!/usr/bin/env python3
"""Generate an AHOS scoring calibration report from committed data.

Joins persisted predictions (`opportunity_score_ledger`) to frozen Lane-A
outcome labels and reports hit rates per score band with Wilson intervals.

Read-only. Writes exactly one artifact under reports/. Never touches Lane-A,
never adjusts a weight or threshold.

Usage:
    python scripts/calibration_report.py
    python scripts/calibration_report.py --horizon 24h --event-class +50%
    python scripts/calibration_report.py --stdout

Exit codes:
    0 = report generated (INCLUDING an honest INSUFFICIENT_DATA verdict)
    2 = report could not be generated at all
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.learning.calibration import (  # noqa: E402
    DEFAULT_EVENT_CLASS,
    DEFAULT_HORIZON,
    CalibrationHarness,
)
from architecture.learning.score_ledger import ScoreLedger  # noqa: E402
from scripts.evidence_common import environment_fingerprint, git_meta, utc_now  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AHOS scoring calibration report")
    ap.add_argument("--horizon", default=DEFAULT_HORIZON,
                    help="outcome horizon (15m,1h,4h,12h,24h,72h,7d)")
    ap.add_argument("--event-class", default=DEFAULT_EVENT_CLASS,
                    help="outcome event class (+25%%,+50%%,+100%%,+200%%)")
    ap.add_argument("--out", default=None, help="output path for the JSON artifact")
    ap.add_argument("--stdout", action="store_true", help="also print the report")
    args = ap.parse_args(argv)

    try:
        harness = CalibrationHarness()
        report = harness.run(horizon=args.horizon, event_class=args.event_class)
    except Exception as e:
        print(f"ERROR: calibration failed: {type(e).__name__}: {e}")
        return 2

    payload = report.as_dict()
    payload["command"] = "python scripts/calibration_report.py"
    payload["timestamp_utc"] = utc_now()
    payload["git"] = git_meta()
    payload["environment"] = environment_fingerprint()
    payload["ledger_census"] = ScoreLedger().engine_versions()

    out = Path(args.out) if args.out else (
        ROOT / "reports" / f"calibration_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"calibration_status : {report.verdict}")
    print(f"predictions (all)  : {report.total_predictions}")
    print(f"eligible pairs     : {report.joined_pairs}  "
          f"(horizon={report.horizon}, class={report.event_class})")
    print(f"eligible sources   : {report.eligible_sources}")
    print(f"source census      : {report.source_census or '(empty ledger)'}")
    print(f"excluded           : {report.excluded_predictions} "
          f"{report.exclusion_reasons or ''}")
    print(f"dataset fingerprint: {report.dataset_fingerprint[:16] or '(none)'}")
    for band in report.bands:
        rate = f"{band.rate:.3f}" if band.rate is not None else "n/a"
        print(f"  band {band.band:>7}: n={band.n:<6} hits={band.positives:<5} "
              f"rate={rate:<6} {band.verdict}"
              + (f" ({band.reason})" if band.reason else ""))
    for finding in report.findings:
        print(f"  - {finding}")
    print(f"artifact           : {out.relative_to(ROOT)}")

    if args.stdout:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
