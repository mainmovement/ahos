"""Daily census of opens blocked by the two-family vote gate (PAPER_ONLY)."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.markets.paper_trade_gates import INDEPENDENT_VOTE_FAMILIES

REL = Path("reports") / "grok" / "PAPER" / "multi_signal_block_daily.json"
LOG_REL = Path("reports") / "grok" / "PAPER" / "paper_trades.jsonl"


def _utc_day(ts: str) -> str | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")
    except ValueError:
        return None


def _missing_families(vote: dict[str, Any]) -> list[str]:
    by_vote = {str(v.get("family")): str(v.get("vote")) for v in (vote.get("votes") or []) if isinstance(v, dict)}
    missing = []
    for family in INDEPENDENT_VOTE_FAMILIES:
        if by_vote.get(family) != "AGREE":
            missing.append(family)
    return missing


def build_daily_block_counter(root: Path, day: str | None = None) -> dict[str, Any]:
    root = Path(root)
    day = day or datetime.now(timezone.utc).strftime("%Y-%m-%d")
    by_desk: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"blocked": 0, "missing_family_counts": {f: 0 for f in INDEPENDENT_VOTE_FAMILIES}}
    )
    log = root / LOG_REL
    if log.is_file():
        for line in log.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("event") != "NO_TRADE" or row.get("reason") != "MULTI_SIGNAL_AGREEMENT":
                continue
            if _utc_day(str(row.get("ts") or "")) != day:
                continue
            desk = str(row.get("desk") or "UNKNOWN")
            cell = by_desk[desk]
            cell["blocked"] += 1
            vote = row.get("independent_votes") if isinstance(row.get("independent_votes"), dict) else {}
            for fam in _missing_families(vote):
                cell["missing_family_counts"][fam] += 1
    desks = []
    for desk in sorted(by_desk):
        cell = by_desk[desk]
        desks.append({"desk": desk, "blocked": cell["blocked"], "missing_family_counts": cell["missing_family_counts"]})
    return {
        "schema": "ahos.multi_signal_block_daily.v1",
        "day_utc": day,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "blocked_opens": sum(d["blocked"] for d in desks),
        "by_desk": desks,
        "note": "A family counts as missing on a block when its vote was not AGREE (unavailable, flat, disagree, or absent). This is a feed census, not an edge score.",
    }


def export_daily_block_counter(root: Path, day: str | None = None) -> dict[str, Any]:
    doc = build_daily_block_counter(root, day)
    out = Path(root) / REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc
