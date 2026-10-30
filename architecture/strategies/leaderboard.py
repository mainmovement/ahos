"""Pre-register, then write the board. A missing path is not a DSR."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.learning.walk_forward import deflated_sharpe, pbo_cscv, sharpe
from architecture.markets.paper_trade_gates import (
    MIN_AGREEING_FAMILIES,
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
    VOTE_SCORE_FLOOR,
)
from architecture.strategies.library import SPECS
from architecture.strategies.meta_brain import thompson_weights
from architecture.strategies.signals import apply_cost, shadow_round_trips, shadow_round_trips_timed, sign_on_frame
from architecture.strategies.wisdom import review_book

REGISTRY_REL = Path("reports") / "grok" / "PAPER" / "strategy_library_registry.json"
OUT_REL = Path("reports") / "grok" / "PAPER" / "strategy_leaderboard.json"
FOCUS_REL = Path("reports") / "grok" / "PAPER" / "mega11_desk_focus.json"
PREREG_REL = Path("docs") / "prereg" / "MEGA11.yaml"
PREREG_SHA256 = "e4cd3a4ecfa2281013324dfa3d289eb35aecfdf6f6b2f5a39f67cc846ca1873e"
FRESH_AFTER = "2026-10-30T18:43:59Z"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write_registry(root: Path) -> dict[str, Any]:
    path = Path(root) / REGISTRY_REL
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    doc = {
        "schema": "ahos.strategy_library_registry.v1",
        "paper_only": True,
        "registered_at": _utc(),
        "strategies": [row["id"] for row in SPECS],
        "oos_fraction": 0.4,
        "min_oos": 30,
        "dsr_min": 0.95,
        "pbo_max": 0.5,
        "after_fees": True,
        "min_agreeing_families": MIN_AGREEING_FAMILIES,
        "vote_score_floor": VOTE_SCORE_FLOOR,
        "min_expected_profit_to_fee_ratio": MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
        "promotion_rule": (
            "A strategy stays shadow until fresh closes after this stamp "
            "have DSR above 0.95, PBO under 0.5, a walk-forward out-of-sample "
            "window of at least 30, fees deducted, and a red team that survived."
        ),
        "applied_to_live": False,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def gate(
    *,
    dsr: float | None,
    pbo: float | None,
    oos_n: int,
    after_fees: bool,
    fresh: bool,
    red_team_survived: bool,
) -> bool:
    return bool(
        fresh
        and red_team_survived
        and after_fees
        and oos_n >= 30
        and dsr is not None
        and dsr > 0.95
        and pbo is not None
        and pbo < 0.5
    )


def score_path(gross: list[float], alternate: list[float], cost: dict[str, float]) -> dict[str, Any]:
    """Walk-forward on a path this strategy actually produced. Fees are deducted."""
    net = [apply_cost(value, cost["fee_per_side"], cost["slippage_per_side"]) for value in gross]
    alt = [apply_cost(value, cost["fee_per_side"], cost["slippage_per_side"]) for value in alternate]
    split = int(len(net) * 0.6)
    oos = net[split:]
    dsr = deflated_sharpe(oos, 2, [sharpe(oos), sharpe(alt[int(len(alt) * 0.6):] or [0.0])])
    blocks = _blocks(net) 
    blocks_alt = _blocks(alt)
    pbo = pbo_cscv([blocks, blocks_alt]) if blocks and blocks_alt else None
    expectancy = round(sum(oos) / len(oos), 6) if oos else None
    return {
        "closes": len(net),
        "oos_n": len(oos),
        "expectancy_after_fees": expectancy,
        "dsr": dsr,
        "pbo": pbo,
        "after_fees": True,
    }


def _blocks(path: list[float], n_blocks: int = 8) -> list[float] | None:
    if len(path) < n_blocks:
        return None
    size = len(path) // n_blocks
    used = path[-(n_blocks * size):]
    return [sum(used[i * size:(i + 1) * size]) for i in range(n_blocks)]


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


def _scout(root: Path) -> dict[str, Any]:
    path = Path(root) / "reports" / "grok" / "M44" / "arxiv_scout.json"
    present = path.is_file()
    papers = path.read_text(encoding="utf-8").count('"arxiv_id"') if present else 0
    return {
        "sources": ("arXiv q-fin", "SSRN", "GitHub"),
        "arxiv_snapshot_present": present,
        "arxiv_titles_in_snapshot": papers,
        "fetched_this_pass": False,
        "upstream_executed": False,
        "state": "shadow",
        "note": "A scout title is not a strategy until it has the same pre-registered gate.",
    }


def _price(row: dict[str, Any]) -> float | None:
    for key in ("exit_price", "price", "fill_price", "mark_price"):
        value = row.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0:
            return float(value)
    return None


def _day(stamp: str) -> int | None:
    text = str(stamp or "")
    if len(text) < 10 or text[8:10].isdigit() is False:
        return None
    return int(text[8:10])


def _fomc_days(root: Path) -> list[str]:
    path = Path(root) / "reports" / "grok" / "M19" / "macro_calendar.json"
    if not path.is_file():
        return []
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    days = []
    for event in doc.get("events") or []:
        if isinstance(event, dict) and event.get("event") == "FOMC_STATEMENT":
            stamp = str(event.get("at_utc") or "")
            if len(stamp) >= 10:
                days.append(stamp[:10])
    return sorted(set(days))


def _days_until(stamp: str, fomc_days: list[str]) -> int | None:
    day = str(stamp or "")[:10]
    if len(day) < 10:
        return None
    later = [item for item in fomc_days if item > day]
    if not later:
        return None
    from datetime import date
    left = date.fromisoformat(day)
    right = date.fromisoformat(later[0])
    return (right - left).days


def _book_frames(rows: list[dict[str, Any]], fomc_days: list[str]) -> list[dict[str, Any]]:
    """One frame per desk and stored regime. Prices stay inside that bucket."""
    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    ordered = sorted(rows, key=lambda row: str(row.get("closed_at") or row.get("ts") or ""))
    for row in ordered:
        price = _price(row)
        if price is None:
            continue
        desk = str(row.get("desk") or "UNASSIGNED")
        regime = str(row.get("regime") or "UNLABELED")
        stamp = str(row.get("closed_at") or row.get("ts") or "")
        frame = grouped.setdefault((desk, regime), {
            "desk": desk, "regime": regime, "closes": [], "times": [], "days": [],
            "days_until_fomc": [], "by_symbol": {},
        })
        frame["closes"].append(price)
        frame["times"].append(stamp)
        frame["days"].append(_day(stamp) or 0)
        until = _days_until(stamp, fomc_days)
        frame["days_until_fomc"].append(until if until is not None else 99)
        symbol = str(row.get("symbol") or "")
        if symbol:
            frame["by_symbol"].setdefault(symbol, []).append(price)
    frames = []
    for frame in grouped.values():
        names = sorted(frame["by_symbol"], key=lambda name: len(frame["by_symbol"][name]), reverse=True)
        if len(names) >= 2:
            frame["left"] = frame["by_symbol"][names[0]]
            frame["right"] = frame["by_symbol"][names[1]]
            frame["panel"] = {name: frame["by_symbol"][name] for name in names}
        frames.append(frame)
    return frames


def _row_for(spec: dict[str, Any], frame: dict[str, Any]) -> dict[str, Any]:
    cost = spec["cost"]
    desk = str(frame.get("desk") or "UNASSIGNED")
    regime = str(frame.get("regime") or "UNLABELED")
    prices = list(frame.get("closes") or [])
    signs = sign_on_frame(spec["id"], frame)
    base = {
        "id": spec["id"],
        "family": spec["family"],
        "citation": spec["citation"],
        "params": spec["params"],
        "regimes": list(spec["regimes"]),
        "cost": cost,
        "desk": desk,
        "regime": regime,
        "state": "shadow",
        "pass_stats": False,
        "red_team": "NOT_SURVIVED",
        "applied_to_live": False,
        "fresh": False,
        "family_vote": {
            "family": "strategy_shadow",
            "name": spec["id"],
            "composite_weight": 0.0,
            "counts_toward_entry_gate": False,
            "shadow": True,
        },
    }
    if signs is None:
        base.update(closes=0, expectancy_after_fees=None, dsr=None, pbo=None, reason="MISSING_INPUTS")
        return base
    fee = float(cost["fee_per_side"])
    slip = float(cost["slippage_per_side"])
    trips = shadow_round_trips(signs, prices, fee, slip)
    timed = shadow_round_trips_timed(signs, prices, list(frame.get("times") or []), fee, slip)
    fresh_nets = [float(trip["net"]) for trip in timed if str(trip.get("exit_at") or "") > FRESH_AFTER]
    base["fresh_closes"] = len(fresh_nets)
    base["fresh_mean"] = round(sum(fresh_nets) / len(fresh_nets), 6) if fresh_nets else None
    if not trips:
        base.update(closes=0, expectancy_after_fees=None, dsr=None, pbo=None, reason="NO_SHADOW_ROUND_TRIP")
        return base
    scored = score_path(trips, trips, cost)
    base.update(
        closes=scored["closes"],
        expectancy_after_fees=scored["expectancy_after_fees"],
        dsr=scored["dsr"],
        pbo=scored["pbo"],
        reason="SHADOW_LOOKBACK",
        wins=sum(1 for value in trips if value > 0),
        losses=sum(1 for value in trips if value <= 0),
    )
    base["pass_stats"] = gate(
        dsr=scored["dsr"], pbo=scored["pbo"], oos_n=scored["oos_n"],
        after_fees=True, fresh=False, red_team_survived=False,
    )
    return base


def _bar_frames(root: Path) -> list[dict[str, Any]]:
    path = Path(root) / "reports" / "grok" / "PAPER" / "equity_intraday_bars.json"
    if not path.is_file():
        return []
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    frames = []
    by_desk: dict[str, dict[str, list[float]]] = {}
    for symbol, bars in (doc.get("bars") or {}).items():
        if not isinstance(bars, dict):
            continue
        closes = [float(value) for value in (bars.get("closes") or []) if isinstance(value, (int, float))]
        if len(closes) < 5:
            continue
        times = [str(value) for value in (bars.get("times") or [])]
        desk = str(bars.get("desk") or "UNASSIGNED")
        frame = {
            "desk": desk,
            "regime": "UNLABELED",
            "closes": closes,
            "times": times if len(times) == len(closes) else [],
            "days": [_day(stamp) or 0 for stamp in times] if len(times) == len(closes) else [],
            "opens": [float(value) for value in (bars.get("opens") or []) if isinstance(value, (int, float))],
            "highs": [float(value) for value in (bars.get("highs") or []) if isinstance(value, (int, float))],
            "lows": [float(value) for value in (bars.get("lows") or []) if isinstance(value, (int, float))],
        }
        if len(frame["opens"]) != len(closes):
            frame["opens"] = []
        if len(frame["highs"]) != len(closes) or len(frame["lows"]) != len(closes):
            frame["highs"] = []
            frame["lows"] = []
        frames.append(frame)
        by_desk.setdefault(desk, {})[str(symbol)] = closes
    for desk, panel in by_desk.items():
        if len(panel) < 2:
            continue
        ordered = sorted(panel, key=lambda name: len(panel[name]), reverse=True)
        frames.append({
            "desk": desk,
            "regime": "UNLABELED",
            "closes": panel[ordered[0]],
            "times": [],
            "days": [],
            "panel": panel,
            "left": panel[ordered[0]],
            "right": panel[ordered[1]],
        })
    return frames


def _desk_focus(root: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    path = Path(root) / PREREG_REL
    digest = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else ""
    fresh = [row for row in rows if int(row.get("fresh_closes") or 0) > 0]
    us_eu = [row["fresh_mean"] for row in fresh if row.get("desk") in {"US_EQUITIES", "EU_EQUITIES"} and row.get("fresh_mean") is not None]
    neg = [row["fresh_mean"] for row in fresh if row.get("desk") in {"GOLD", "CRYPTO"} and row.get("fresh_mean") is not None]
    rank = sorted(fresh, key=lambda row: (-int(row["fresh_closes"]), str(row["id"]), str(row["desk"])))
    doc = {
        "schema": "ahos.mega11_desk_focus.v1",
        "paper_only": True,
        "prereg_sha256": digest,
        "hash_ok": digest == PREREG_SHA256,
        "fresh_after": FRESH_AFTER,
        "fresh_closes": sum(int(row.get("fresh_closes") or 0) for row in rows),
        "rank": [
            {"id": row["id"], "desk": row["desk"], "regime": row["regime"], "fresh_closes": row["fresh_closes"], "fresh_mean": row["fresh_mean"]}
            for row in rank[:20]
        ],
        "us_eu_mean": round(sum(us_eu) / len(us_eu), 6) if us_eu else None,
        "gold_crypto_mean": round(sum(neg) / len(neg), 6) if neg else None,
        "hypothesis_status": "WAITING_FOR_FRESH" if not fresh else "BELOW_MINIMUM",
        "promoted": False,
        "lookback_excluded": True,
        "applied_to_live": False,
    }
    if digest != PREREG_SHA256:
        doc["hypothesis_status"] = "HASH_MISMATCH"
        doc["rank"] = []
        doc["us_eu_mean"] = None
        doc["gold_crypto_mean"] = None
    out = Path(root) / FOCUS_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return doc


def export_leaderboard(root: Path) -> dict[str, Any]:
    root = Path(root)
    registry = write_registry(root)
    frames = _book_frames(_closes(root), _fomc_days(root))
    frames.extend(_bar_frames(root))
    rows = []
    outcomes: dict[str, tuple[int, int]] = {}
    if not frames:
        for spec in SPECS:
            rows.append(_row_for(spec, {"desk": "UNASSIGNED", "regime": "UNLABELED", "closes": []}))
    else:
        for spec in SPECS:
            wins = losses = 0
            for frame in frames:
                row = _row_for(spec, frame)
                wins += int(row.get("wins") or 0)
                losses += int(row.get("losses") or 0)
                rows.append(row)
            outcomes[spec["id"]] = (wins, losses)
    vote_path = root / "reports" / "grok" / "PAPER" / "strategy_shadow_votes.jsonl"
    vote_path.parent.mkdir(parents=True, exist_ok=True)
    with vote_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps({
                "id": row["id"],
                "desk": row["desk"],
                "regime": row.get("regime"),
                "closes": row["closes"],
                "vote": row["family_vote"],
                "applied_to_live": False,
            }, ensure_ascii=False) + "\n")
    doc = {
        "schema": "ahos.strategy_leaderboard.v1",
        "paper_only": True,
        "generated_at": _utc(),
        "registered_at": registry.get("registered_at"),
        "rows": rows,
        "meta_brain": thompson_weights([spec["id"] for spec in SPECS], outcomes=outcomes),
        "wisdom": review_book(_closes(root)),
        "research": _scout(root),
        "live_promoted": 0,
        "pass_stats": False,
        "applied_to_live": False,
        "strategies_with_closes": len({row["id"] for row in rows if int(row.get("closes") or 0) > 0}),
        "desk_focus": _desk_focus(root, rows),
    }
    out = root / OUT_REL
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc
