"""Shadow entry and gold-exit rules. They do not open, close, or size a paper trade.

The constants below are the pre-registration. A close counts only when both
its open and its close are strictly after the stamp in the registry file.
Historical closes are not a sample. Nothing here writes a live weight.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.markets.multi_market_desks import DESK_SPECS
from architecture.markets.paper_account import LEDGER_REL
from architecture.markets.weekday_session_gate import SYMBOL_VENUE, venue_intervals

REGISTRY_REL = Path("reports") / "grok" / "PAPER" / "mega6_preregistration.json"
SCORE_REL = Path("reports") / "grok" / "PAPER" / "mega6_shadow_score.json"
RED_TEAM_REL = Path("reports") / "grok" / "PAPER" / "mega6_red_team.json"

# Live gates stay in paper_trade_gates.py. These are shadow-only.
SHADOW_VOTE_SCORE_FLOOR = 0.15
SHADOW_MIN_AGREEING_FAMILIES = 3
SPREAD_FRACTION_OF_PUBLISHED = 0.5
PUBLISHED_SPREAD_FALLBACK_PCT = 0.5
VOL_ATR_MAX = 0.02
SESSION_EDGE_MINUTES = 30
GOLD_TRAIL_ARM = 1.0
GOLD_TRAIL_GIVEBACK = 0.5
GOLD_TIME_STOP_S = 6 * 3600
MIN_FRESH = 30
PROBABILITY_SOURCE = "SIGNED_COMPOSITE_LINEAR"

# Frozen from reports/grok/PAPER/edge_decomposition.json at 2026-10-30T14:08:32Z.
# Not refit when later closes arrive.
ENTRIES_DESKS = (
    "ASIA_EQUITIES",
    "CRYPTO",
    "CRYPTO_FUTURES",
    "FOREX",
    "OIL",
    "PB_TOKEN",
    "US_EQUITIES",
)


def _utc(moment: datetime | None = None) -> str:
    now = moment or datetime.now(timezone.utc)
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def published_spread_cap(desk: str) -> float:
    spec = DESK_SPECS.get(desk, {})
    raw = spec.get("max_spread_pct", PUBLISHED_SPREAD_FALLBACK_PCT)
    return float(raw) * SPREAD_FRACTION_OF_PUBLISHED


def predicted_probability(composite: float, side: str) -> float:
    """A fixed map from the signed composite. It is not a calibrated probability."""
    direction = 1.0 if str(side).upper() == "LONG" else -1.0
    raw = 0.5 + 0.4 * float(composite) * direction
    return round(min(0.95, max(0.05, raw)), 4)


def session_edge(symbol: str, moment: datetime) -> dict[str, Any]:
    """First and last 30 minutes of the published venue session. Crypto has none."""
    venue = SYMBOL_VENUE.get(symbol)
    if venue is None:
        return {"applicable": False, "reason": "NO_CASH_SESSION", "near_edge": False}
    now = moment.astimezone(timezone.utc)
    current = next(((start, end) for start, end in venue_intervals(venue, now) if start <= now < end), None)
    if current is None:
        return {"applicable": True, "inside": False, "near_edge": False, "minutes_from_edge": None}
    start, end = current
    edge = min((now - start).total_seconds(), (end - now).total_seconds()) / 60.0
    return {
        "applicable": True,
        "inside": True,
        "minutes_from_edge": round(edge, 2),
        "near_edge": edge < SESSION_EDGE_MINUTES,
    }


def _agree_abs_min(vote_audit: dict[str, Any] | None) -> float | None:
    if not isinstance(vote_audit, dict):
        return None
    scores = []
    for row in vote_audit.get("votes") or []:
        if not isinstance(row, dict) or row.get("vote") != "AGREE":
            continue
        mean = row.get("mean_score")
        if isinstance(mean, bool) or not isinstance(mean, (int, float)):
            continue
        scores.append(abs(float(mean)))
    if not scores:
        return None
    return round(min(scores), 4)


def stamp_open(
    *,
    composite: float,
    side: str,
    vote_audit: dict[str, Any] | None,
    spread_pct: float | None,
    atr_pct: float | None,
    symbol: str,
    moment: datetime,
    fee_rate: float,
    desk: str,
) -> dict[str, Any]:
    """Features for a later shadow score. Calling this does not block the open."""
    agree = None
    if isinstance(vote_audit, dict) and isinstance(vote_audit.get("agreeing_families"), int):
        agree = int(vote_audit["agreeing_families"])
    spread = None if isinstance(spread_pct, bool) or not isinstance(spread_pct, (int, float)) else float(spread_pct)
    atr = None if isinstance(atr_pct, bool) or not isinstance(atr_pct, (int, float)) else float(atr_pct)
    features = {
        "desk": desk,
        "agreeing_families": agree,
        "agree_abs_min": _agree_abs_min(vote_audit),
        "spread_pct": None if spread is None else round(spread, 4),
        "atr_pct": None if atr is None else round(atr, 6),
        "session": session_edge(symbol, moment),
        "fee_rate": float(fee_rate),
        "predicted_probability": predicted_probability(composite, side),
        "probability_source": PROBABILITY_SOURCE,
        "calibrated": False,
        "applied_to_decision": False,
    }
    features["filters"] = filter_verdicts(features)
    return features


def filter_verdicts(features: dict[str, Any]) -> dict[str, str]:
    """KEEP, DROP, or UNEVALUABLE. UNEVALUABLE is not a pass."""
    floor = features.get("agree_abs_min")
    families = features.get("agreeing_families")
    spread = features.get("spread_pct")
    atr = features.get("atr_pct")
    session = features.get("session") if isinstance(features.get("session"), dict) else {}
    desk = str(features.get("desk") or "")
    out = {
        "VOTE_SCORE_FLOOR_0_15": "UNEVALUABLE" if floor is None else ("DROP" if float(floor) < SHADOW_VOTE_SCORE_FLOOR else "KEEP"),
        "THREE_FAMILIES": "UNEVALUABLE" if not isinstance(families, int) else ("DROP" if families < SHADOW_MIN_AGREEING_FAMILIES else "KEEP"),
        "SPREAD_HALF_PUBLISHED": "UNEVALUABLE" if not isinstance(spread, (int, float)) else (
            "DROP" if float(spread) > published_spread_cap(desk) else "KEEP"
        ),
        "VOL_ATR_ABOVE_0_02": "UNEVALUABLE" if not isinstance(atr, (int, float)) else (
            "DROP" if float(atr) > VOL_ATR_MAX else "KEEP"
        ),
    }
    if session.get("applicable") is False:
        out["SESSION_EDGE_30M"] = "KEEP"
    elif session.get("near_edge") is True:
        out["SESSION_EDGE_30M"] = "DROP"
    elif session.get("inside") is True and session.get("near_edge") is False:
        out["SESSION_EDGE_30M"] = "KEEP"
    else:
        out["SESSION_EDGE_30M"] = "UNEVALUABLE"
    named = [out[key] for key in out]
    if "DROP" in named:
        out["ALL_ENTRY_FILTERS"] = "DROP"
    elif "UNEVALUABLE" in named:
        out["ALL_ENTRY_FILTERS"] = "UNEVALUABLE"
    else:
        out["ALL_ENTRY_FILTERS"] = "KEEP"
    return out


def registry_params() -> dict[str, Any]:
    return {
        "shadow_vote_score_floor": SHADOW_VOTE_SCORE_FLOOR,
        "live_vote_score_floor_unchanged": 0.05,
        "shadow_min_agreeing_families": SHADOW_MIN_AGREEING_FAMILIES,
        "live_min_agreeing_families_unchanged": 2,
        "spread_fraction_of_published": SPREAD_FRACTION_OF_PUBLISHED,
        "published_spread_fallback_pct": PUBLISHED_SPREAD_FALLBACK_PCT,
        "vol_atr_max": VOL_ATR_MAX,
        "session_edge_minutes": SESSION_EDGE_MINUTES,
        "entries_desks": list(ENTRIES_DESKS),
        "entries_desks_source": "edge_decomposition.json generated_at 2026-10-30T14:08:32Z",
        "gold_trail_arm_stop_mult": GOLD_TRAIL_ARM,
        "gold_trail_giveback_stop_mult": GOLD_TRAIL_GIVEBACK,
        "gold_time_stop_s": GOLD_TIME_STOP_S,
        "live_time_stop_unchanged": "12h and a small move, or 24h",
        "probability_source": PROBABILITY_SOURCE,
        "probability_calibrated": False,
        "applied_to_live_weights": False,
        "min_fresh_closes": MIN_FRESH,
    }


def write_registry(root: Path, *, moment: datetime | None = None) -> dict[str, Any]:
    """Create the stamp once. A second call returns the file and does not move it."""
    path = root / REGISTRY_REL
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    doc = {
        "schema": "ahos.mega6_preregistration.v1",
        "paper_only": True,
        "registered_at": _utc(moment),
        "params": registry_params(),
        "scoring_rule": "A close counts only when opened_at and closed_at are both after registered_at.",
        "applied_to_live_weights": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def _load_registry(root: Path) -> dict[str, Any] | None:
    path = root / REGISTRY_REL
    if not path.is_file():
        return None
    doc = json.loads(path.read_text(encoding="utf-8"))
    return doc if isinstance(doc, dict) else None


def note_gold_path(root: Path, pos: dict[str, Any], price: float, now_ts: float) -> None:
    """Record a shadow exit price. The live reason is chosen by the caller."""
    registry = _load_registry(root)
    if registry is None:
        return
    opened = pos.get("opened_at")
    registered = registry.get("registered_at")
    if not isinstance(opened, str) or not isinstance(registered, str) or opened <= registered:
        return
    if pos.get("desk") != "GOLD":
        return
    if not isinstance(price, (int, float)) or isinstance(price, bool) or price <= 0:
        return
    entry = float(pos["entry_price"])
    direction = 1.0 if pos.get("side") == "LONG" else -1.0
    move = (float(price) - entry) / entry * direction
    prior = pos.get("shadow_mfe")
    mfe = move if not isinstance(prior, (int, float)) else max(float(prior), move)
    pos["shadow_mfe"] = mfe
    stop = float(pos.get("stop_pct") or 0)
    if (
        pos.get("shadow_trail_exit_price") is None
        and stop > 0
        and mfe >= GOLD_TRAIL_ARM * stop
        and (mfe - move) >= GOLD_TRAIL_GIVEBACK * stop
    ):
        pos["shadow_trail_exit_price"] = float(price)
        pos["shadow_trail_at"] = _utc(datetime.fromtimestamp(now_ts, tz=timezone.utc))
    opened_ts = pos.get("opened_ts")
    if (
        pos.get("shadow_time_exit_price") is None
        and isinstance(opened_ts, (int, float))
        and not isinstance(opened_ts, bool)
        and now_ts - float(opened_ts) >= GOLD_TIME_STOP_S
    ):
        pos["shadow_time_exit_price"] = float(price)
        pos["shadow_time_at"] = _utc(datetime.fromtimestamp(now_ts, tz=timezone.utc))


def _alternate_pnl(row: dict[str, Any], exit_price: float) -> float | None:
    features = row.get("entry_features") if isinstance(row.get("entry_features"), dict) else {}
    fee = features.get("fee_rate")
    entry = row.get("entry_price")
    qty = row.get("qty")
    side = row.get("side")
    if side not in ("LONG", "SHORT"):
        return None
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in (fee, entry, qty, exit_price)):
        return None
    direction = 1.0 if side == "LONG" else -1.0
    gross = (float(exit_price) - float(entry)) * float(qty) * direction
    fees = abs(float(exit_price) * float(qty) * float(fee)) + abs(float(entry) * float(qty) * float(fee))
    funding = row.get("funding_usd")
    extra = float(funding) if isinstance(funding, (int, float)) and not isinstance(funding, bool) else 0.0
    return round(gross - fees + extra, 4)


def _after(stamp: str | None, registered: str) -> bool:
    return isinstance(stamp, str) and stamp > registered


def _closes(root: Path) -> list[dict[str, Any]]:
    path = root / LEDGER_REL
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("event") == "CLOSE" and isinstance(row.get("realized_pnl_usd"), (int, float)):
            rows.append(row)
    return rows


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _rule_pnl(row: dict[str, Any], rule: str) -> tuple[str, float | None]:
    """Return the shadow verdict and the pnl used if the rule is evaluable."""
    if rule in ("GOLD_TRAIL_HALF_STOP", "GOLD_TIME_STOP_6H"):
        if row.get("desk") != "GOLD" or row.get("partial") is True:
            return "OUT_OF_SCOPE", None
        price_key = "shadow_trail_exit_price" if rule == "GOLD_TRAIL_HALF_STOP" else "shadow_time_exit_price"
        price = row.get(price_key)
        if price is None:
            pnl = row.get("realized_pnl_usd")
            return "KEEP", float(pnl) if isinstance(pnl, (int, float)) else None
        alt = _alternate_pnl(row, float(price))
        if alt is None:
            return "UNEVALUABLE", None
        return "DROP_EARLY", alt
    features = row.get("entry_features") if isinstance(row.get("entry_features"), dict) else None
    if features is None or str(row.get("desk") or "") not in ENTRIES_DESKS:
        return "OUT_OF_SCOPE", None
    verdicts = features.get("filters") if isinstance(features.get("filters"), dict) else filter_verdicts(features)
    verdict = verdicts.get(rule)
    if verdict == "KEEP":
        return "KEEP", float(row["realized_pnl_usd"])
    if verdict == "DROP":
        return "DROP", 0.0
    return "UNEVALUABLE", None


def _score_rule(rows: list[dict[str, Any]], rule: str) -> dict[str, Any]:
    live: list[float] = []
    shadow: list[float] = []
    unevaluable = 0
    for row in rows:
        verdict, pnl = _rule_pnl(row, rule)
        if verdict in ("OUT_OF_SCOPE", "UNEVALUABLE") or pnl is None:
            if verdict == "UNEVALUABLE":
                unevaluable += 1
            continue
        live.append(float(row["realized_pnl_usd"]))
        shadow.append(pnl)
    n = len(live)
    return {
        "rule": rule,
        "fresh_evaluable": n,
        "unevaluable": unevaluable,
        "live_expectancy_usd": _mean(live),
        "shadow_expectancy_usd": _mean(shadow),
        "pass_stats": False,
        "red_team": "NOT_SURVIVED",
        "reasons": ["AWAITING_FRESH_CLOSES"] if n < MIN_FRESH else ["RED_TEAM_ABSENT", "FRESH_SAMPLE_NOT_PROMOTED"],
        "applied_to_live_weights": False,
    }


RULES = (
    "VOTE_SCORE_FLOOR_0_15",
    "THREE_FAMILIES",
    "SPREAD_HALF_PUBLISHED",
    "VOL_ATR_ABOVE_0_02",
    "SESSION_EDGE_30M",
    "ALL_ENTRY_FILTERS",
    "GOLD_TRAIL_HALF_STOP",
    "GOLD_TIME_STOP_6H",
)


def book_expectancy(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cells: dict[str, list[float]] = {}
    for row in rows:
        cells.setdefault(str(row.get("desk") or "UNKNOWN"), []).append(float(row["realized_pnl_usd"]))
    out = []
    for desk in sorted(cells):
        sample = cells[desk]
        out.append({
            "desk": desk,
            "closes": len(sample),
            "live_expectancy_usd": _mean(sample),
            "shadow_expectancy_usd": None,
            "shadow_reason": "AWAITING_FRESH_CLOSES",
        })
    return out


def fresh_desk_expectancy(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Paired live vs the combined entry filter, plus gold exit rules on GOLD."""
    by_desk: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_desk.setdefault(str(row.get("desk") or "UNKNOWN"), []).append(row)
    out = []
    for desk in sorted(by_desk):
        sample = by_desk[desk]
        rule = "ALL_ENTRY_FILTERS" if desk in ENTRIES_DESKS else None
        entry = _score_rule(sample, rule) if rule else None
        trail = _score_rule(sample, "GOLD_TRAIL_HALF_STOP") if desk == "GOLD" else None
        timed = _score_rule(sample, "GOLD_TIME_STOP_6H") if desk == "GOLD" else None
        out.append({
            "desk": desk,
            "fresh_closes": len(sample),
            "entry_filter": entry,
            "gold_trail": trail,
            "gold_time_stop": timed,
        })
    return out


def evaluate(root: Path) -> dict[str, Any]:
    registry = _load_registry(root)
    if registry is None:
        raise FileNotFoundError(REGISTRY_REL.as_posix())
    registered = str(registry.get("registered_at") or "")
    closes = _closes(root)
    fresh = [
        row for row in closes
        if _after(row.get("opened_at") if isinstance(row.get("opened_at"), str) else None, registered)
        and _after(row.get("closed_at") if isinstance(row.get("closed_at"), str) else row.get("ts"), registered)
    ]
    rules = [_score_rule(fresh, rule) for rule in RULES]
    for row in rules:
        row["pass_stats"] = False
        row["red_team"] = "NOT_SURVIVED"
        if "SURVIVED_RED_TEAM" in row["reasons"]:
            row["reasons"] = [reason for reason in row["reasons"] if reason != "SURVIVED_RED_TEAM"]
    doc = {
        "schema": "ahos.mega6_shadow_score.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "registered_at": registered,
        "book_closes": len(closes),
        "fresh_closes": len(fresh),
        "applied_to_live_weights": False,
        "promoted": False,
        "book": book_expectancy(closes),
        "fresh_by_desk": fresh_desk_expectancy(fresh),
        "rules": rules,
    }
    path = root / SCORE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    red = {
        "schema": "ahos.mega6_red_team.v1",
        "paper_only": True,
        "generated_at": doc["generated_at"],
        "registered_at": registered,
        "verdict": "NOT_SURVIVED",
        "survived_red_team": False,
        "rules": [
            {"rule": row["rule"], "verdict": "NOT_SURVIVED", "pass_stats": False, "reasons": row["reasons"]}
            for row in rules
        ],
    }
    (root / RED_TEAM_REL).write_text(json.dumps(red, indent=2) + "\n", encoding="utf-8")
    return doc

