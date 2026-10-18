#!/usr/bin/env python3
"""Export M49 lessons sqlite to JSON for Arena read-only display. No secrets."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.learning.lessons_ledger import LessonsLedger, STATUS_UNVERIFIED
from architecture.mission.ledger import default_ledger_path


def _map_row(row) -> dict:
    status = "PROPOSED" if row.status == STATUS_UNVERIFIED else "ACCEPTED"
    return {
        "demo": False,
        "id": row.lesson_id,
        "market": (row.market or "unknown").upper(),
        "mistake": row.claim,
        "lesson": row.counterfactual,
        "sourceReplayId": row.evidence_refs[0] if row.evidence_refs else None,
        "status": status,
        "reason": f"{row.source}|{row.taxonomy}|{row.status}",
        "unseenTest": None,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Export M49 lessons for Arena")
    ap.add_argument(
        "--sqlite",
        type=Path,
        default=None,
        help="lessons sqlite (default: beside mission ledger)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "reports" / "grok" / "M49" / "lessons_snapshot.json",
    )
    ap.add_argument("--as-of", default=None, help="ISO date for visibility filter")
    args = ap.parse_args(argv)
    ledger = default_ledger_path(create=False)
    db = args.sqlite or ledger.parent / "m49_lessons.sqlite"
    if not db.is_file():
        payload = {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "paper_only": True,
            "source": str(db),
            "chain_ok": None,
            "lessons": [],
            "note": "sqlite missing; no lessons exported",
        }
    else:
        store = LessonsLedger(db)
        try:
            as_of = args.as_of or datetime.now(timezone.utc).strftime("%Y-%m-%d")
            visible = store.visible(as_of)
            payload = {
                "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "paper_only": True,
                "source": str(db),
                "chain_ok": store.verify(),
                "lessons": [_map_row(r) for r in visible if r.source != "review"],
            }
        finally:
            store.close()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {out} lessons={len(payload['lessons'])} chain_ok={payload.get('chain_ok')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
