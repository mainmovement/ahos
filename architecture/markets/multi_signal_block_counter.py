"""Daily census of opens blocked by the two-family vote gate (PAPER_ONLY)."""
from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.markets.paper_trade_gates import INDEPENDENT_VOTE_FAMILIES

REL = Path("reports") / "grok" / "PAPER" / "multi_signal_block_daily.json"
WINDOW_REL = Path("reports") / "grok" / "PAPER" / "gate_window_report.json"
# First paper cycle after the Stage 1 two-family gate was loaded into the running process.
GATE_LIVE_AT = "2026-10-30T00:40:16Z"
REQUIRED_WINDOW_HOURS = 6.0
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


def _parse_utc(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _vote_map(row: dict[str, Any]) -> dict[str, str]:
    vote = row.get("independent_votes")
    if not isinstance(vote, dict):
        brain = row.get("brain") if isinstance(row.get("brain"), dict) else {}
        vote = brain.get("independent_votes")
    if not isinstance(vote, dict):
        return {}
    return {str(v.get("family")): str(v.get("vote")) for v in (vote.get("votes") or []) if isinstance(v, dict)}


def build_gate_window_report(
    root: Path,
    *,
    since: str = GATE_LIVE_AT,
    required_hours: float = REQUIRED_WINDOW_HOURS,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Opens vs two-family blocks since the gate went live. A short window is not a 6h result."""
    root = Path(root)
    start = _parse_utc(since)
    now = now or datetime.now(timezone.utc)
    elapsed_h = 0.0 if start is None else max(0.0, (now - start).total_seconds() / 3600.0)
    complete = elapsed_h >= required_hours
    by_desk: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "opens": 0,
            "blocks": 0,
            "cycles_with_votes": 0,
            "agree_counts": {f: 0 for f in INDEPENDENT_VOTE_FAMILIES},
        }
    )
    log = root / LOG_REL
    if log.is_file() and start is not None:
        for line in log.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts = _parse_utc(str(row.get("ts") or ""))
            if ts is None or ts < start:
                continue
            event = row.get("event")
            if event not in {"OPEN", "NO_TRADE"}:
                continue
            if event == "NO_TRADE" and row.get("reason") != "MULTI_SIGNAL_AGREEMENT":
                continue
            desk = str(row.get("desk") or "UNKNOWN")
            cell = by_desk[desk]
            if event == "OPEN":
                cell["opens"] += 1
            else:
                cell["blocks"] += 1
            votes = _vote_map(row)
            if votes:
                cell["cycles_with_votes"] += 1
                for fam, vote in votes.items():
                    if vote == "AGREE" and fam in cell["agree_counts"]:
                        cell["agree_counts"][fam] += 1
    desks = []
    for desk in sorted(by_desk):
        cell = by_desk[desk]
        never = [fam for fam, n in cell["agree_counts"].items() if n == 0]
        desks.append(
            {
                "desk": desk,
                "opens": cell["opens"],
                "blocks": cell["blocks"],
                "cycles_with_votes": cell["cycles_with_votes"],
                "agree_counts": cell["agree_counts"],
                "families_never_agreed_in_window": never if cell["cycles_with_votes"] else [],
                "families_not_observed": list(INDEPENDENT_VOTE_FAMILIES) if cell["cycles_with_votes"] == 0 else [],
            }
        )
    return {
        "schema": "ahos.gate_window_report.v1",
        "generated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "gate_live_at": since,
        "required_hours": required_hours,
        "elapsed_hours": round(elapsed_h, 3),
        "window_status": "COMPLETE" if complete else "INSUFFICIENT_WINDOW",
        "opens": sum(d["opens"] for d in desks),
        "blocks": sum(d["blocks"] for d in desks),
        "by_desk": desks,
        "honesty": (
            "families_never_agreed_in_window is only about rows that reached the vote gate inside this elapsed slice. "
            "INSUFFICIENT_WINDOW means six hours have not passed since the gate process started."
        ),
    }


def export_gate_window_report(root: Path) -> dict[str, Any]:
    doc = build_gate_window_report(root)
    out = Path(root) / WINDOW_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


def export_daily_block_counter(root: Path, day: str | None = None) -> dict[str, Any]:
    doc = build_daily_block_counter(root, day)
    out = Path(root) / REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc
