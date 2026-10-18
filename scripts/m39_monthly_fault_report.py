#!/usr/bin/env python3
"""Run the M39 monthly paper fault suite and write a JSON report. No injection."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.health.faults import M39_FAULTS, run_fault_suite


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="M39 monthly fault suite (paper, synthetic)")
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "reports" / "grok" / "M39" / "monthly_fault_suite.json",
        help="JSON report path",
    )
    args = ap.parse_args(argv)
    results = run_fault_suite(M39_FAULTS)
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "suite": "M39",
        "faults": [asdict(r) for r in results],
        "all_halt": all(r.level == "HALT" for r in results),
        "all_within_budget": all(r.within_budget for r in results),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} faults={len(results)} all_halt={payload['all_halt']}")
    return 0 if payload["all_halt"] and payload["all_within_budget"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
