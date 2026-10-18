#!/usr/bin/env python3
"""Export tier-gate / replay honesty as Self-Evaluation snapshot for Arena."""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUMMARY = ROOT / "reports" / "grok" / "M13_REPLAY" / "tier_gate_exports" / "summary.json"
DEFAULT_OUT = ROOT / "reports" / "grok" / "M58" / "self_eval_snapshot.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_measurable(raw: str | None) -> tuple[int | None, int | None]:
    if not raw or not isinstance(raw, str):
        return None, None
    m = re.match(r"^(\d+)/(\d+)$", raw.strip())
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2))


def build_snapshot(summary_path: Path) -> dict:
    summary: dict = {}
    if summary_path.is_file():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            summary = {}
    markets = summary.get("markets") if isinstance(summary.get("markets"), dict) else {}
    gold = markets.get("gold") if isinstance(markets.get("gold"), dict) else {}
    passed, total = _parse_measurable(gold.get("measurable_pass"))
    replay = summary.get("replay") if isinstance(summary.get("replay"), dict) else {}
    verdict = replay.get("verdict") or "UNKNOWN"
    unmeas = gold.get("unmeasurable") if isinstance(gold.get("unmeasurable"), list) else []
    note = f"{summary.get('label', 'PAPER')}: {verdict}; gold tier {gold.get('tier', 'T0')}"
    scorecard = {
        "period": "week",
        "decisionsReviewed": total,
        "decisionsWithEvidence": passed,
        "decisionsWithUnseenCheck": None,
        "calibrationNote": note,
        "unresolvedItems": len(unmeas),
        "highlights": [
            {
                "id": "tier-gold",
                "market": "gold",
                "rationaleSummary": f"measurable {gold.get('measurable_pass', '-')}",
                "outcomeKnown": "no",
                "reviewState": "REVIEWED",
            }
        ],
        "allDecisions": [],
    }
    return {
        "generated_at": _utc_now(),
        "paper_only": True,
        "selfEvaluation": {
            "executionMode": "PAPER_ONLY",
            "realTrading": False,
            "source": "M13_REPLAY/tier_gate_exports/summary.json",
            "generatedAt": _utc_now(),
            "demo": False,
            "scorecards": [scorecard, {**scorecard, "period": "month"}],
        },
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Export self-evaluation snapshot for Arena")
    ap.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args(argv)
    payload = build_snapshot(Path(args.summary))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    sc = payload["selfEvaluation"]["scorecards"][0]
    print(f"wrote {out} evidence={sc.get('decisionsWithEvidence')}/{sc.get('decisionsReviewed')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
