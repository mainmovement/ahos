"""Weekly hit-rate of each family's own vote sign versus the later price.

Counterfactual: a vote is scored whether or not a paper trade was opened.
Composite weight stays 0. This module does not write signal weights.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from architecture.markets.paper_trade_gates import INDEPENDENT_VOTE_FAMILIES, SHADOW_VOTE_FAMILIES, family_vote_signs

OBS_REL = Path("reports") / "grok" / "PAPER" / "family_vote_observations.jsonl"
SCORECARD_REL = Path("reports") / "grok" / "PAPER" / "weekly_family_vote_scorecard.json"
SCHEMA = "ahos.family_vote_scorecard.v1"

HORIZONS = (("4h", 4 * 3600, 30 * 60), ("24h", 24 * 3600, 60 * 60))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _iso_week(dt: datetime) -> str:
    year, week, _day = dt.isocalendar()
    return f"{year}-W{week:02d}"


def record_family_votes(root: Path, *, ts: str, symbol: str, desk: str, price: float, sigs: list[dict]) -> dict[str, Any] | None:
    """Append signed votes for this cycle. Returns the row, or None when nothing was signed."""
    if not isinstance(price, (int, float)) or isinstance(price, bool) or price <= 0:
        return None
    signed = []
    for vote in family_vote_signs(sigs):
        if vote.get("sign") not in ("LONG", "SHORT"):
            continue
        signed.append(
            {
                "family": vote["family"],
                "sign": vote["sign"],
                "mean_score": vote.get("mean_score"),
                "advisory": bool(vote.get("advisory")),
                "composite_weight": 0.0,
            }
        )
    if not signed:
        return None
    row = {
        "ts": ts,
        "symbol": symbol,
        "desk": desk,
        "price": float(price),
        "votes": signed,
        "counterfactual": True,
        "composite_weight": 0.0,
        "paper_only": True,
    }
    path = Path(root) / OBS_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def _load_rows(root: Path) -> list[dict[str, Any]]:
    path = Path(root) / OBS_REL
    if not path.is_file():
        return []
    rows = []
    seen: set[tuple[str, str]] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        key = (str(row.get("ts")), str(row.get("symbol")))
        if key in seen or _parse(str(row.get("ts") or "")) is None:
            continue
        seen.add(key)
        rows.append(row)
    rows.sort(key=lambda row: str(row.get("ts")))
    return rows


def _tape(rows: list[dict[str, Any]]) -> dict[str, list[tuple[datetime, float]]]:
    tape: dict[str, list[tuple[datetime, float]]] = {}
    for row in rows:
        when = _parse(str(row.get("ts") or ""))
        price = row.get("price")
        symbol = str(row.get("symbol") or "")
        if when is None or not symbol or not isinstance(price, (int, float)) or isinstance(price, bool) or price <= 0:
            continue
        tape.setdefault(symbol, []).append((when, float(price)))
    for symbol in tape:
        tape[symbol].sort(key=lambda item: item[0])
    return tape


def _future_price(points: list[tuple[datetime, float]], start: datetime, horizon_s: int, slack_s: int) -> tuple[float, datetime] | None:
    earliest = start + timedelta(seconds=horizon_s)
    latest = start + timedelta(seconds=horizon_s + slack_s)
    for when, price in points:
        if when < earliest:
            continue
        if when > latest:
            return None
        return price, when
    return None


def _explode(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        when = _parse(str(row.get("ts") or ""))
        if when is None:
            continue
        for vote in row.get("votes") or []:
            if not isinstance(vote, dict) or vote.get("sign") not in ("LONG", "SHORT"):
                continue
            out.append(
                {
                    "ts": when,
                    "symbol": str(row.get("symbol") or ""),
                    "desk": str(row.get("desk") or ""),
                    "price": float(row["price"]),
                    "family": str(vote.get("family") or ""),
                    "sign": vote["sign"],
                }
            )
    return out


def _nonoverlapping(items: list[dict[str, Any]], horizon_s: int) -> list[dict[str, Any]]:
    last: dict[tuple[str, str], datetime] = {}
    kept = []
    for item in sorted(items, key=lambda row: row["ts"]):
        key = (item["symbol"], item["family"])
        prev = last.get(key)
        if prev is not None and (item["ts"] - prev).total_seconds() < horizon_s:
            continue
        last[key] = item["ts"]
        kept.append(item)
    return kept


def _rate(hits: int, misses: int) -> float | None:
    resolved = hits + misses
    if resolved == 0:
        return None
    return round(hits / resolved, 4)


def build_weekly_family_scorecard(root: Path, *, now: datetime | None = None) -> dict[str, Any]:
    now = now or _utc_now()
    week = _iso_week(now)
    rows = [row for row in _load_rows(root) if _iso_week(_parse(str(row.get("ts") or "")) or now) == week]
    tape = _tape(_load_rows(root))
    votes = _explode(rows)
    families: dict[str, Any] = {}
    for family in list(INDEPENDENT_VOTE_FAMILIES) + list(SHADOW_VOTE_FAMILIES):
        cell: dict[str, Any] = {}
        for label, horizon_s, slack_s in HORIZONS:
            hits = misses = ties = pending = no_print = 0
            for item in _nonoverlapping([v for v in votes if v["family"] == family], horizon_s):
                if now < item["ts"] + timedelta(seconds=horizon_s):
                    pending += 1
                    continue
                found = _future_price(tape.get(item["symbol"]) or [], item["ts"], horizon_s, slack_s)
                if found is None:
                    no_print += 1
                    continue
                future, _when = found
                ret = (future - item["price"]) / item["price"]
                if ret == 0:
                    ties += 1
                    continue
                up = ret > 0
                hit = (item["sign"] == "LONG" and up) or (item["sign"] == "SHORT" and not up)
                if hit:
                    hits += 1
                else:
                    misses += 1
            cell[label] = {
                "hits": hits,
                "misses": misses,
                "ties": ties,
                "pending": pending,
                "no_print_in_window": no_print,
                "hit_rate": _rate(hits, misses),
            }
        families[family] = cell
    return {
        "schema": SCHEMA,
        "week": week,
        "generated_at": _iso(now),
        "paper_only": True,
        "counterfactual": True,
        "composite_weight": 0.0,
        "horizons": {
            "4h": "first print in [4h, 4h30m]; overlapping votes inside 4h are not counted twice",
            "24h": "first print in [24h, 25h]; overlapping votes inside 24h are not counted twice",
        },
        "families": families,
        "honesty": "Pending and missing prints are not hits. A zero move is a tie and is outside the rate. This scorecard does not change a weight.",
    }


def export_weekly_family_scorecard(root: Path, *, now: datetime | None = None) -> dict[str, Any]:
    doc = build_weekly_family_scorecard(root, now=now)
    path = Path(root) / SCORECARD_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    return doc
