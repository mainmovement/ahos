"""Shadow fixes registered in docs/prereg/MEGA12.yaml. Nothing here opens a trade.

A close is fresh only when it was opened and closed after the registration
commit. Older rows are tagged and then left out of the score.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.markets.paper_trade_gates import (
    MIN_AGREEING_FAMILIES,
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
    VOTE_SCORE_FLOOR,
    family_vote_signs,
)

PREREG_REL = Path("docs") / "prereg" / "MEGA12.yaml"
OUT_REL = Path("reports") / "grok" / "PAPER" / "mega12_shadow.json"
PREREG_SHA256 = "82e5e1b676cc30476a648ce9f43a655a51b38aa5170bd4c48116d6ae0020ff32"
FRESH_AFTER = "2026-10-30T19:10:04Z"
HIGH_IMPACT = (
    "FOMC_STATEMENT",
    "EIA_WPSR",
    "ECB_GOV_COUNCIL",
    "BOE_MPC_DECISION",
    "BOJ_MPM_DECISION",
    "OPEC_MINISTERIAL",
)
N_VARIANTS = 9


def _dt(stamp: str | None) -> datetime | None:
    if not isinstance(stamp, str) or len(stamp) < 20:
        return None
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None


def _closes(root: Path) -> list[dict[str, Any]]:
    path = Path(root) / "reports" / "grok" / "PAPER" / "paper_trades.jsonl"
    if not path.is_file():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if '"CLOSE"' not in line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(row, dict) and row.get("event") == "CLOSE":
            rows.append(row)
    return rows


def load_events(root: Path) -> list[datetime]:
    path = Path(root) / "reports" / "grok" / "M19" / "macro_calendar.json"
    if not path.is_file():
        return []
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    found = []
    for event in doc.get("events") or []:
        if not isinstance(event, dict) or event.get("event") not in HIGH_IMPACT:
            continue
        moment = _dt(event.get("at_utc") if isinstance(event.get("at_utc"), str) else None)
        if moment is not None:
            found.append(moment)
    return found


def lag_minutes(opened: str | None, events: list[datetime]) -> float | None:
    moment = _dt(opened)
    if moment is None or not events:
        return None
    prior = [event for event in events if event <= moment]
    if not prior:
        return None
    return (moment - max(prior)).total_seconds() / 60.0


def _signals(row: dict[str, Any]) -> list[dict[str, Any]]:
    brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
    return [item for item in (brain.get("signals") or []) if isinstance(item, dict)]


def non_news_agrees(row: dict[str, Any]) -> int:
    side = str(row.get("side") or "")
    agree = 0
    for vote in family_vote_signs(_signals(row)):
        if vote.get("family") in {None, "news"} or vote.get("shadow"):
            continue
        if vote.get("sign") == side:
            agree += 1
    return agree


def mtf_agrees(row: dict[str, Any]) -> bool | None:
    members = [item for item in _signals(row) if item.get("name") == "mtf_trend"]
    if not members:
        return None
    scores = []
    for item in members:
        score = item.get("score")
        if item.get("available") and isinstance(score, (int, float)) and not isinstance(score, bool):
            scores.append(float(score))
    if not scores:
        return False
    mean = sum(scores) / len(scores)
    if abs(mean) < VOTE_SCORE_FLOOR:
        return False
    return (mean > 0 and row.get("side") == "LONG") or (mean < 0 and row.get("side") == "SHORT")


def _pnl(row: dict[str, Any]) -> float | None:
    value = row.get("realized_pnl_usd")
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def cooldown_skips(row: dict[str, Any], events: list[datetime], window_min: int) -> bool | None:
    lag = lag_minutes(row.get("opened_at") if isinstance(row.get("opened_at"), str) else None, events)
    if lag is None:
        return None
    if lag > window_min:
        return False
    if non_news_agrees(row) >= 2:
        return False
    return True


def fade_skips(row: dict[str, Any], events: list[datetime]) -> bool | None:
    lag = lag_minutes(row.get("opened_at") if isinstance(row.get("opened_at"), str) else None, events)
    if lag is None:
        return None
    return lag <= 15


def _skip_stats(rows: list[dict[str, Any]], skipped_flags: list[bool | None]) -> dict[str, Any]:
    skipped = [row for row, flag in zip(rows, skipped_flags) if flag is True and _pnl(row) is not None]
    pnls = [_pnl(row) for row in skipped]
    losses = [value for value in pnls if value is not None and value < 0]
    wins = [value for value in pnls if value is not None and value > 0]
    known = [value for value in pnls if value is not None]
    return {
        "trades_skipped": len(skipped),
        "loss_avoided_usd": round(-sum(losses), 6) if losses else 0.0 if skipped else None,
        "winners_forgone_usd": round(sum(wins), 6) if wins else 0.0 if skipped else None,
        "net_delta_usd": round(-sum(known), 6) if known else None,
        "applied_to_live": False,
    }


def _fee_net(row: dict[str, Any], exit_price: float, fraction: float = 1.0) -> float | None:
    features = row.get("entry_features") if isinstance(row.get("entry_features"), dict) else {}
    fee = features.get("fee_rate")
    entry = row.get("entry_price")
    qty = row.get("qty")
    side = row.get("side")
    if side not in ("LONG", "SHORT"):
        return None
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in (fee, entry, qty)):
        return None
    if entry <= 0 or qty <= 0:
        return None
    direction = 1.0 if side == "LONG" else -1.0
    piece = float(qty) * fraction
    gross = (float(exit_price) - float(entry)) * piece * direction
    fees = abs(float(exit_price) * piece * float(fee)) + abs(float(entry) * piece * float(fee))
    funding = row.get("funding_usd")
    extra = float(funding) * fraction if isinstance(funding, (int, float)) and not isinstance(funding, bool) else 0.0
    return gross - fees + extra


def _atr(row: dict[str, Any]) -> float | None:
    features = row.get("entry_features") if isinstance(row.get("entry_features"), dict) else {}
    atr = features.get("atr_pct")
    if isinstance(atr, bool) or not isinstance(atr, (int, float)) or atr <= 0:
        return None
    return float(atr)


def gold_atr_pnl(row: dict[str, Any]) -> float | None:
    if row.get("desk") != "GOLD":
        return None
    atr = _atr(row)
    mfe = row.get("mfe")
    entry = row.get("entry_price")
    fill = row.get("fill_price")
    if atr is None or not isinstance(mfe, (int, float)) or isinstance(mfe, bool):
        return None
    if not isinstance(entry, (int, float)) or not isinstance(fill, (int, float)) or isinstance(entry, bool):
        return None
    direction = 1.0 if row.get("side") == "LONG" else -1.0
    move = (float(fill) - float(entry)) / float(entry) * direction
    if float(mfe) >= atr and (float(mfe) - move) >= atr:
        trail = float(entry) * (1.0 + direction * (float(mfe) - atr))
        return _fee_net(row, trail)
    return _pnl(row)


def gold_partial_pnl(row: dict[str, Any]) -> float | None:
    if row.get("desk") != "GOLD":
        return None
    atr = _atr(row)
    mfe = row.get("mfe")
    entry = row.get("entry_price")
    fill = row.get("fill_price")
    if atr is None or not isinstance(mfe, (int, float)) or isinstance(mfe, bool):
        return None
    if not isinstance(entry, (int, float)) or not isinstance(fill, (int, float)) or isinstance(entry, bool):
        return None
    if float(mfe) < atr:
        return _pnl(row)
    direction = 1.0 if row.get("side") == "LONG" else -1.0
    at_r = float(entry) * (1.0 + direction * atr)
    first = _fee_net(row, at_r, 0.5)
    rest = _fee_net(row, float(fill), 0.5)
    if first is None or rest is None:
        return None
    return round(first + rest, 6)


def gold_time_pnl(row: dict[str, Any]) -> float | None:
    if row.get("desk") != "GOLD":
        return None
    opened = _dt(row.get("opened_at") if isinstance(row.get("opened_at"), str) else None)
    closed = _dt(row.get("closed_at") if isinstance(row.get("closed_at"), str) else None)
    if opened is None or closed is None:
        return None
    if (closed - opened).total_seconds() < 21600:
        return _pnl(row)
    price = row.get("shadow_time_exit_price")
    if not isinstance(price, (int, float)) or isinstance(price, bool):
        return None
    return _fee_net(row, float(price))


def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _gold_block(rows: list[dict[str, Any]]) -> dict[str, Any]:
    rules = {
        "gold_atr_trail": [gold_atr_pnl(row) for row in rows],
        "gold_time_stop": [gold_time_pnl(row) for row in rows],
        "gold_partial_1r": [gold_partial_pnl(row) for row in rows],
    }
    scored = []
    for name, pnls in rules.items():
        known = [value for value in pnls if value is not None]
        live = [_pnl(row) for row, alt in zip(rows, pnls) if alt is not None and _pnl(row) is not None]
        scored.append({
            "rule": name,
            "fresh_evaluable": len(known),
            "shadow_mean_usd": _mean(known),
            "live_mean_usd": _mean([value for value in live if value is not None]),
            "applied_to_live": False,
        })
    eligible = [row for row in scored if row["fresh_evaluable"] and row["shadow_mean_usd"] is not None]
    changed = [row for row in eligible if row["shadow_mean_usd"] != row["live_mean_usd"]]
    pick = max(changed, key=lambda row: row["shadow_mean_usd"])["rule"] if changed else None
    return {"rules": scored, "pick": pick, "applied_to_live": False}


def _dominant_mtf(row: dict[str, Any]) -> bool:
    brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
    contrib = {}
    for item in brain.get("contributions") or []:
        if isinstance(item, dict) and isinstance(item.get("signal"), str) and isinstance(item.get("contribution"), (int, float)):
            contrib[item["signal"]] = abs(float(item["contribution"]))
    if not contrib:
        return False
    return max(contrib, key=contrib.get) == "mtf_trend"


def _entry_block(rows: list[dict[str, Any]]) -> dict[str, Any]:
    kept = []
    dropped = 0
    unevaluable = 0
    for row in rows:
        trend = mtf_agrees(row)
        if trend is None:
            unevaluable += 1
            continue
        if trend and non_news_agrees(row) >= 1:
            kept.append(row)
        else:
            dropped += 1
    dominant = sum(1 for row in kept if _dominant_mtf(row))
    return {
        "fresh_kept": len(kept),
        "fresh_dropped": dropped,
        "unevaluable": unevaluable,
        "mtf_trend_dominant_share_after": None if not kept else round(dominant / len(kept), 4),
        "applied_to_live": False,
    }


def _tilt(rows: list[dict[str, Any]]) -> dict[str, Any]:
    buckets: dict[str, list[float]] = {}
    for row in rows:
        pnl = _pnl(row)
        if pnl is None:
            continue
        buckets.setdefault(str(row.get("desk") or "UNKNOWN"), []).append(pnl)
    means = {desk: _mean(values) for desk, values in buckets.items()}
    positive = {desk: mean for desk, mean in means.items() if mean is not None and mean > 0}
    total = sum(positive.values())
    weights = {desk: round(mean / total, 6) for desk, mean in positive.items()} if total else {}
    return {
        "fresh_means_usd": means,
        "shadow_weights": weights,
        "negative_desks_get_zero": sorted(desk for desk, mean in means.items() if mean is not None and mean <= 0),
        "floors_unchanged": {
            "min_agreeing_families": MIN_AGREEING_FAMILIES,
            "vote_score_floor": VOTE_SCORE_FLOOR,
            "min_expected_profit_to_fee_ratio": MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
        },
        "applied_to_live": False,
    }


def _fresh(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kept = []
    for row in rows:
        opened = row.get("opened_at") if isinstance(row.get("opened_at"), str) else ""
        closed = row.get("closed_at") if isinstance(row.get("closed_at"), str) else ""
        if opened > FRESH_AFTER and closed > FRESH_AFTER:
            kept.append(row)
    return kept


def _news_block(rows: list[dict[str, Any]], events: list[datetime], window: int, fade: bool = False) -> dict[str, Any]:
    flags = [fade_skips(row, events) if fade else cooldown_skips(row, events, window) for row in rows]
    stats = _skip_stats(rows, flags)
    stats["window_min"] = 15 if fade else window
    stats["unevaluable"] = sum(1 for flag in flags if flag is None)
    return stats


def evaluate(root: Path, rows: list[dict[str, Any]] | None = None, events: list[datetime] | None = None) -> dict[str, Any]:
    root = Path(root)
    prereg = root / PREREG_REL
    digest = hashlib.sha256(prereg.read_bytes()).hexdigest() if prereg.is_file() else ""
    book = _closes(root) if rows is None else rows
    calendar = load_events(root) if events is None else events
    fresh = _fresh(book)
    news = {
        "news_cooldown_15": _news_block(fresh, calendar, 15),
        "news_cooldown_30": _news_block(fresh, calendar, 30),
        "news_cooldown_60": _news_block(fresh, calendar, 60),
        "fade_first_spike_15": _news_block(fresh, calendar, 15, fade=True),
    }
    gold = _gold_block([row for row in fresh if row.get("desk") == "GOLD"])
    entry = _entry_block(fresh)
    tilt = _tilt(fresh)
    helping = None
    best = 0.0
    for name, block in news.items():
        delta = block.get("net_delta_usd")
        if block.get("trades_skipped") and isinstance(delta, (int, float)) and delta > best:
            best = float(delta)
            helping = name
    picked = next((row for row in gold.get("rules") or [] if row.get("rule") == gold.get("pick")), None)
    if picked and picked.get("shadow_mean_usd") is not None and picked.get("live_mean_usd") is not None:
        gain = float(picked["shadow_mean_usd"]) - float(picked["live_mean_usd"])
        if gain > best:
            helping = gold["pick"]
    doc = {
        "schema": "ahos.mega12_shadow.v1",
        "paper_only": True,
        "prereg_sha256": digest,
        "hash_ok": digest == PREREG_SHA256,
        "fresh_after": FRESH_AFTER,
        "fresh_closes": len(fresh),
        "n_variants": N_VARIANTS,
        "news": news,
        "gold": gold,
        "entry": entry,
        "tilt": tilt,
        "lookback_news_cooldown_60": _news_block(book, calendar, 60),
        "helping": helping,
        "promoted": False,
        "applied_to_live": False,
        "pass_stats": False,
        "red_team": "NOT_SURVIVED",
    }
    if digest != PREREG_SHA256:
        doc["news"] = {}
        doc["gold"] = {"pick": None, "rules": []}
        doc["entry"] = {}
        doc["tilt"] = {"applied_to_live": False, "shadow_weights": {}}
        doc["helping"] = None
        doc["lookback_news_cooldown_60"] = {}
        doc["hypothesis_status"] = "HASH_MISMATCH"
    else:
        doc["hypothesis_status"] = "WAITING_FOR_FRESH" if not fresh else "BELOW_MINIMUM"
    return doc


def export_shadow(root: Path) -> dict[str, Any]:
    doc = evaluate(root)
    path = Path(root) / OUT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return doc
