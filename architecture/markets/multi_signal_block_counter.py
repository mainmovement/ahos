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
            "fee_drag": 0,
            "cycles_with_votes": 0,
            "agree_counts": {f: 0 for f in INDEPENDENT_VOTE_FAMILIES},
            "vote_states": {
                f: {"AGREE": 0, "DISAGREE": 0, "FLAT": 0, "UNAVAILABLE": 0, "ABSENT": 0}
                for f in INDEPENDENT_VOTE_FAMILIES
            },
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
            reason = row.get("reason")
            if event not in {"OPEN", "NO_TRADE"}:
                continue
            if event == "NO_TRADE" and reason not in {"MULTI_SIGNAL_AGREEMENT", "FEE_DRAG_EXPECTED_PROFIT_LT_2X_FEES"}:
                continue
            desk = str(row.get("desk") or "UNKNOWN")
            cell = by_desk[desk]
            if event == "OPEN":
                cell["opens"] += 1
            elif reason == "FEE_DRAG_EXPECTED_PROFIT_LT_2X_FEES":
                cell["fee_drag"] += 1
            else:
                cell["blocks"] += 1
            votes = _vote_map(row)
            if votes:
                cell["cycles_with_votes"] += 1
                seen = set(votes)
                for fam, vote in votes.items():
                    if fam not in cell["agree_counts"]:
                        continue
                    if vote == "AGREE":
                        cell["agree_counts"][fam] += 1
                    bucket = vote if vote in cell["vote_states"][fam] else "UNAVAILABLE"
                    cell["vote_states"][fam][bucket] += 1
                for fam in INDEPENDENT_VOTE_FAMILIES:
                    if fam not in seen:
                        cell["vote_states"][fam]["ABSENT"] += 1
    desks = []
    for desk in sorted(by_desk):
        cell = by_desk[desk]
        never = [fam for fam, n in cell["agree_counts"].items() if n == 0]
        scored = [
            fam
            for fam, states in cell["vote_states"].items()
            if states["AGREE"] or states["DISAGREE"] or states["FLAT"]
        ]
        desks.append(
            {
                "desk": desk,
                "opens": cell["opens"],
                "blocks": cell["blocks"],
                "fee_drag": cell["fee_drag"],
                "cycles_with_votes": cell["cycles_with_votes"],
                "vote_states": cell["vote_states"],
                "agree_counts": cell["agree_counts"],
                "families_never_agreed_in_window": never if cell["cycles_with_votes"] else [],
                "families_scored": scored,
                "families_never_scored": [f for f in INDEPENDENT_VOTE_FAMILIES if f not in scored]
                if cell["cycles_with_votes"]
                else [],
                "families_not_observed": list(INDEPENDENT_VOTE_FAMILIES) if cell["cycles_with_votes"] == 0 else [],
            }
        )
    composite = _composite_stop_census(root, start)
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
        "fee_drag": sum(d["fee_drag"] for d in desks),
        "by_desk": desks,
        "composite_stop_census": composite,
        "honesty": (
            "AGREE is a vote with the side. FLAT means the family was scored and the mean was under the floor. "
            "UNAVAILABLE or ABSENT means it did not score. families_never_agreed includes FLAT. "
            "families_never_scored does not. Fee-drag rows passed the vote gate. "
            "INSUFFICIENT_WINDOW means six hours have not passed since the gate process started."
        ),
    }


def _median(vals: list[float]) -> float | None:
    if not vals:
        return None
    s = sorted(vals)
    mid = len(s) // 2
    if len(s) % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2.0


def _families_with_any_signal(scores: dict[str, Any]) -> list[str]:
    fired = []
    for fam, names in INDEPENDENT_VOTE_FAMILIES.items():
        for name in names:
            try:
                val = float(scores.get(name) or 0.0)
            except (TypeError, ValueError):
                continue
            if abs(val) > 1e-9:
                fired.append(fam)
                break
    return fired


def _composite_buckets(vals: list[float], entry: float = 0.32) -> dict[str, int]:
    buckets = {"below_neg_entry": 0, "inside_entry_band": 0, "above_pos_entry": 0}
    for v in vals:
        if v <= -entry:
            buckets["below_neg_entry"] += 1
        elif v >= entry:
            buckets["above_pos_entry"] += 1
        else:
            buckets["inside_entry_band"] += 1
    return buckets


def _composite_stop_census(root: Path, start: datetime | None) -> dict[str, Any]:
    """Per-desk composite distribution and which vote families produced a non-zero score."""
    reasons: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    composites: dict[str, list[float]] = defaultdict(list)
    family_hits: dict[str, dict[str, int]] = defaultdict(lambda: {f: 0 for f in INDEPENDENT_VOTE_FAMILIES})
    composite_rows = 0
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
            if row.get("event") not in {"NO_TRADE", "SKIP", "OPEN"}:
                continue
            desk = str(row.get("desk") or "UNKNOWN")
            reason = str(row.get("reason") or row.get("event"))
            reasons[desk][reason] += 1
            if row.get("event") == "NO_TRADE" and row.get("reason") == "COMPOSITE_BELOW_ENTRY":
                composite_rows += 1
                try:
                    composites[desk].append(float(row.get("composite")))
                except (TypeError, ValueError):
                    pass
                scores = row.get("signal_scores") if isinstance(row.get("signal_scores"), dict) else {}
                for fam in _families_with_any_signal(scores):
                    family_hits[desk][fam] += 1
    desks = []
    only_composite = True
    saw_no_trade = False
    session_like = ("MARKET", "QUOTE_TIME", "SESSION", "WITNESS", "STALE")
    for desk in sorted(set(reasons) | set(composites)):
        no_trade_reasons = {
            k: v
            for k, v in reasons[desk].items()
            if k not in {"OPEN", "HOLD"} and not any(tok in k for tok in session_like)
        }
        if no_trade_reasons and set(no_trade_reasons) != {"COMPOSITE_BELOW_ENTRY"}:
            only_composite = False
        if no_trade_reasons:
            saw_no_trade = True
        vals = composites.get(desk) or []
        desks.append(
            {
                "desk": desk,
                "reason_counts": dict(reasons[desk]),
                "composite_below_entry_n": len(vals),
                "composite_distribution": None
                if not vals
                else {
                    "min": round(min(vals), 4),
                    "p50": round(_median(vals) or 0.0, 4),
                    "max": round(max(vals), 4),
                    "buckets_vs_entry_0.32": _composite_buckets(vals),
                },
                "families_with_any_nonzero_score": [
                    fam for fam, n in family_hits[desk].items() if n > 0
                ],
                "family_hit_rows": family_hits[desk],
            }
        )
    if not saw_no_trade:
        only_composite = False
    return {
        "entry_abs": 0.32,
        "composite_below_entry_rows": composite_rows,
        "every_desk_stopped_at_composite_below_entry": bool(saw_no_trade and only_composite and composite_rows > 0),
        "by_desk": desks,
        "signal_rule": "A family produced a signal when any of its member scores had absolute value above zero on a COMPOSITE_BELOW_ENTRY row. Zero is silence.",
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
