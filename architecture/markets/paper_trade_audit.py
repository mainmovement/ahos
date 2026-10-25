"""M13 / M42 — Audit closed paper trades for fee, slippage, OMS, and ledger honesty (PAPER_ONLY)."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.markets.paper_account import LEDGER_REL, load_paper_trades
from architecture.markets.paper_trader import INSTRUMENTS
from architecture.markets.weekday_session_gate import session_report

PAPER_ONLY = True
MISSION_LEDGER_REL = Path("data") / "mission_ledger" / "mission_ledger.jsonl"


def _parse_iso(ts: str) -> datetime | None:
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _expected_fill(quote: float, side: str, slip: float) -> float:
    if side == "LONG":
        return quote * (1.0 + slip)
    return quote * (1.0 - slip)


def audit_paper_trades_jsonl(root: Path) -> dict[str, Any]:
    path = root / LEDGER_REL
    issues: list[str] = []
    opens = 0
    closes = 0
    skips = 0
    if not path.is_file():
        return {
            "paper_only": True,
            "trades_file": str(LEDGER_REL).replace("\\", "/"),
            "opens": 0,
            "closes": 0,
            "skips": 0,
            "issues": [],
            "status": "GREEN",
            "note_fa": "هنوز معاملهٔ بسته‌ای ثبت نشده — حساب ۱۰۰ دلار بدون تغییر.",
        }
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            issues.append(f"line{i}:invalid_json")
            continue
        ev = row.get("event")
        sym = row.get("symbol")
        if ev == "SKIP":
            skips += 1
            continue
        if ev == "OPEN":
            opens += 1
            oms_ok = row.get("oms") == "ACCEPTED_PAPER" or (
                bool(row.get("ledger_hash")) and row.get("fill_price") is not None and row.get("notional_usd")
            )
            if not oms_ok:
                issues.append(f"line{i}:{sym}:oms_not_accepted_paper")
            desk, fee, slip = INSTRUMENTS.get(str(sym), ("?", 0.001, 0.0005))
            fp = row.get("fill_price")
            qp = row.get("quote_price")
            side = row.get("side")
            if isinstance(fp, (int, float)) and isinstance(qp, (int, float)) and side in ("LONG", "SHORT"):
                exp = _expected_fill(float(qp), side, float(slip))
                if abs(fp - exp) > max(1e-6, exp * 1e-4):
                    issues.append(f"line{i}:{sym}:fill_slippage_mismatch")
            fee_usd = row.get("fee_usd")
            notional = row.get("notional_usd")
            if isinstance(fee_usd, (int, float)) and isinstance(notional, (int, float)):
                exp_fee = float(notional) * float(fee)
                if abs(float(fee_usd) - exp_fee) > max(1e-6, exp_fee * 0.02):
                    issues.append(f"line{i}:{sym}:entry_fee_mismatch")
        elif ev == "CLOSE":
            closes += 1
            if row.get("realized_pnl_usd") is None:
                issues.append(f"line{i}:{sym}:close_missing_realized_pnl")
            if not row.get("closed_at"):
                issues.append(f"line{i}:{sym}:close_missing_closed_at")
            fees = row.get("fees_usd")
            if not isinstance(fees, (int, float)) or float(fees) < 0:
                issues.append(f"line{i}:{sym}:close_missing_fees")
    closed_trades = load_paper_trades(root)
    if closes != len(closed_trades):
        issues.append(f"close_count_mismatch:jsonl={closes}:ledger={len(closed_trades)}")
    status = "GREEN" if not issues else "AMBER"
    return {
        "paper_only": True,
        "trades_file": str(LEDGER_REL).replace("\\", "/"),
        "opens": opens,
        "closes": closes,
        "closed_with_pnl": len(closed_trades),
        "skips": skips,
        "issues": issues[:40],
        "status": status,
        "note_fa": (
            f"ممیزی {opens} باز و {closes} بسته — "
            + ("بدون ایراد ساختاری." if status == "GREEN" else f"{len(issues)} نکتهٔ ساختاری (بدون معاملهٔ زنده).")
        ),
    }


def audit_mission_ledger_paper_refs(root: Path) -> dict[str, Any]:
    p = root / MISSION_LEDGER_REL
    hits = 0
    if not p.is_file():
        return {"ledger_present": False, "paper_trader_refs": 0, "status": "AMBER", "note_fa": "ledger هنوز خالی است."}
    pat = re.compile(r"PAPER_TRADER|paper_trades\.jsonl", re.I)
    for line in p.read_text(encoding="utf-8").splitlines():
        if pat.search(line):
            hits += 1
    return {
        "ledger_present": True,
        "paper_trader_refs": hits,
        "status": "GREEN" if hits >= 0 else "AMBER",
        "note_fa": f"{hits} ردیف مرتبط با معامله‌گر کاغذی در زنجیرهٔ hash.",
    }


def _load_witness_probe(root: Path) -> dict[str, Any]:
    p = root / "reports" / "grok" / "PAPER" / "weekday_witness_probe.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_trader_promotion_gate(root: Path) -> str | None:
    p = root / "reports" / "grok" / "PAPER" / "paper_trader_status.json"
    try:
        st = json.loads(p.read_text(encoding="utf-8"))
        perf = st.get("performance") or {}
        if isinstance(perf, dict) and perf.get("promotion_gate"):
            return str(perf["promotion_gate"])
        if isinstance(perf, dict) and int(perf.get("n") or 0) < 30:
            return "NOT_ELIGIBLE (needs >= 30 closed trades, CI lower bound > 0, DSR > 0.95)"
        return st.get("edge_status_fa")
    except Exception:
        return None


def export_paper_trade_audit_snapshot(root: Path) -> dict[str, Any]:
    trades = audit_paper_trades_jsonl(root)
    ledger = audit_mission_ledger_paper_refs(root)
    sess = session_report()
    probe = _load_witness_probe(root)
    raw_gate = _load_trader_promotion_gate(root)
    not_eligible = "NOT_ELIGIBLE (needs >= 30 closed trades, CI lower bound > 0, DSR > 0.95)"
    promotion_gate = raw_gate if raw_gate and "NOT_ELIGIBLE" in str(raw_gate) else not_eligible
    payload = {
        "schema": "ahos.paper_trade_audit.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "unproven_edge": True,
        "trades": trades,
        "mission_ledger": ledger,
        "session_gate": sess,
        "weekday_fill_gate_fa": str(probe.get("summary_fa") or sess.get("summary_fa") or ""),
        "tradable_asset_classes": probe.get("tradable_asset_classes") or [],
        "verified_asset_classes": probe.get("verified_asset_classes") or [],
        "promotion_gate": promotion_gate,
        "stored_promotion_word_is_evaluate": str(raw_gate) == "EVALUATE",
        "promotion_gate_fa": "هنوز واجد ارتقا نیست: کمتر از ۳۰ معاملهٔ بسته یا DSR/PBO پاس نشده — لبهٔ سودآوری اثبات‌نشده.",
        "status": (
            "AMBER"
            if trades["closes"] > 0 and ledger.get("ledger_present") and ledger.get("paper_trader_refs", 0) == 0
            else trades["status"]
        ),
    }
    if trades["issues"]:
        payload["status"] = "AMBER"
    out = root / "reports" / "grok" / "PAPER" / "paper_trade_audit.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def measure_exit_reason_census(root: Path) -> dict[str, Any]:
    """Count recorded close reasons. A reason absent from the log was not observed there."""
    import json
    from collections import defaultdict

    counts: dict[str, int] = defaultdict(int)
    pnl: dict[str, float] = defaultdict(float)
    partial = 0
    closes = 0
    path = Path(root) / LEDGER_REL
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if not isinstance(row, dict) or row.get("event") != "CLOSE":
                continue
            closes += 1
            reason = str(row.get("reason") or "UNLABELED")
            counts[reason] += 1
            if isinstance(row.get("realized_pnl_usd"), (int, float)):
                pnl[reason] += float(row["realized_pnl_usd"])
            if row.get("partial") is True:
                partial += 1
    return {
        "paper_only": True,
        "close_rows": closes,
        "partial_rows": partial,
        "reason_counts": dict(counts),
        "pnl_by_reason_usd": {k: round(v, 4) for k, v in pnl.items()},
        "daemon_restarted": False,
        "absence_note": "A reason that is not in this log was not observed. It is not evidence that the rule is absent from code the running process has not loaded.",
    }


def write_exit_reason_census(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.exit_reason_census.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_exit_reason_census(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "exit_reason_census.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _log_rows(root: Path) -> list[dict[str, Any]]:
    path = Path(root) / LEDGER_REL
    if not path.is_file():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if isinstance(row, dict):
            out.append(row)
    return out


def _hold_hours(row: dict[str, Any]) -> float | None:
    try:
        opened = datetime.strptime(str(row.get("opened_at")), "%Y-%m-%dT%H:%M:%SZ")
        closed = datetime.strptime(str(row.get("closed_at")), "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        return None
    return round((closed - opened).total_seconds() / 3600.0, 2)


def measure_conflict_anatomy(root: Path) -> dict[str, Any]:
    """Classify recorded witness-conflict exits. The exit rule is not changed."""
    from collections import Counter, defaultdict

    from architecture.markets.second_source import DEFAULT_TOL, TOLERANCE
    from architecture.markets.token_safety_live import POOL_PRICE_TOL

    def applicable(symbol: str) -> float:
        if symbol.startswith("DEX_"):
            return POOL_PRICE_TOL
        return TOLERANCE.get(symbol, DEFAULT_TOL)

    rows = _log_rows(root)
    by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("symbol"):
            by_symbol[str(row["symbol"])].append(row)
    gaps: list[float] = []
    holds: list[float] = []
    missing = within = within_spot = inconsistent = prior_zero = prior_one = prior_more = 0
    dex_rows = mapped_rows = 0
    dex_excess: list[float] = []
    mapped_excess: list[float] = []
    symbols: Counter[str] = Counter()
    kinds: Counter[str] = Counter()
    for seq in by_symbol.values():
        for index, row in enumerate(seq):
            if row.get("event") != "CLOSE" or row.get("reason") != "WITNESS_CONFLICT_EXIT":
                continue
            symbol = str(row.get("symbol"))
            symbols[symbol] += 1
            dex = symbol.startswith("DEX_")
            if dex:
                dex_rows += 1
            else:
                mapped_rows += 1
            raw_source = str((row.get("witness") or {}).get("source_b") or "")
            kinds[raw_source.split(":", 1)[0] or "UNLABELED"] += 1
            prior = 0
            cursor = index - 1
            while cursor >= 0 and (seq[cursor].get("witness") or {}).get("verdict") == "CONFLICT":
                prior += 1
                cursor -= 1
            if prior == 0:
                prior_zero += 1
            elif prior == 1:
                prior_one += 1
            else:
                prior_more += 1
            gap = (row.get("witness") or {}).get("gap")
            tol = applicable(symbol)
            spot_tol = TOLERANCE.get(symbol, DEFAULT_TOL)
            if not isinstance(gap, (int, float)):
                missing += 1
            else:
                gaps.append(float(gap))
                excess = round(float(gap) - tol, 5)
                (dex_excess if dex else mapped_excess).append(excess)
                if excess <= 0:
                    within += 1
                    inconsistent += 1
                if float(gap) - spot_tol <= 0:
                    within_spot += 1
            held = _hold_hours(row)
            if held is not None:
                holds.append(held)
    ordered = sorted(gaps)
    return {
        "paper_only": True,
        "exit_rule_changed": False,
        "rule": "FAIL_CLOSED_ON_RECORDED_DISAGREEMENT",
        "rows": sum(symbols.values()),
        "gap_missing": missing,
        "gap_min": ordered[0] if ordered else None,
        "gap_max": ordered[-1] if ordered else None,
        "gap_upper_median": ordered[len(ordered) // 2] if ordered else None,
        "within_tolerance": within,
        "within_spot_default": within_spot,
        "inconsistent_with_current_tolerance": inconsistent,
        "dex_rows": dex_rows,
        "mapped_rows": mapped_rows,
        "dex_excess_min": min(dex_excess) if dex_excess else None,
        "mapped_excess_min": min(mapped_excess) if mapped_excess else None,
        "source_kinds": dict(kinds),
        "pool_price_tolerance": POOL_PRICE_TOL,
        "spot_default_tolerance": DEFAULT_TOL,
        "tolerance_source": "INFERRED_FROM_CURRENT_CODE_NOT_STORED_ON_THE_ROW",
        "prior_conflict_zero": prior_zero,
        "prior_conflict_one": prior_one,
        "prior_conflict_more": prior_more,
        "symbols": dict(symbols),
        "hold_hours_min": min(holds) if holds else None,
        "hold_hours_max": max(holds) if holds else None,
    }


def write_conflict_anatomy(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.witness_conflict_anatomy.v2",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_conflict_anatomy(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "witness_conflict_anatomy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_reversal_anatomy(root: Path) -> dict[str, Any]:
    """Check recorded signal-reversal exits against the stored composite threshold."""
    from architecture.markets.paper_trader import ENTRY

    signed: list[float] = []
    moves: list[float] = []
    holds: list[float] = []
    reversals = [row for row in _log_rows(root)
                 if row.get("event") == "CLOSE" and row.get("reason") == "SIGNAL_REVERSAL"]
    for row in reversals:
        side = 1.0 if row.get("side") == "LONG" else -1.0
        composite = row.get("exit_composite")
        if isinstance(composite, (int, float)):
            signed.append(round(float(composite) * side, 4))
        entry = row.get("entry_price")
        fill = row.get("fill_price")
        if isinstance(entry, (int, float)) and isinstance(fill, (int, float)) and entry:
            moves.append(round((float(fill) - float(entry)) / float(entry) * side, 4))
        held = _hold_hours(row)
        if held is not None:
            holds.append(held)
    beyond = bool(signed) and all(value <= -ENTRY for value in signed)
    if not reversals:
        status = "NO_REVERSAL_ROWS"
    elif len(signed) != len(reversals):
        status = "COMPOSITE_NOT_STORED"
    elif beyond:
        status = "MATCHES_RECORDED_THRESHOLD"
    else:
        status = "THRESHOLD_MISS"
    return {
        "paper_only": True,
        "exit_rule_changed": False,
        "threshold": ENTRY,
        "rows": len(reversals),
        "signed_composite_n": len(signed),
        "all_at_or_beyond_threshold": beyond if reversals else True,
        "signed_composite_min": min(signed) if signed else None,
        "signed_composite_max": max(signed) if signed else None,
        "signed_move_min": min(moves) if moves else None,
        "signed_move_max": max(moves) if moves else None,
        "hold_hours_min": min(holds) if holds else None,
        "hold_hours_max": max(holds) if holds else None,
        "status": status,
    }


def measure_dex_roundtrip(root: Path) -> dict[str, Any]:
    """Recorded open and close counts for DEX_ symbols. The pnl sum is the log, not an edge."""
    from collections import defaultdict

    opens: dict[str, int] = defaultdict(int)
    closes: dict[str, int] = defaultdict(int)
    pnl: dict[str, float] = defaultdict(float)
    for row in _log_rows(root):
        symbol = str(row.get("symbol") or "")
        if not symbol.startswith("DEX_"):
            continue
        if row.get("event") == "OPEN":
            opens[symbol] += 1
        elif row.get("event") == "CLOSE":
            closes[symbol] += 1
            if isinstance(row.get("realized_pnl_usd"), (int, float)):
                pnl[symbol] += float(row["realized_pnl_usd"])
    names = sorted(set(opens) | set(closes))
    table = [{
        "symbol": name,
        "opens": opens[name],
        "closes": closes[name],
        "open_minus_close": opens[name] - closes[name],
        "realized_pnl_usd": round(pnl[name], 4),
    } for name in names]
    return {
        "paper_only": True,
        "edge_claimed": False,
        "symbols": table,
        "flat": all(item["open_minus_close"] == 0 for item in table),
        "realized_pnl_usd": round(sum(item["realized_pnl_usd"] for item in table), 4),
    }


def write_dex_roundtrip(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.dex_roundtrip.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_dex_roundtrip(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "dex_roundtrip.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def write_reversal_anatomy(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.reversal_anatomy.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_reversal_anatomy(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "reversal_anatomy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_skip_census(root: Path) -> dict[str, Any]:
    """Count SKIP and NO_TRADE reasons already written on the paper log."""
    from collections import Counter

    counts: Counter[str] = Counter()
    for row in _log_rows(root):
        if row.get("event") in ("SKIP", "NO_TRADE"):
            counts[str(row.get("reason") or "UNLABELED")] += 1
    dominant = sorted(counts, key=lambda key: (-counts[key], key))[0] if counts else None
    return {
        "paper_only": True,
        "event_rows": sum(counts.values()),
        "reason_counts": dict(counts),
        "dominant_reason": dominant,
    }


def measure_symbol_book(root: Path) -> dict[str, Any]:
    """Per-symbol close pnl. Desk totals are the sum, so opposite signs stay visible."""
    from collections import defaultdict

    from architecture.markets.paper_account import DESKS

    known = set(DESKS)
    raw_symbol: dict[str, dict[str, Any]] = {}
    raw_desk: dict[str, float] = defaultdict(float)
    desk_closes: dict[str, int] = defaultdict(int)
    for row in _log_rows(root):
        if row.get("event") != "CLOSE":
            continue
        symbol = str(row.get("symbol") or "MISSING")
        desk = str(row.get("desk") or "MISSING")
        pnl = float(row["realized_pnl_usd"]) if isinstance(row.get("realized_pnl_usd"), (int, float)) else 0.0
        item = raw_symbol.setdefault(symbol, {"desk": desk, "closes": 0, "pnl": 0.0, "reasons": defaultdict(lambda: [0, 0.0])})
        item["closes"] += 1
        item["pnl"] += pnl
        reason = str(row.get("reason") or "MISSING")
        item["reasons"][reason][0] += 1
        item["reasons"][reason][1] += pnl
        raw_desk[desk] += pnl
        desk_closes[desk] += 1
    symbols = []
    for symbol in sorted(raw_symbol):
        item = raw_symbol[symbol]
        symbols.append({
            "symbol": symbol,
            "desk": item["desk"],
            "closes": item["closes"],
            "realized_pnl_usd": round(item["pnl"], 4),
            "reasons": [{
                "reason": reason,
                "n": item["reasons"][reason][0],
                "realized_pnl_usd": round(item["reasons"][reason][1], 4),
            } for reason in sorted(item["reasons"])],
        })
    desks = []
    for desk in sorted(raw_desk):
        desks.append({
            "desk": desk,
            "closes": desk_closes[desk],
            "realized_pnl_usd": round(raw_desk[desk], 4),
            "rounded_usd": round(raw_desk[desk], 2),
            "assigned": desk in known,
        })
    return {
        "paper_only": True,
        "edge_claimed": False,
        "close_rows": sum(item["closes"] for item in symbols),
        "symbols": symbols,
        "desks": desks,
        "account_realized_pnl_usd": round(sum(raw_desk.values()), 4),
        "rounded_desk_sum_usd": round(sum(item["rounded_usd"] for item in desks), 2),
        "unassigned_desks": sum(1 for item in desks if not item["assigned"]),
    }


def write_symbol_book(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.symbol_book.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_symbol_book(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "symbol_book.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_open_book(root: Path, now: datetime | None = None) -> dict[str, Any]:
    """Unmatched OPEN rows. Age is not an exit order."""
    from collections import defaultdict, deque

    from architecture.markets.paper_trader import MAX_HOLD_S, TIME_STOP_HOLD_FRAC

    now = now or datetime.now(timezone.utc)
    queues: dict[str, deque] = defaultdict(deque)
    unmatched = 0
    for row in _log_rows(root):
        symbol = str(row.get("symbol") or "")
        if row.get("event") == "OPEN":
            queues[symbol].append(row)
        elif row.get("event") == "CLOSE" and queues[symbol]:
            queues[symbol].popleft()
        elif row.get("event") == "CLOSE":
            unmatched += 1
    time_stop_h = MAX_HOLD_S * TIME_STOP_HOLD_FRAC / 3600.0
    max_h = MAX_HOLD_S / 3600.0
    opens = []
    unknown_age = False
    beyond = False
    for symbol in sorted(queues):
        for row in queues[symbol]:
            opened = row.get("opened_at") or row.get("ts")
            try:
                started = datetime.strptime(str(opened), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                hours = (now - started).total_seconds() / 3600.0
            except (TypeError, ValueError):
                hours = None
            if hours is None:
                unknown_age = True
            elif hours > time_stop_h or hours > max_h:
                beyond = True
            opens.append({
                "symbol": symbol,
                "desk": row.get("desk"),
                "side": row.get("side"),
                "open_time": opened,
            })
    path = Path(root) / "reports" / "grok" / "PAPER" / "paper_positions.json"
    file_symbols = None
    if path.is_file():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            doc = None
        positions = doc.get("positions") if isinstance(doc, dict) else None
        if isinstance(positions, dict):
            file_symbols = sorted(str(key) for key in positions)
    log_symbols = sorted({item["symbol"] for item in opens})
    if not opens:
        status = "NO_OPEN_ROWS"
    elif beyond:
        status = "AT_OR_BEYOND_A_HOLD_LIMIT"
    elif unknown_age:
        status = "OPEN_AGE_UNKNOWN"
    else:
        status = "INSIDE_BOTH_LIMITS"
    return {
        "paper_only": True,
        "exit_inferred": False,
        "daemon_restarted": False,
        "time_stop_hours": time_stop_h,
        "max_hold_hours": max_h,
        "open_rows": opens,
        "unmatched_closes": unmatched,
        "status": status,
        "positions_file_symbols": file_symbols,
        "log_matches_positions_file": file_symbols == log_symbols,
    }


def write_open_book(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.open_book.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_open_book(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "open_book.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_stored_witness_fields(root: Path) -> dict[str, Any]:
    """Count tolerance and pair fields actually stored on close rows."""
    tolerance = pair = address_pair = 0
    closes = 0
    for row in _log_rows(root):
        if row.get("event") != "CLOSE":
            continue
        closes += 1
        witness = row.get("witness") if isinstance(row.get("witness"), dict) else {}
        if "tolerance" in witness:
            tolerance += 1
        stored_pair = witness.get("pair")
        if isinstance(stored_pair, str):
            pair += 1
            if "0x" in stored_pair.lower() or "pool32:" in stored_pair:
                address_pair += 1
    return {
        "paper_only": True,
        "exit_rule_changed": False,
        "daemon_restarted": False,
        "close_rows": closes,
        "tolerance_stored": tolerance,
        "pair_stored": pair,
        "address_shaped_pair_stored": address_pair,
    }


def write_stored_witness_fields(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.stored_witness_fields.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_stored_witness_fields(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "stored_witness_fields.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_entry_gate(root: Path) -> dict[str, Any]:
    """Signed entry composite against the recorded 0.25 gate. The score is not a probability."""
    from architecture.markets.paper_trader import ENTRY

    scored: list[float] = []
    pnls: list[float] = []
    missing = raw_outside = 0
    closes = 0
    for row in _log_rows(root):
        if row.get("event") != "CLOSE":
            continue
        closes += 1
        brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
        composite = brain.get("composite")
        side = row.get("side")
        pnl = row.get("realized_pnl_usd")
        if side not in ("LONG", "SHORT") or not isinstance(composite, (int, float)) or not isinstance(pnl, (int, float)):
            missing += 1
            continue
        value = float(composite)
        if value < 0 or value > 1:
            raw_outside += 1
        direction = 1.0 if side == "LONG" else -1.0
        scored.append(round(value * direction, 4))
        pnls.append(float(pnl))
    above = sum(1 for value in scored if value >= ENTRY)
    if closes == 0:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif above != len(scored):
        status = "BELOW_RECORDED_THRESHOLD"
    else:
        status = "GATE_HELD_NOT_A_PROBABILITY"
    return {
        "paper_only": True,
        "edge_claimed": False,
        "gate_changed": False,
        "threshold": ENTRY,
        "close_rows": closes,
        "scored_rows": len(scored),
        "missing_rows": missing,
        "signed_min": min(scored) if scored else None,
        "signed_max": max(scored) if scored else None,
        "at_or_above_threshold": above,
        "wins": sum(1 for value in pnls if value > 0),
        "losses": sum(1 for value in pnls if value < 0),
        "flat": sum(1 for value in pnls if value == 0),
        "realized_pnl_usd": round(sum(pnls), 4),
        "raw_outside_unit_interval": raw_outside,
        "brier": None,
        "brier_status": "NOT_A_PROBABILITY" if scored else "NOT_RUN",
        "status": status,
    }


def write_entry_gate(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.entry_gate.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_entry_gate(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "entry_gate.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_kelly_label(root: Path) -> dict[str, Any]:
    """The stored kelly field. This measurement does not turn Kelly on."""
    from collections import Counter

    labels: Counter[str] = Counter()
    numeric = missing = opens = 0
    for row in _log_rows(root):
        if row.get("event") != "OPEN":
            continue
        opens += 1
        kelly = row.get("kelly")
        if isinstance(kelly, str) and kelly:
            labels[kelly] += 1
        elif isinstance(kelly, (int, float)):
            numeric += 1
        else:
            missing += 1
    if opens == 0:
        status = "NO_OPENS"
    elif numeric:
        status = "NUMERIC_KELLY_PRESENT"
    elif missing == opens:
        status = "KELLY_FIELD_ABSENT"
    elif missing:
        status = "MIXED"
    elif len(labels) == 1 and "OFF" in next(iter(labels)):
        status = "UNIFORM_OFF_LABEL"
    elif len(labels) == 1:
        status = "UNIFORM_LABEL"
    else:
        status = "MIXED"
    return {
        "paper_only": True,
        "kelly_switched_on": False,
        "open_rows": opens,
        "label_counts": dict(labels),
        "numeric_rows": numeric,
        "missing_rows": missing,
        "status": status,
    }


def write_kelly_label(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.kelly_label.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_kelly_label(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "kelly_label.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_fee_identity(root: Path) -> dict[str, Any]:
    """Net pnl plus close fees is the log's implied gross. It is not a second cash gap."""
    from collections import defaultdict, deque

    queues: dict[str, deque] = defaultdict(deque)
    open_fee = closed_entry_fee = still_open_fee = close_fees = net = 0.0
    opens = closes = unmatched = missing_open_fee = 0
    for row in _log_rows(root):
        symbol = str(row.get("symbol") or "")
        if row.get("event") == "OPEN":
            opens += 1
            queues[symbol].append(row)
            if isinstance(row.get("fee_usd"), (int, float)):
                open_fee += float(row["fee_usd"])
            else:
                missing_open_fee += 1
        elif row.get("event") == "CLOSE":
            closes += 1
            if isinstance(row.get("fees_usd"), (int, float)):
                close_fees += float(row["fees_usd"])
            if isinstance(row.get("realized_pnl_usd"), (int, float)):
                net += float(row["realized_pnl_usd"])
            if queues[symbol]:
                opened = queues[symbol].popleft()
                if isinstance(opened.get("fee_usd"), (int, float)):
                    closed_entry_fee += float(opened["fee_usd"])
            else:
                unmatched += 1
    for queue in queues.values():
        for opened in queue:
            if isinstance(opened.get("fee_usd"), (int, float)):
                still_open_fee += float(opened["fee_usd"])
    return {
        "paper_only": True,
        "edge_claimed": False,
        "added_to_cash_gap": False,
        "open_rows": opens,
        "close_rows": closes,
        "open_fee_usd": round(open_fee, 6),
        "closed_entry_fee_usd": round(closed_entry_fee, 6),
        "still_open_entry_fee_usd": round(still_open_fee, 6),
        "close_fees_usd": round(close_fees, 6),
        "net_pnl_usd": round(net, 4),
        "implied_gross_usd": round(net + close_fees, 6),
        "missing_open_fee": missing_open_fee,
        "unmatched_closes": unmatched,
        "status": "NO_CLOSES" if closes == 0 else "IDENTITY_OF_THE_LOG",
    }


def write_fee_identity(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.fee_identity.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_fee_identity(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "fee_identity.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_weight_vintage(root: Path) -> dict[str, Any]:
    """Close pnl by stored weights version. Small cells are not a comparison."""
    from collections import defaultdict

    cells: dict[str, list[float]] = defaultdict(lambda: [0, 0.0])
    missing = closes = 0
    for row in _log_rows(root):
        if row.get("event") != "CLOSE":
            continue
        closes += 1
        brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
        version = brain.get("weights_version")
        pnl = row.get("realized_pnl_usd")
        if version is None or not isinstance(pnl, (int, float)):
            missing += 1
            continue
        key = str(version)
        cells[key][0] += 1
        cells[key][1] += float(pnl)

    def _order(key: str) -> tuple:
        try:
            return (0, int(key))
        except ValueError:
            return (1, key)

    versions = [{
        "weights_version": key,
        "closes": cells[key][0],
        "realized_pnl_usd": round(cells[key][1], 4),
    } for key in sorted(cells, key=_order)]
    largest = max((item["closes"] for item in versions), default=0)
    if closes == 0:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif largest < 30:
        status = "TOO_SMALL_TO_COMPARE"
    else:
        status = "COMPARABLE_CELL_PRESENT"
    return {
        "paper_only": True,
        "comparison_claimed": False,
        "sample_gate": 30,
        "close_rows": closes,
        "missing_rows": missing,
        "largest_cell": largest,
        "versions": versions,
        "status": status,
    }


def write_weight_vintage(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.weight_vintage.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_weight_vintage(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "weight_vintage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _close_brains(root: Path) -> list[dict[str, Any]]:
    out = []
    for row in _log_rows(root):
        if row.get("event") == "CLOSE":
            out.append(row)
    return out


def measure_contribution_identity(root: Path) -> dict[str, Any]:
    """Stored composite against the weighted average of stored contributions."""
    gaps: list[float] = []
    missing = 0
    closes = _close_brains(root)
    for row in closes:
        brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
        contributions = brain.get("contributions")
        composite = brain.get("composite")
        if not isinstance(contributions, list) or not isinstance(composite, (int, float)):
            missing += 1
            continue
        weight = sum(float(item.get("weight") or 0) for item in contributions if isinstance(item, dict))
        total = sum(float(item.get("contribution") or 0) for item in contributions if isinstance(item, dict))
        if weight == 0:
            missing += 1
            continue
        gaps.append(round(total / weight - float(composite), 5))
    beyond = sum(1 for gap in gaps if abs(gap) > 0.001)
    if not closes:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif beyond:
        status = "IDENTITY_BROKEN"
    else:
        status = "IDENTITY_WITHIN_ROUNDING"
    return {
        "paper_only": True,
        "edge_claimed": False,
        "close_rows": len(closes),
        "scored_rows": len(gaps),
        "missing_rows": missing,
        "max_abs_gap": None if not gaps else round(max(abs(gap) for gap in gaps), 5),
        "beyond_rounding": beyond,
        "rounding_band": 0.001,
        "status": status,
    }


def write_contribution_identity(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.contribution_identity.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_contribution_identity(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "contribution_identity.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_dominant_signal(root: Path) -> dict[str, Any]:
    """Largest stored contribution. Sign agreement with the side is the formula, not skill."""
    from collections import Counter

    rows = Counter()
    matches = Counter()
    missing = 0
    closes = _close_brains(root)
    for row in closes:
        brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
        contributions = [item for item in (brain.get("contributions") or []) if isinstance(item, dict)]
        side = row.get("side")
        if not contributions or side not in ("LONG", "SHORT"):
            missing += 1
            continue
        best = max(contributions, key=lambda item: abs(float(item.get("contribution") or 0)))
        name = str(best.get("signal") or "MISSING")
        rows[name] += 1
        score = best.get("score")
        direction = 1.0 if side == "LONG" else -1.0
        if isinstance(score, (int, float)) and float(score) * direction > 0:
            matches[name] += 1
    signals = [{
        "signal": name,
        "rows": rows[name],
        "sign_matches_side": matches[name],
    } for name in sorted(rows, key=lambda name: (-rows[name], name))]
    matched = sum(item["sign_matches_side"] for item in signals)
    scored = sum(item["rows"] for item in signals)
    if not closes:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif matched == scored:
        status = "LARGEST_TERM_SHARES_THE_SIDE"
    else:
        status = "MIXED_SIGNS"
    return {
        "paper_only": True,
        "skill_claimed": False,
        "close_rows": len(closes),
        "scored_rows": scored,
        "missing_rows": missing,
        "sign_matches_side": matched,
        "signals": signals,
        "status": status,
    }


def write_dominant_signal(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.dominant_signal.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_dominant_signal(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "dominant_signal.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_side_book(root: Path) -> dict[str, Any]:
    """Recorded pnl by position side. A positive side sum is not an edge."""
    from collections import defaultdict

    cells: dict[str, list[float]] = defaultdict(lambda: [0, 0.0, 0, 0])
    closes = _close_brains(root)
    missing = 0
    for row in closes:
        side = row.get("side")
        pnl = row.get("realized_pnl_usd")
        if side not in ("LONG", "SHORT") or not isinstance(pnl, (int, float)):
            missing += 1
            continue
        cells[side][0] += 1
        cells[side][1] += float(pnl)
        if float(pnl) > 0:
            cells[side][2] += 1
        elif float(pnl) < 0:
            cells[side][3] += 1
    sides = [{
        "side": side,
        "closes": cells[side][0],
        "realized_pnl_usd": round(cells[side][1], 4),
        "wins": cells[side][2],
        "losses": cells[side][3],
    } for side in sorted(cells)]
    if not closes:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    else:
        status = "RECORDED_SPLIT"
    return {
        "paper_only": True,
        "edge_claimed": False,
        "close_rows": len(closes),
        "missing_rows": missing,
        "sides": sides,
        "realized_pnl_usd": round(sum(item["realized_pnl_usd"] for item in sides), 4),
        "status": status,
    }


def write_side_book(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.side_book.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_side_book(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "side_book.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_entry_regime(root: Path) -> dict[str, Any]:
    """Entry-regime schema and HMM state counts. Cells under 30 are not a comparison."""
    from collections import Counter

    schemas: Counter[str] = Counter()
    states: Counter[str] = Counter()
    missing = 0
    closes = _close_brains(root)
    for row in closes:
        brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
        regime = brain.get("regime")
        if not isinstance(regime, dict) or not regime:
            missing += 1
            continue
        if "hmm_state" not in regime:
            schemas["NO_HMM"] += 1
            states["ABSENT"] += 1
        elif "ratio" in regime:
            schemas["HMM_WITH_RATIO"] += 1
            states[str(regime.get("hmm_state"))] += 1
        else:
            schemas["HMM_WITHOUT_RATIO"] += 1
            states[str(regime.get("hmm_state"))] += 1
    schema_rows = [{"schema": name, "rows": schemas[name]} for name in sorted(schemas)]
    state_rows = [{"state": name, "rows": states[name]} for name in sorted(states)]
    largest = max((item["rows"] for item in state_rows), default=0)
    if not closes:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif largest < 30:
        status = "TOO_SMALL_TO_COMPARE"
    else:
        status = "COMPARABLE_CELL_PRESENT"
    return {
        "paper_only": True,
        "comparison_claimed": False,
        "sample_gate": 30,
        "close_rows": len(closes),
        "missing_rows": missing,
        "schemas": schema_rows,
        "hmm_states": state_rows,
        "largest_hmm_cell": largest,
        "status": status,
    }


def write_entry_regime(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.entry_regime.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_entry_regime(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "entry_regime.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _signed(row: dict[str, Any], key: str) -> float | None:
    side = row.get("side")
    value = row.get(key) if key != "entry" else (row.get("entry_brain") or {}).get("composite")
    if side not in ("LONG", "SHORT") or not isinstance(value, (int, float)):
        return None
    direction = 1.0 if side == "LONG" else -1.0
    return round(float(value) * direction, 4)


def measure_exit_score_path(root: Path) -> dict[str, Any]:
    """Signed exit score by close reason. A positive conflict exit is not a reversal."""
    from collections import defaultdict

    from architecture.markets.paper_trader import ENTRY

    buckets: dict[str, list[tuple[float, float]]] = defaultdict(list)
    missing = 0
    closes = _close_brains(root)
    for row in closes:
        exit_score = _signed(row, "exit_composite")
        entry_score = _signed(row, "entry")
        if exit_score is None or entry_score is None:
            missing += 1
            continue
        buckets[str(row.get("reason") or "MISSING")].append((exit_score, round(exit_score - entry_score, 4)))
    reasons = []
    for reason in sorted(buckets):
        pairs = buckets[reason]
        exits = [item[0] for item in pairs]
        deltas = [item[1] for item in pairs]
        reasons.append({
            "reason": reason,
            "rows": len(pairs),
            "signed_exit_min": min(exits),
            "signed_exit_max": max(exits),
            "delta_min": min(deltas),
            "delta_max": max(deltas),
            "at_or_beyond_reversal": sum(1 for value in exits if value <= -ENTRY),
            "between_reversal_and_zero": sum(1 for value in exits if -ENTRY < value <= 0),
            "positive_below_entry": sum(1 for value in exits if 0 < value < ENTRY),
            "at_or_above_entry": sum(1 for value in exits if value >= ENTRY),
        })
    if not closes:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    else:
        status = "PATH_RECORDED"
    return {
        "paper_only": True,
        "edge_claimed": False,
        "exit_rule_changed": False,
        "threshold": ENTRY,
        "close_rows": len(closes),
        "missing_rows": missing,
        "reasons": reasons,
        "status": status,
    }


def write_exit_score_path(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.exit_score_path.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_exit_score_path(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "exit_score_path.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_hold_by_reason(root: Path) -> dict[str, Any]:
    """Hold hours by close reason. A long hold is not an exit order."""
    from collections import defaultdict

    hours: dict[str, list[float]] = defaultdict(list)
    missing = 0
    closes = _close_brains(root)
    for row in closes:
        held = _hold_hours(row)
        if held is None:
            missing += 1
            continue
        hours[str(row.get("reason") or "MISSING")].append(held)
    reasons = [{
        "reason": reason,
        "rows": len(hours[reason]),
        "hold_hours_min": min(hours[reason]),
        "hold_hours_max": max(hours[reason]),
    } for reason in sorted(hours)]
    if not closes:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    else:
        status = "ALL_TIMESTAMPS_PRESENT"
    return {
        "paper_only": True,
        "exit_inferred": False,
        "close_rows": len(closes),
        "missing_rows": missing,
        "reasons": reasons,
        "status": status,
    }


def write_hold_by_reason(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.hold_by_reason.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_hold_by_reason(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "hold_by_reason.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_signal_breadth(root: Path) -> dict[str, Any]:
    """How many stored contributions support each close. The weight sum is not forced to 1."""
    from collections import Counter

    counts: list[int] = []
    weight_sums: list[float] = []
    missing = 0
    closes = _close_brains(root)
    for row in closes:
        brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
        contributions = [item for item in (brain.get("contributions") or []) if isinstance(item, dict)]
        if not contributions:
            missing += 1
            continue
        counts.append(len(contributions))
        weight_sums.append(round(sum(float(item.get("weight") or 0) for item in contributions), 4))
    histogram = [{"signals": count, "rows": tally} for count, tally in sorted(Counter(counts).items())]
    if not closes:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    else:
        status = "RECORDED_BREADTH"
    return {
        "paper_only": True,
        "edge_claimed": False,
        "minimum_changed": False,
        "close_rows": len(closes),
        "missing_rows": missing,
        "signal_count_min": min(counts) if counts else None,
        "signal_count_max": max(counts) if counts else None,
        "signal_counts": histogram,
        "weight_sum_min": min(weight_sums) if weight_sums else None,
        "weight_sum_max": max(weight_sums) if weight_sums else None,
        "weight_sum_below_1": sum(1 for value in weight_sums if value < 1),
        "weight_sum_below_half": sum(1 for value in weight_sums if value < 0.5),
        "status": status,
    }


def write_signal_breadth(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.signal_breadth.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_signal_breadth(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "signal_breadth.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _paired_closes(root: Path) -> list[tuple[dict[str, Any], dict[str, Any] | None]]:
    from collections import defaultdict, deque

    queues: dict[str, deque] = defaultdict(deque)
    pairs = []
    for row in _log_rows(root):
        symbol = str(row.get("symbol") or "")
        if row.get("event") == "OPEN":
            queues[symbol].append(row)
        elif row.get("event") == "CLOSE":
            pairs.append((row, queues[symbol].popleft() if queues[symbol] else None))
    return pairs


def _direction(row: dict[str, Any]) -> float | None:
    if row.get("side") == "LONG":
        return 1.0
    if row.get("side") == "SHORT":
        return -1.0
    return None


def measure_exit_trigger(root: Path) -> dict[str, Any]:
    """Quote move against the stored stop. The take-profit line is the quote, not the fill."""
    from architecture.markets.paper_trader import TAKE_MULT

    take_rows = take_beyond = fill_inside = other_beyond = stop_crossed = missing = 0
    closes = _paired_closes(root)
    for row, opened in closes:
        direction = _direction(row)
        entry = row.get("entry_price")
        quote = row.get("quote_price")
        fill = row.get("fill_price")
        stop = (opened or {}).get("stop_pct") if isinstance(opened, dict) else None
        if (direction is None or not isinstance(entry, (int, float)) or not entry
                or not isinstance(quote, (int, float)) or not isinstance(fill, (int, float))
                or not isinstance(stop, (int, float)) or not stop):
            missing += 1
            continue
        quote_ratio = (float(quote) - float(entry)) / float(entry) * direction / float(stop)
        fill_ratio = (float(fill) - float(entry)) / float(entry) * direction / float(stop)
        is_take = row.get("reason") == "TAKE_PROFIT"
        if is_take:
            take_rows += 1
        if quote_ratio >= TAKE_MULT:
            if is_take:
                take_beyond += 1
            else:
                other_beyond += 1
            if fill_ratio < TAKE_MULT:
                fill_inside += 1
        if quote_ratio <= -1:
            stop_crossed += 1
    if not closes:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif take_beyond == take_rows and other_beyond == 0 and stop_crossed == 0:
        status = "RULE_CONSISTENT"
    else:
        status = "RULE_INCONSISTENT"
    return {
        "paper_only": True,
        "exit_rule_changed": False,
        "take_multiple": TAKE_MULT,
        "close_rows": len(closes),
        "missing_rows": missing,
        "take_profit_rows": take_rows,
        "take_profit_quote_beyond": take_beyond,
        "fill_inside_take_line": fill_inside,
        "other_quote_beyond": other_beyond,
        "stop_crossed": stop_crossed,
        "status": status,
    }


def write_exit_trigger(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.exit_trigger.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_exit_trigger(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "exit_trigger.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_signal_dissent(root: Path) -> dict[str, Any]:
    """Same-side, opposing, and zero scores. No signal is removed."""
    from collections import defaultdict

    cells: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0, 0])
    agree = oppose = zero = 0
    shares_opp: list[float] = []
    shares_zero: list[float] = []
    closes = _close_brains(root)
    missing = 0
    for row in closes:
        direction = _direction(row)
        brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
        contributions = [item for item in (brain.get("contributions") or []) if isinstance(item, dict)]
        if direction is None or not contributions:
            missing += 1
            continue
        weight = sum(float(item.get("weight") or 0) for item in contributions)
        opposed = diluted = 0.0
        for item in contributions:
            name = str(item.get("signal") or "MISSING")
            score = float(item.get("score") or 0)
            item_weight = float(item.get("weight") or 0)
            cells[name][0] += 1
            if score == 0:
                zero += 1
                diluted += item_weight
                cells[name][3] += 1
            elif score * direction > 0:
                agree += 1
                cells[name][1] += 1
            else:
                oppose += 1
                opposed += item_weight
                cells[name][2] += 1
        base = weight or 1.0
        shares_opp.append(opposed / base)
        shares_zero.append(diluted / base)
    signals = [{
        "signal": name,
        "present": cells[name][0],
        "agree": cells[name][1],
        "oppose": cells[name][2],
        "zero": cells[name][3],
    } for name in sorted(cells)]
    always_zero = [item["signal"] for item in signals if item["agree"] == 0 and item["oppose"] == 0]
    always_opposes = [item["signal"] for item in signals if item["agree"] == 0 and item["oppose"] == item["present"] and item["oppose"] > 0]
    never_agrees = [item["signal"] for item in signals if item["agree"] == 0]
    if not closes:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    else:
        status = "DISSENT_RECORDED"
    return {
        "paper_only": True,
        "skill_claimed": False,
        "signals_removed": False,
        "close_rows": len(closes),
        "missing_rows": missing,
        "contribution_agree": agree,
        "contribution_oppose": oppose,
        "contribution_zero": zero,
        "closes_with_opposition": sum(1 for value in shares_opp if value > 0),
        "opposition_weight_share_min": None if not shares_opp else round(min(shares_opp), 4),
        "opposition_weight_share_max": None if not shares_opp else round(max(shares_opp), 4),
        "zero_weight_share_min": None if not shares_zero else round(min(shares_zero), 4),
        "zero_weight_share_max": None if not shares_zero else round(max(shares_zero), 4),
        "always_zero": always_zero,
        "always_opposes": always_opposes,
        "never_agrees": never_agrees,
        "signals": signals,
        "status": status,
    }


def write_signal_dissent(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.signal_dissent.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_signal_dissent(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "signal_dissent.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_exit_slippage(root: Path) -> dict[str, Any]:
    """Signed quote move minus signed fill move. This drag is not a cash gap."""
    from collections import defaultdict

    drag = defaultdict(float)
    counts = defaultdict(int)
    missing = 0
    closes = _paired_closes(root)
    for row, _opened in closes:
        direction = _direction(row)
        entry = row.get("entry_price")
        quote = row.get("quote_price")
        fill = row.get("fill_price")
        if (direction is None or not isinstance(entry, (int, float)) or not entry
                or not isinstance(quote, (int, float)) or not isinstance(fill, (int, float))):
            missing += 1
            continue
        quote_move = (float(quote) - float(entry)) / float(entry) * direction
        fill_move = (float(fill) - float(entry)) / float(entry) * direction
        reason = str(row.get("reason") or "MISSING")
        drag[reason] += quote_move - fill_move
        counts[reason] += 1
    reasons = [{
        "reason": reason,
        "rows": counts[reason],
        "drag": round(drag[reason], 6),
    } for reason in sorted(drag)]
    if not closes:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    else:
        status = "DRAG_RECORDED"
    return {
        "paper_only": True,
        "edge_claimed": False,
        "added_to_cash_gap": False,
        "close_rows": len(closes),
        "missing_rows": missing,
        "drag_sum": round(sum(drag.values()), 6),
        "reasons": reasons,
        "status": status,
    }


def write_exit_slippage(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.exit_slippage.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_exit_slippage(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "exit_slippage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_path_storage(root: Path) -> dict[str, Any]:
    """The path keys are either on the close or they are not. Absence is not zero."""
    closes = [row for row in _log_rows(root) if row.get("event") == "CLOSE"]
    holds = [row for row in _log_rows(root) if row.get("event") == "HOLD"]
    missing_mae = missing_mfe = missing_points = missing_partial = stored = 0
    for row in closes:
        has_mae = isinstance(row.get("mae"), (int, float))
        has_mfe = isinstance(row.get("mfe"), (int, float))
        has_points = isinstance(row.get("path_points"), int)
        if not has_mae:
            missing_mae += 1
        if not has_mfe:
            missing_mfe += 1
        if not has_points:
            missing_points += 1
        if "partial" not in row:
            missing_partial += 1
        if has_mae and has_mfe and has_points:
            stored += 1
    if not closes:
        status = "NO_CLOSED_ROWS"
    elif stored == len(closes):
        status = "PATH_STORED"
    elif stored == 0 and missing_mae == missing_mfe == missing_points == len(closes):
        status = "PATH_NOT_STORED"
    else:
        status = "PATH_PARTIAL"
    return {
        "paper_only": True,
        "path_backfilled": False,
        "exit_inferred": False,
        "close_rows": len(closes),
        "path_stored_rows": stored,
        "missing_mae": missing_mae,
        "missing_mfe": missing_mfe,
        "missing_path_points": missing_points,
        "missing_partial": missing_partial,
        "hold_rows": len(holds),
        "hold_with_mfe": sum(1 for row in holds if isinstance(row.get("mfe"), (int, float))),
        "hold_with_chandelier": sum(1 for row in holds if isinstance(row.get("chandelier_stop"), (int, float))),
        "status": status,
    }


def write_path_storage(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.path_storage.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_path_storage(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "path_storage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_take_field(root: Path) -> dict[str, Any]:
    """Stored take against stored stop. One digit of storage is not a new multiple."""
    from architecture.markets.paper_trader import TAKE_MULT

    storage_unit = 1e-5
    opens = [row for row in _log_rows(root) if row.get("event") == "OPEN"]
    missing = within = beyond = 0
    gaps: list[float] = []
    for row in opens:
        stop = row.get("stop_pct")
        take = row.get("take_pct")
        if not isinstance(stop, (int, float)) or not stop or not isinstance(take, (int, float)):
            missing += 1
            continue
        gap = abs(float(take) - float(stop) * TAKE_MULT)
        gaps.append(gap)
        if gap <= storage_unit + 1e-12:
            within += 1
        else:
            beyond += 1
    if not opens:
        status = "NO_OPEN_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif beyond == 0:
        status = "WITHIN_STORAGE_PRECISION"
    else:
        status = "BEYOND_STORAGE_PRECISION"
    return {
        "paper_only": True,
        "multiple_changed": False,
        "take_multiple": TAKE_MULT,
        "storage_unit": storage_unit,
        "open_rows": len(opens),
        "missing_rows": missing,
        "within_storage": within,
        "beyond_storage": beyond,
        "max_abs_gap": None if not gaps else round(max(gaps), 8),
        "status": status,
    }


def write_take_field(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.take_field.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_take_field(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "take_field.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _cost_schedule(symbol: str) -> tuple[float, float] | None:
    from architecture.markets.paper_trader import DEX_FEE, DEX_SLIP, INSTRUMENTS

    if symbol.startswith("DEX_"):
        return float(DEX_FEE), float(DEX_SLIP)
    spec = INSTRUMENTS.get(symbol)
    if spec is None:
        return None
    return float(spec[1]), float(spec[2])


def measure_cost_schedule(root: Path) -> dict[str, Any]:
    """Open fee and both slips against the instrument table. The table is not an edge."""
    opens = [row for row in _log_rows(root) if row.get("event") == "OPEN"]
    closes = [row for row in _log_rows(root) if row.get("event") == "CLOSE"]
    missing = open_fee_mismatch = open_slip_mismatch = close_slip_mismatch = 0
    for row in opens:
        schedule = _cost_schedule(str(row.get("symbol") or ""))
        fee = row.get("fee_usd")
        notional = row.get("notional_usd")
        slip = row.get("slippage_pct")
        if (schedule is None or not isinstance(fee, (int, float)) or not isinstance(notional, (int, float))
                or not notional or not isinstance(slip, (int, float))):
            missing += 1
            continue
        fee_rate, slip_rate = schedule
        if abs(float(fee) / float(notional) - fee_rate) > 1e-6:
            open_fee_mismatch += 1
        if abs(float(slip) - slip_rate) > 1e-9:
            open_slip_mismatch += 1
    for row in closes:
        schedule = _cost_schedule(str(row.get("symbol") or ""))
        slip = row.get("slippage_pct")
        if schedule is None or not isinstance(slip, (int, float)):
            missing += 1
            continue
        if abs(float(slip) - schedule[1]) > 1e-9:
            close_slip_mismatch += 1
    if not opens and not closes:
        status = "NO_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif open_fee_mismatch or open_slip_mismatch or close_slip_mismatch:
        status = "SCHEDULE_MISMATCH"
    else:
        status = "SCHEDULE_HELD"
    return {
        "paper_only": True,
        "edge_claimed": False,
        "schedule_changed": False,
        "close_fee_compared": False,
        "open_rows": len(opens),
        "close_rows": len(closes),
        "missing_rows": missing,
        "open_fee_mismatch": open_fee_mismatch,
        "open_slip_mismatch": open_slip_mismatch,
        "close_slip_mismatch": close_slip_mismatch,
        "status": status,
    }


def write_cost_schedule(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.cost_schedule.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_cost_schedule(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "cost_schedule.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_witness_reason(root: Path) -> dict[str, Any]:
    """The stored verdict against the exit reason. The exit order is not changed."""
    conflict = conflict_ok = other = other_ok = missing = 0
    opens = open_ok = open_missing = 0
    for row in _log_rows(root):
        event = row.get("event")
        witness = row.get("witness") if isinstance(row.get("witness"), dict) else None
        verdict = witness.get("verdict") if witness else None
        if event == "OPEN":
            opens += 1
            if verdict == "VERIFIED":
                open_ok += 1
            else:
                open_missing += 1
            continue
        if event != "CLOSE":
            continue
        reason = row.get("reason")
        if not reason or verdict is None:
            missing += 1
            continue
        if reason == "WITNESS_CONFLICT_EXIT":
            conflict += 1
            if verdict == "CONFLICT":
                conflict_ok += 1
        else:
            other += 1
            if verdict == "VERIFIED":
                other_ok += 1
    closes = conflict + other + missing
    if closes == 0:
        status = "NO_CLOSED_ROWS"
    elif missing or conflict_ok != conflict or other_ok != other or open_missing:
        status = "INCOMPLETE" if missing or open_missing else "VERDICT_MISMATCH"
    else:
        status = "VERDICT_MATCHES_REASON"
    return {
        "paper_only": True,
        "exit_rule_changed": False,
        "close_rows": closes,
        "missing_rows": missing,
        "conflict_rows": conflict,
        "conflict_verdict_conflict": conflict_ok,
        "other_rows": other,
        "other_verdict_verified": other_ok,
        "open_rows": opens,
        "open_verified": open_ok,
        "open_missing": open_missing,
        "status": status,
    }


def write_witness_reason(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.witness_reason.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_witness_reason(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "witness_reason.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_fee_decomposition(root: Path) -> dict[str, Any]:
    """Close fee against the open fee plus the exit fee. This is not a cash gap."""
    band = 1e-6
    within = beyond = missing = fraction_not_one = 0
    gaps: list[float] = []
    for row, opened in _paired_closes(root):
        schedule = _cost_schedule(str(row.get("symbol") or ""))
        fees = row.get("fees_usd")
        fill = row.get("fill_price")
        qty = row.get("qty")
        close_notional = row.get("notional_usd")
        open_fee = (opened or {}).get("fee_usd") if isinstance(opened, dict) else None
        open_notional = (opened or {}).get("notional_usd") if isinstance(opened, dict) else None
        if (schedule is None or not isinstance(fees, (int, float)) or not isinstance(fill, (int, float))
                or not isinstance(qty, (int, float)) or not isinstance(open_fee, (int, float))
                or not isinstance(close_notional, (int, float)) or not isinstance(open_notional, (int, float))
                or not open_notional):
            missing += 1
            continue
        fraction = float(close_notional) / float(open_notional)
        if abs(fraction - 1.0) > 1e-4:
            fraction_not_one += 1
        gap = abs(float(fees) - (float(open_fee) * fraction + float(fill) * float(qty) * schedule[0]))
        gaps.append(gap)
        if gap <= band:
            within += 1
        else:
            beyond += 1
    closes = within + beyond + missing
    if closes == 0:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif beyond == 0:
        status = "FEE_DECOMPOSED"
    else:
        status = "FEE_BEYOND_BAND"
    return {
        "paper_only": True,
        "edge_claimed": False,
        "added_to_cash_gap": False,
        "fee_band": band,
        "close_rows": closes,
        "missing_rows": missing,
        "within_band": within,
        "beyond_band": beyond,
        "fraction_not_one": fraction_not_one,
        "max_abs_gap": None if not gaps else round(max(gaps), 8),
        "status": status,
    }


def write_fee_decomposition(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.fee_decomposition.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_fee_decomposition(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "fee_decomposition.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_equity_replay(root: Path) -> dict[str, Any]:
    """Logged equity at each open against the sum of earlier close pnl. The residual is not a cash gap."""
    from architecture.markets.paper_account import INITIAL_CAPITAL_USD

    cent = 0.01
    equity = float(INITIAL_CAPITAL_USD)
    missing = within = beyond = opens = 0
    gaps: list[float] = []
    for row in _log_rows(root):
        if row.get("event") == "OPEN":
            opens += 1
            logged = row.get("equity_at_open_usd")
            if not isinstance(logged, (int, float)):
                missing += 1
                continue
            gap = abs(float(logged) - equity)
            gaps.append(gap)
            if gap <= cent:
                within += 1
            else:
                beyond += 1
        elif row.get("event") == "CLOSE" and isinstance(row.get("realized_pnl_usd"), (int, float)):
            equity += float(row["realized_pnl_usd"])
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif beyond == 0:
        status = "WITHIN_ONE_CENT"
    else:
        status = "BEYOND_ONE_CENT"
    return {
        "paper_only": True,
        "equity_rewritten": False,
        "added_to_cash_gap": False,
        "initial_capital_usd": float(INITIAL_CAPITAL_USD),
        "cent_band": cent,
        "open_rows": opens,
        "missing_rows": missing,
        "within_cent": within,
        "beyond_cent": beyond,
        "max_abs_gap": None if not gaps else round(max(gaps), 4),
        "end_equity_usd": round(equity, 4),
        "status": status,
    }


def write_equity_replay(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.equity_replay.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_equity_replay(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "equity_replay.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _parse_stamp(value: object) -> datetime | None:
    try:
        return datetime.strptime(str(value), "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        return None


def measure_quote_age(root: Path) -> dict[str, Any]:
    """Age of the stored quote at the log stamp. The stale gate is not changed."""
    from architecture.markets.paper_trader import MAX_TRADE_AGE_S

    cells = {
        "OPEN": {"rows": 0, "missing": 0, "over_gate": 0, "clock_ahead": 0, "ages": [], "ahead": []},
        "CLOSE": {"rows": 0, "missing": 0, "over_gate": 0, "clock_ahead": 0, "ages": [], "ahead": []},
    }
    for row in _log_rows(root):
        event = row.get("event")
        if event not in cells:
            continue
        cell = cells[event]
        cell["rows"] += 1
        stamped = _parse_stamp(row.get("ts"))
        market = _parse_stamp(row.get("market_time"))
        if stamped is None or market is None:
            cell["missing"] += 1
            continue
        age = (stamped - market).total_seconds()
        cell["ages"].append(age)
        if age > MAX_TRADE_AGE_S:
            cell["over_gate"] += 1
        if age < 0:
            cell["clock_ahead"] += 1
            cell["ahead"].append(-age)
    opens, closes = cells["OPEN"], cells["CLOSE"]
    if opens["rows"] == 0 and closes["rows"] == 0:
        status = "NO_ROWS"
    elif opens["missing"] or closes["missing"]:
        status = "INCOMPLETE"
    elif opens["over_gate"] == 0 and closes["over_gate"] == 0:
        status = "WITHIN_STALE_GATE"
    else:
        status = "BEYOND_STALE_GATE"
    def _max(values: list[float]) -> float | None:
        return None if not values else round(max(values), 1)

    return {
        "paper_only": True,
        "gate_changed": False,
        "gate_seconds": MAX_TRADE_AGE_S,
        "open_rows": opens["rows"],
        "close_rows": closes["rows"],
        "open_missing": opens["missing"],
        "close_missing": closes["missing"],
        "open_over_gate": opens["over_gate"],
        "close_over_gate": closes["over_gate"],
        "open_clock_ahead": opens["clock_ahead"],
        "close_clock_ahead": closes["clock_ahead"],
        "open_age_max_s": _max(opens["ages"]),
        "close_age_max_s": _max(closes["ages"]),
        "open_ahead_max_s": _max(opens["ahead"]),
        "close_ahead_max_s": _max(closes["ahead"]),
        "status": status,
    }


def write_quote_age(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.quote_age.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_quote_age(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "quote_age.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _source_kind(source: object) -> str:
    text = str(source or "")
    kind = text.split(":", 1)[0] if text else "MISSING"
    if "0x" in kind.lower() or not kind:
        return "ADDRESS_SHAPED_KIND"
    return kind


def measure_source_address(root: Path) -> dict[str, Any]:
    """Count log sources that still carry an address. The receipt does not copy it."""
    from collections import defaultdict

    counts: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    open_addr = close_addr = 0
    for row in _log_rows(root):
        event = row.get("event")
        if event not in ("OPEN", "CLOSE"):
            continue
        source = str(row.get("source") or "")
        kind = _source_kind(source)
        slot = 0 if event == "OPEN" else 1
        counts[kind][slot] += 1
        if "0x" in source.lower():
            if event == "OPEN":
                open_addr += 1
            else:
                close_addr += 1
    kinds = [{
        "kind": kind,
        "open_rows": counts[kind][0],
        "close_rows": counts[kind][1],
    } for kind in sorted(counts)]
    if open_addr or close_addr:
        status = "ADDRESS_ON_LOG"
    elif not kinds:
        status = "NO_ROWS"
    else:
        status = "NO_ADDRESS"
    return {
        "paper_only": True,
        "log_rewritten": False,
        "open_with_address": open_addr,
        "close_with_address": close_addr,
        "kinds": kinds,
        "status": status,
    }


def write_source_address(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.source_address.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_source_address(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "source_address.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(snap, ensure_ascii=False, indent=1)
    if "0x" in text.lower():
        raise RuntimeError("source address receipt copied an address")
    path.write_text(text, encoding="utf-8")
    return snap


def measure_book_overlap(root: Path) -> dict[str, Any]:
    """One open per symbol until it closes. Nothing is closed from this count."""
    from collections import defaultdict, deque

    queues: dict[str, deque] = defaultdict(deque)
    overlap = unpaired = opened_match = closed_match = closes = 0
    for row in _log_rows(root):
        symbol = str(row.get("symbol") or "")
        if row.get("event") == "OPEN":
            if queues[symbol]:
                overlap += 1
            queues[symbol].append(row)
        elif row.get("event") == "CLOSE":
            closes += 1
            opened = queues[symbol].popleft() if queues[symbol] else None
            if opened is None:
                unpaired += 1
                continue
            if row.get("opened_at") == opened.get("ts"):
                opened_match += 1
            if row.get("closed_at") == row.get("ts"):
                closed_match += 1
    still_open = sorted(symbol for symbol, queue in queues.items() if queue)
    if overlap or unpaired:
        status = "OVERLAP"
    elif closes == 0 and not still_open:
        status = "NO_ROWS"
    else:
        status = "NO_OVERLAP"
    return {
        "paper_only": True,
        "positions_closed": False,
        "overlap_opens": overlap,
        "unpaired_closes": unpaired,
        "close_rows": closes,
        "opened_at_matches_open_ts": opened_match,
        "closed_at_matches_ts": closed_match,
        "still_open": still_open,
        "status": status,
    }


def write_book_overlap(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.book_overlap.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_book_overlap(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "book_overlap.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_refusal_gate(root: Path) -> dict[str, Any]:
    """A below-entry refusal is inside 0.25. Any other refusal has already cleared it."""
    from architecture.markets.paper_trader import ENTRY

    below = below_inside = below_outside = other = other_above = missing = 0
    below_abs: list[float] = []
    other_abs: list[float] = []
    for row in _log_rows(root):
        if row.get("event") != "NO_TRADE":
            continue
        comp = row.get("composite")
        if not isinstance(comp, (int, float)):
            missing += 1
            continue
        mag = abs(float(comp))
        if row.get("reason") == "COMPOSITE_BELOW_ENTRY":
            below += 1
            below_abs.append(mag)
            if mag < ENTRY:
                below_inside += 1
            else:
                below_outside += 1
        else:
            other += 1
            other_abs.append(mag)
            if mag >= ENTRY:
                other_above += 1
    rows = below + other + missing
    if rows == 0:
        status = "NO_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif below_outside == 0 and other_above == other:
        status = "GATE_HELD"
    else:
        status = "GATE_BROKEN"
    return {
        "paper_only": True,
        "gate_changed": False,
        "threshold": ENTRY,
        "rows": rows,
        "missing_rows": missing,
        "below_rows": below,
        "below_inside": below_inside,
        "below_outside": below_outside,
        "other_rows": other,
        "other_at_or_above": other_above,
        "below_abs_max": None if not below_abs else round(max(below_abs), 4),
        "other_abs_min": None if not other_abs else round(min(other_abs), 4),
        "status": status,
    }


def write_refusal_gate(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.refusal_gate.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_refusal_gate(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "refusal_gate.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_quantity_identity(root: Path) -> dict[str, Any]:
    """Quantity times the entry fill against notional. The dust is not a cash gap."""
    band = 1e-6
    within = beyond = missing = opens = closes = 0
    gaps: list[float] = []
    for row in _log_rows(root):
        event = row.get("event")
        if event == "OPEN":
            opens += 1
            left, right = row.get("fill_price"), row.get("qty")
        elif event == "CLOSE":
            closes += 1
            left, right = row.get("entry_price"), row.get("qty")
        else:
            continue
        notional = row.get("notional_usd")
        if not all(isinstance(v, (int, float)) and v for v in (left, right, notional)):
            missing += 1
            continue
        gap = abs(float(right) * float(left) - float(notional))
        gaps.append(gap)
        if gap <= band:
            within += 1
        else:
            beyond += 1
    if opens == 0 and closes == 0:
        status = "NO_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif beyond == 0:
        status = "QTY_MATCHES"
    else:
        status = "QTY_BEYOND"
    return {
        "paper_only": True,
        "added_to_cash_gap": False,
        "qty_band": band,
        "open_rows": opens,
        "close_rows": closes,
        "missing_rows": missing,
        "within_band": within,
        "beyond_band": beyond,
        "max_abs_gap": None if not gaps else round(max(gaps), 8),
        "status": status,
    }


def write_quantity_identity(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.quantity_identity.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_quantity_identity(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "quantity_identity.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_size_cap(root: Path) -> dict[str, Any]:
    """Notional against the risk line and the desk line. Neither cap is changed."""
    from architecture.markets.paper_trader import DESK_WEIGHTS, INSTRUMENTS, RISK_PER_TRADE

    money_band = 0.01
    per_n = {desk: max(1, sum(1 for spec in INSTRUMENTS.values() if spec[0] == desk)) for desk in DESK_WEIGHTS}
    missing = defaulted = risk_above = desk_above = scored = 0
    risk_ratios: list[float] = []
    desk_ratios: list[float] = []
    opens = 0
    for row in _log_rows(root):
        if row.get("event") != "OPEN":
            continue
        opens += 1
        brain = row.get("brain") if isinstance(row.get("brain"), dict) else {}
        regime = brain.get("regime") if isinstance(brain.get("regime"), dict) else {}
        size_mult = regime.get("size_mult")
        event_mult = brain.get("event_size_mult")
        equity = row.get("equity_at_open_usd")
        stop = row.get("stop_pct")
        notional = row.get("notional_usd")
        desk = row.get("desk")
        if (desk not in DESK_WEIGHTS or not isinstance(size_mult, (int, float)) or not size_mult
                or not isinstance(equity, (int, float)) or not equity
                or not isinstance(stop, (int, float)) or not stop
                or not isinstance(notional, (int, float))):
            missing += 1
            continue
        if not isinstance(event_mult, (int, float)):
            defaulted += 1
            event_mult = 1.0
        risk_line = float(equity) * RISK_PER_TRADE / float(stop) * float(size_mult) * float(event_mult)
        desk_line = float(equity) * DESK_WEIGHTS[desk] / per_n[desk] * float(size_mult) * float(event_mult)
        scored += 1
        if risk_line:
            risk_ratios.append(float(notional) / risk_line)
        if desk_line:
            desk_ratios.append(float(notional) / desk_line)
        if float(notional) > risk_line + money_band:
            risk_above += 1
        if float(notional) > desk_line + money_band:
            desk_above += 1
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif risk_above == 0 and desk_above == 0:
        status = "INSIDE_DESK_AND_RISK"
    else:
        status = "ABOVE_CAP"
    return {
        "paper_only": True,
        "caps_changed": False,
        "kelly_switched_on": False,
        "money_band": money_band,
        "open_rows": opens,
        "scored_rows": scored,
        "missing_rows": missing,
        "event_size_defaulted": defaulted,
        "risk_above": risk_above,
        "desk_above": desk_above,
        "risk_ratio_max": None if not risk_ratios else round(max(risk_ratios), 4),
        "desk_ratio_max": None if not desk_ratios else round(max(desk_ratios), 4),
        "status": status,
    }


def write_size_cap(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.size_cap.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_size_cap(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "size_cap.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


_REGIME_SIZE = {"HIGH": 0.5, "NORMAL": 1.0, "LOW": 0.8, "UNKNOWN": 0.5}


def measure_adv_cap(root: Path) -> dict[str, Any]:
    """Stored participation against the one-percent cap. The cap is not changed."""
    from collections import Counter

    sources: Counter[str] = Counter()
    missing_object = source_blank = floor = mismatch = over = stored = 0
    rates: list[float] = []
    for row in _log_rows(root):
        if row.get("event") != "OPEN":
            continue
        brain = row.get("brain") if isinstance(row.get("brain"), dict) else {}
        adv = brain.get("adv_cap") if isinstance(brain.get("adv_cap"), dict) else None
        if adv is None:
            missing_object += 1
            continue
        stored += 1
        raw = adv.get("adv_source")
        label = str(raw or "BLANK")
        if "0x" in label.lower():
            label = "ADDRESS_SHAPED"
        sources[label] += 1
        if not raw:
            source_blank += 1
        if raw == "ASSUMED_FLOOR_50M_NO_VOLUME_IN_FEED":
            floor += 1
        rate = adv.get("participation_rate")
        if isinstance(rate, (int, float)):
            rates.append(float(rate))
            if float(rate) > 0.01:
                over += 1
        notional = adv.get("notional_usd")
        cap = adv.get("cap_1pct_usd")
        if isinstance(notional, (int, float)) and isinstance(cap, (int, float)):
            if bool(adv.get("allowed")) != (float(notional) <= float(cap)):
                mismatch += 1
        else:
            mismatch += 1
    opens = stored + missing_object
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif stored == 0:
        status = "NO_STORED_CAP"
    elif mismatch == 0 and over == 0 and floor == 0:
        status = "CAP_HELD"
    else:
        status = "CAP_BROKEN"
    return {
        "paper_only": True,
        "cap_changed": False,
        "edge_claimed": False,
        "open_rows": opens,
        "stored_rows": stored,
        "missing_object": missing_object,
        "source_blank": source_blank,
        "assumed_floor_rows": floor,
        "allowed_mismatch": mismatch,
        "rate_over_1pct": over,
        "participation_rate_max": None if not rates else round(max(rates), 10),
        "sources": [{"source": name, "rows": sources[name]} for name in sorted(sources)],
        "status": status,
    }


def write_adv_cap(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.adv_cap.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_adv_cap(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "adv_cap.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(snap, ensure_ascii=False, indent=1)
    if "0x" in text.lower():
        raise RuntimeError("adv cap receipt copied an address")
    path.write_text(text, encoding="utf-8")
    return snap


def measure_regime_multiple(root: Path) -> dict[str, Any]:
    """Stored size multiple against the regime table. The table is not changed."""
    matched = mismatched = missing = haircut = unknown = 0
    opens = 0
    for row in _log_rows(root):
        if row.get("event") != "OPEN":
            continue
        opens += 1
        brain = row.get("brain") if isinstance(row.get("brain"), dict) else {}
        regime = brain.get("regime") if isinstance(brain.get("regime"), dict) else {}
        label = regime.get("regime")
        mult = regime.get("size_mult")
        if label not in _REGIME_SIZE or not isinstance(mult, (int, float)):
            missing += 1
            continue
        if label == "UNKNOWN":
            unknown += 1
        expected = _REGIME_SIZE[label]
        if regime.get("depth_disagreement_haircut") is True:
            haircut += 1
            expected = round(expected * 0.5, 4)
        if abs(float(mult) - expected) <= 1e-9:
            matched += 1
        else:
            mismatched += 1
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif mismatched == 0:
        status = "MULTIPLE_MATCHES"
    else:
        status = "MULTIPLE_MISMATCH"
    return {
        "paper_only": True,
        "multiple_changed": False,
        "open_rows": opens,
        "matched_rows": matched,
        "mismatched_rows": mismatched,
        "missing_rows": missing,
        "haircut_rows": haircut,
        "unknown_rows": unknown,
        "status": status,
    }


def write_regime_multiple(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.regime_multiple.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_regime_multiple(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "regime_multiple.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_higher_tf(root: Path) -> dict[str, Any]:
    """Stored higher-timeframe sign against the open side. The rule is not changed."""
    agree = disagree = missing = 0
    for row in _log_rows(root):
        if row.get("event") != "OPEN":
            continue
        brain = row.get("brain") if isinstance(row.get("brain"), dict) else {}
        signals = brain.get("signals") if isinstance(brain.get("signals"), list) else []
        higher = None
        for item in signals:
            if not isinstance(item, dict) or item.get("name") != "mtf_trend":
                continue
            evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
            higher = evidence.get("higher_tf_sign")
        side = row.get("side")
        if not isinstance(higher, (int, float)) or side not in ("LONG", "SHORT"):
            missing += 1
            continue
        want = 1 if side == "LONG" else -1
        if int(higher) == want:
            agree += 1
        else:
            disagree += 1
    opens = agree + disagree + missing
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif agree == 0 and disagree == 0:
        status = "NO_STORED_SIGN"
    elif disagree == 0:
        status = "SIGN_AGREES"
    else:
        status = "SIGN_DISAGREES"
    return {
        "paper_only": True,
        "rule_changed": False,
        "open_rows": opens,
        "agree_rows": agree,
        "disagree_rows": disagree,
        "missing_rows": missing,
        "status": status,
    }


def write_higher_tf(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.higher_tf.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_higher_tf(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "higher_tf.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_pnl_identity(root: Path) -> dict[str, Any]:
    """Stored close pnl against rounded gross minus fees. The match is not a cash gap."""
    band = 0.0001
    within = beyond = missing = 0
    gaps: list[float] = []
    for row in _log_rows(root):
        if row.get("event") != "CLOSE":
            continue
        direction = _direction(row)
        entry, fill, qty = row.get("entry_price"), row.get("fill_price"), row.get("qty")
        fees, pnl = row.get("fees_usd"), row.get("realized_pnl_usd")
        if (direction is None or not isinstance(fees, (int, float)) or not isinstance(pnl, (int, float))
                or not all(isinstance(v, (int, float)) and v for v in (entry, fill, qty))):
            missing += 1
            continue
        gross = (float(fill) - float(entry)) * float(qty) * direction
        gap = abs(round(gross - float(fees), 4) - float(pnl))
        gaps.append(gap)
        if gap <= band:
            within += 1
        else:
            beyond += 1
    closes = within + beyond + missing
    if closes == 0:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif beyond == 0:
        status = "PNL_IDENTITY"
    else:
        status = "PNL_BEYOND"
    return {
        "paper_only": True,
        "added_to_cash_gap": False,
        "edge_claimed": False,
        "pnl_band": band,
        "close_rows": closes,
        "missing_rows": missing,
        "within_band": within,
        "beyond_band": beyond,
        "max_abs_gap": None if not gaps else round(max(gaps), 4),
        "status": status,
    }


def write_pnl_identity(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.pnl_identity.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_pnl_identity(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "pnl_identity.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_gross_sign(root: Path) -> dict[str, Any]:
    """Sign of price gross by exit reason. A positive gross is not an edge."""
    from collections import defaultdict

    cells: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    missing = 0
    for row in _log_rows(root):
        if row.get("event") != "CLOSE":
            continue
        direction = _direction(row)
        entry, fill, qty = row.get("entry_price"), row.get("fill_price"), row.get("qty")
        if direction is None or not all(isinstance(v, (int, float)) and v for v in (entry, fill, qty)):
            missing += 1
            continue
        gross = (float(fill) - float(entry)) * float(qty) * direction
        reason = str(row.get("reason") or "MISSING")
        cells[reason][0] += 1
        if gross > 0:
            cells[reason][1] += 1
        elif gross < 0:
            cells[reason][2] += 1
    reasons = [{
        "reason": reason,
        "rows": cells[reason][0],
        "gross_positive": cells[reason][1],
        "gross_negative": cells[reason][2],
    } for reason in sorted(cells)]
    closes = sum(item["rows"] for item in reasons) + missing
    if closes == 0:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    else:
        status = "GROSS_RECORDED"
    return {
        "paper_only": True,
        "edge_claimed": False,
        "exit_rule_changed": False,
        "close_rows": closes,
        "missing_rows": missing,
        "gross_positive": sum(item["gross_positive"] for item in reasons),
        "gross_negative": sum(item["gross_negative"] for item in reasons),
        "reasons": reasons,
        "status": status,
    }


def write_gross_sign(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.gross_sign.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_gross_sign(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "gross_sign.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_debate_claim(root: Path) -> dict[str, Any]:
    """Flags stored on the open debate. A stored approval is not canonical authority."""
    from collections import Counter

    stored = missing = approved_true = swap_true = brier_present = ece_present = 0
    statuses: Counter[str] = Counter()
    for row in _log_rows(root):
        if row.get("event") != "OPEN":
            continue
        brain = row.get("brain") if isinstance(row.get("brain"), dict) else {}
        debate = brain.get("council_debate")
        if not isinstance(debate, dict):
            missing += 1
            continue
        stored += 1
        if debate.get("approved_paper") is True:
            approved_true += 1
        if debate.get("swap_gate_passed") is True:
            swap_true += 1
        if debate.get("brier_judge") is not None:
            brier_present += 1
        if debate.get("ece_judge") is not None:
            ece_present += 1
        statuses[str(debate.get("status") or "MISSING")] += 1
    opens = stored + missing
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif stored == 0:
        status = "NO_STORED_DEBATE"
    elif approved_true or brier_present or swap_true:
        status = "STORED_CLAIM_NOT_AUTHORITY"
    else:
        status = "NO_APPROVAL_CLAIM"
    return {
        "paper_only": True,
        "authority_used": False,
        "log_rewritten": False,
        "open_rows": opens,
        "stored_rows": stored,
        "missing_rows": missing,
        "approved_true": approved_true,
        "swap_true": swap_true,
        "brier_present": brier_present,
        "ece_present": ece_present,
        "statuses": [{"status": name, "rows": statuses[name]} for name in sorted(statuses)],
        "status": status,
    }


def write_debate_claim(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.debate_claim.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_debate_claim(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "debate_claim.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_fill_formula(root: Path) -> dict[str, Any]:
    """Stored fill against the quote and the stored slippage. The formula is not changed."""
    band = 1e-6
    within = beyond = missing = open_rows = close_rows = 0
    gaps: list[float] = []
    for row in _log_rows(root):
        event = row.get("event")
        if event not in ("OPEN", "CLOSE"):
            continue
        if event == "OPEN":
            open_rows += 1
        else:
            close_rows += 1
        direction = _direction(row)
        quote, fill, slip = row.get("quote_price"), row.get("fill_price"), row.get("slippage_pct")
        if (direction is None or not isinstance(slip, (int, float))
                or not isinstance(quote, (int, float)) or not quote
                or not isinstance(fill, (int, float)) or not fill):
            missing += 1
            continue
        sign = 1.0 if event == "OPEN" else -1.0
        expect = round(float(quote) * (1.0 + sign * float(slip) * direction), 6)
        gap = abs(expect - float(fill))
        gaps.append(gap)
        if gap <= band:
            within += 1
        else:
            beyond += 1
    rows = open_rows + close_rows
    if rows == 0:
        status = "NO_FILL_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif beyond == 0:
        status = "FILL_FORMULA"
    else:
        status = "FILL_BEYOND"
    return {
        "paper_only": True,
        "formula_changed": False,
        "added_to_cash_gap": False,
        "edge_claimed": False,
        "fill_band": band,
        "open_rows": open_rows,
        "close_rows": close_rows,
        "missing_rows": missing,
        "within_band": within,
        "beyond_band": beyond,
        "max_abs_gap": None if not gaps else round(max(gaps), 6),
        "status": status,
    }


def write_fill_formula(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.fill_formula.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_fill_formula(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "fill_formula.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_open_composite(root: Path) -> dict[str, Any]:
    """Signed open composite against the recorded gate. The score is not a probability."""
    from architecture.markets.paper_trader import ENTRY
    from collections import defaultdict, deque

    signed: list[float] = []
    missing = below = 0
    queues: dict[str, deque] = defaultdict(deque)
    copied = differ = copy_missing = 0
    for row in _log_rows(root):
        event = row.get("event")
        if event == "OPEN":
            queues[str(row.get("symbol"))].append(row)
            brain = row.get("brain") if isinstance(row.get("brain"), dict) else {}
            composite = brain.get("composite")
            direction = _direction(row)
            if direction is None or not isinstance(composite, (int, float)):
                missing += 1
                continue
            value = round(float(composite) * direction, 4)
            signed.append(value)
            if value < ENTRY:
                below += 1
        elif event == "CLOSE":
            opened = queues[str(row.get("symbol"))].popleft() if queues[str(row.get("symbol"))] else None
            open_brain = opened.get("brain") if isinstance(opened, dict) and isinstance(opened.get("brain"), dict) else {}
            close_brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
            left, right = open_brain.get("composite"), close_brain.get("composite")
            if opened is None or not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
                copy_missing += 1
            elif left == right:
                copied += 1
            else:
                differ += 1
    opens = len(signed) + missing
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif missing or copy_missing:
        status = "INCOMPLETE"
    elif below:
        status = "BELOW_RECORDED_THRESHOLD"
    elif differ:
        status = "COPY_DIFFERS"
    else:
        status = "GATE_HELD_NOT_A_PROBABILITY"
    return {
        "paper_only": True,
        "gate_changed": False,
        "edge_claimed": False,
        "threshold": ENTRY,
        "brier": None,
        "open_rows": opens,
        "missing_rows": missing,
        "below_gate": below,
        "signed_min": None if not signed else round(min(signed), 4),
        "signed_max": None if not signed else round(max(signed), 4),
        "copied_rows": copied,
        "differ_rows": differ,
        "copy_missing_rows": copy_missing,
        "status": status,
    }


def write_open_composite(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.open_composite.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_open_composite(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "open_composite.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_cluster_cap(root: Path) -> dict[str, Any]:
    """Simultaneous notional against the cluster cap. This measure closes nothing."""
    from architecture.markets.paper_trader import CLUSTER_CAPS, CLUSTER_OF_DESK, MAX_OPEN_NOTIONAL

    money_band = 0.01
    book: dict[str, dict[str, float | str]] = {}
    missing = above_cluster = above_gross = scored = 0
    worst_cap = worst_gross = None
    for row in _log_rows(root):
        event = row.get("event")
        symbol = str(row.get("symbol") or "")
        if event == "OPEN":
            notional, equity = row.get("notional_usd"), row.get("equity_at_open_usd")
            desk = row.get("desk")
            cluster = CLUSTER_OF_DESK.get(str(desk or ""))
            if (not isinstance(notional, (int, float)) or not isinstance(equity, (int, float))
                    or not equity or cluster not in CLUSTER_CAPS):
                missing += 1
                continue
            book[symbol] = {"notional": float(notional), "cluster": cluster}
            totals: dict[str, float] = {}
            for item in book.values():
                name = str(item["cluster"])
                totals[name] = totals.get(name, 0.0) + float(item["notional"])
            gross = sum(float(item["notional"]) for item in book.values())
            scored += 1
            gross_ratio = gross / float(equity)
            worst_gross = gross_ratio if worst_gross is None else max(worst_gross, gross_ratio)
            if gross > MAX_OPEN_NOTIONAL * float(equity) + money_band:
                above_gross += 1
            for name, amount in totals.items():
                cap = CLUSTER_CAPS[name]
                ratio = (amount / float(equity)) / cap if cap else None
                if ratio is not None:
                    worst_cap = ratio if worst_cap is None else max(worst_cap, ratio)
                if amount > cap * float(equity) + money_band:
                    above_cluster += 1
        elif event == "CLOSE" and row.get("partial") is not True:
            book.pop(symbol, None)
    opens = scored + missing
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif above_cluster or above_gross:
        status = "ABOVE_CLUSTER"
    else:
        status = "INSIDE_CLUSTER"
    return {
        "paper_only": True,
        "caps_changed": False,
        "positions_closed": False,
        "edge_claimed": False,
        "money_band": money_band,
        "max_open_multiple": MAX_OPEN_NOTIONAL,
        "caps": {name: CLUSTER_CAPS[name] for name in sorted(CLUSTER_CAPS)},
        "open_rows": opens,
        "scored_rows": scored,
        "missing_rows": missing,
        "above_cluster": above_cluster,
        "above_gross": above_gross,
        "worst_cap_ratio": None if worst_cap is None else round(worst_cap, 4),
        "worst_gross_ratio": None if worst_gross is None else round(worst_gross, 4),
        "still_open": sorted(book),
        "status": status,
    }


def write_cluster_cap(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.cluster_cap.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_cluster_cap(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "cluster_cap.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_stop_floor(root: Path) -> dict[str, Any]:
    """Stored stop against the recorded floor. The floor is not changed."""
    from architecture.markets.paper_trader import MIN_STOP

    missing = below = 0
    stops: list[float] = []
    for row in _log_rows(root):
        if row.get("event") != "OPEN":
            continue
        stop = row.get("stop_pct")
        if not isinstance(stop, (int, float)):
            missing += 1
            continue
        stops.append(float(stop))
        if float(stop) < MIN_STOP - 1e-9:
            below += 1
    opens = len(stops) + missing
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif below:
        status = "BELOW_FLOOR"
    else:
        status = "FLOOR_HELD"
    return {
        "paper_only": True,
        "floor_changed": False,
        "edge_claimed": False,
        "min_stop": MIN_STOP,
        "open_rows": opens,
        "missing_rows": missing,
        "below_floor": below,
        "stop_min": None if not stops else round(min(stops), 5),
        "stop_max": None if not stops else round(max(stops), 5),
        "status": status,
    }


def write_stop_floor(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.stop_floor.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_stop_floor(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "stop_floor.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_entry_screens(root: Path) -> dict[str, Any]:
    """Spread and news on the accepted opens. A missing funding z is not a pass."""
    crypto = other = spread_false = spread_missing = 0
    news_against = news_missing = z_rows = crowded = 0
    for row in _log_rows(root):
        if row.get("event") != "OPEN":
            continue
        desk = row.get("desk")
        if desk == "CRYPTO":
            crypto += 1
        else:
            other += 1
        brain = row.get("brain") if isinstance(row.get("brain"), dict) else {}
        signals = brain.get("signals") if isinstance(brain.get("signals"), list) else []
        names = {item.get("name"): item for item in signals if isinstance(item, dict)}
        direction = _direction(row)
        oflow = names.get("order_flow")
        if desk == "CRYPTO":
            if not isinstance(oflow, dict):
                spread_missing += 1
            elif (oflow.get("evidence") or {}).get("spread_gate_ok") is False:
                spread_false += 1
        fund = names.get("funding_oi")
        z = (fund.get("evidence") or {}).get("funding_z") if isinstance(fund, dict) else None
        if isinstance(z, (int, float)):
            z_rows += 1
            if direction is not None and ((direction > 0 and z >= 2.0) or (direction < 0 and z <= -2.0)):
                crowded += 1
        news = names.get("news")
        score = news.get("score") if isinstance(news, dict) else None
        if not isinstance(news, dict) or not isinstance(score, (int, float)):
            news_missing += 1
        elif news.get("available") and direction is not None and float(score) * direction < -0.5:
            news_against += 1
    opens = crypto + other
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif spread_missing or news_missing:
        status = "INCOMPLETE"
    elif spread_false or news_against or crowded:
        status = "SCREEN_HIT"
    elif z_rows == 0:
        status = "FUNDING_Z_NOT_STORED"
    else:
        status = "SCREENS_HELD"
    return {
        "paper_only": True,
        "rule_changed": False,
        "z_treated_as_clear": False,
        "edge_claimed": False,
        "open_rows": opens,
        "crypto_rows": crypto,
        "other_rows": other,
        "spread_false": spread_false,
        "spread_missing": spread_missing,
        "news_against": news_against,
        "news_missing": news_missing,
        "funding_z_rows": z_rows,
        "funding_crowded": crowded,
        "status": status,
    }


def write_entry_screens(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.entry_screens.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_entry_screens(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "entry_screens.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _row_ts(value: object) -> float | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def measure_loss_limit(root: Path) -> dict[str, Any]:
    """Trailing realized loss against the kill-switch lines. Marks are not included."""
    from architecture.markets.paper_account import INITIAL_CAPITAL_USD
    from architecture.markets.paper_trader import DAILY_LOSS_LIMIT, WEEKLY_LOSS_LIMIT

    closes = []
    missing = 0
    for row in _log_rows(root):
        if row.get("event") != "CLOSE":
            continue
        pnl = row.get("realized_pnl_usd")
        stamp = _row_ts(row.get("closed_at") or row.get("ts"))
        if not isinstance(pnl, (int, float)) or stamp is None:
            missing += 1
            continue
        closes.append((stamp, float(pnl)))
    day_breach = week_breach = 0
    worst_day = worst_week = None
    equity = float(INITIAL_CAPITAL_USD)
    for stamp, pnl in closes:
        equity += pnl
        if equity <= 0:
            missing += 1
            continue
        day = sum(value for when, value in closes if stamp - 86400 < when <= stamp)
        week = sum(value for when, value in closes if stamp - 7 * 86400 < when <= stamp)
        day_ratio = day / equity
        week_ratio = week / equity
        worst_day = day_ratio if worst_day is None else min(worst_day, day_ratio)
        worst_week = week_ratio if worst_week is None else min(worst_week, week_ratio)
        if day < -DAILY_LOSS_LIMIT * equity:
            day_breach += 1
        if week < -WEEKLY_LOSS_LIMIT * equity:
            week_breach += 1
    rows = len(closes) + missing
    if rows == 0:
        status = "NO_CLOSED_ROWS"
    elif missing:
        status = "INCOMPLETE"
    elif day_breach or week_breach:
        status = "LIMIT_BREACHED"
    else:
        status = "INSIDE_LIMIT"
    return {
        "paper_only": True,
        "limits_changed": False,
        "daemon_halted": False,
        "marks_included": False,
        "edge_claimed": False,
        "daily_limit": DAILY_LOSS_LIMIT,
        "weekly_limit": WEEKLY_LOSS_LIMIT,
        "close_rows": rows,
        "missing_rows": missing,
        "day_breaches": day_breach,
        "week_breaches": week_breach,
        "worst_day_ratio": None if worst_day is None else round(worst_day, 4),
        "worst_week_ratio": None if worst_week is None else round(worst_week, 4),
        "status": status,
    }


def write_loss_limit(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.loss_limit.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_loss_limit(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "loss_limit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _atr_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            parts = str(key).lower().replace("-", "_").split("_")
            if "atr" in parts or _atr_key(item):
                return True
        return False
    if isinstance(value, list):
        return any(_atr_key(item) for item in value)
    return False


def measure_atr_stop(root: Path) -> dict[str, Any]:
    """A stop above the floor is not proof of two times ATR. The ATR is not stored."""
    from architecture.markets.paper_trader import MIN_STOP

    on_floor = above = below = missing = atr_stored = 0
    for row in _log_rows(root):
        if row.get("event") != "OPEN":
            continue
        if _atr_key(row.get("brain")):
            atr_stored += 1
        stop = row.get("stop_pct")
        if not isinstance(stop, (int, float)):
            missing += 1
            continue
        if abs(float(stop) - MIN_STOP) <= 1e-9:
            on_floor += 1
        elif float(stop) > MIN_STOP:
            above += 1
        else:
            below += 1
    opens = on_floor + above + below + missing
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif missing or below:
        status = "INCOMPLETE"
    elif atr_stored == 0:
        status = "ATR_NOT_STORED"
    else:
        status = "ATR_STORED"
    return {
        "paper_only": True,
        "floor_changed": False,
        "atr_verified": False,
        "edge_claimed": False,
        "min_stop": MIN_STOP,
        "open_rows": opens,
        "missing_rows": missing,
        "on_floor": on_floor,
        "above_floor": above,
        "below_floor": below,
        "atr_stored_rows": atr_stored,
        "status": status,
    }


def write_atr_stop(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.atr_stop.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_atr_stop(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "atr_stop.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_skip_address(root: Path) -> dict[str, Any]:
    """Count address-shaped sources on skips, holds, and refusals. Do not copy one."""
    from collections import Counter

    addr_source = addr_pair = unlabeled = 0
    kinds: Counter[str] = Counter()
    for row in _log_rows(root):
        if row.get("event") not in ("SKIP", "HOLD", "NO_TRADE"):
            continue
        source = str(row.get("source") or "")
        if "0x" in source.lower() or "pool32:" in source.lower():
            addr_source += 1
            kind = source.split(":", 1)[0]
            if kind and "0x" not in kind.lower() and "pool32" not in kind.lower():
                kinds[kind] += 1
            else:
                unlabeled += 1
        witness = row.get("witness") if isinstance(row.get("witness"), dict) else {}
        pair = witness.get("pair")
        if isinstance(pair, str) and ("0x" in pair.lower() or "pool32:" in pair.lower()):
            addr_pair += 1
    if addr_source or addr_pair:
        status = "ADDRESS_ON_LOG"
    else:
        status = "NO_ADDRESS"
    return {
        "paper_only": True,
        "log_rewritten": False,
        "edge_claimed": False,
        "address_sources": addr_source,
        "address_pairs": addr_pair,
        "unlabeled_address_rows": unlabeled,
        "kinds": [{"kind": name, "rows": kinds[name]} for name in sorted(kinds)],
        "status": status,
    }


def write_skip_address(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.skip_address.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_skip_address(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "skip_address.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(snap, ensure_ascii=False, indent=1)
    if "0x" in text.lower():
        raise RuntimeError("skip address receipt copied an address")
    path.write_text(text, encoding="utf-8")
    return snap


def measure_witness_skip(root: Path) -> dict[str, Any]:
    """A witness skip blocks an entry. It is not an exit and it is not a security pass."""
    from collections import Counter

    counts: Counter[str] = Counter()
    for row in _log_rows(root):
        if row.get("event") != "SKIP":
            continue
        reason = str(row.get("reason") or "")
        if reason.startswith("WITNESS_"):
            counts[reason] += 1
    reasons = [{"reason": name, "rows": counts[name]} for name in sorted(counts)]
    if not reasons:
        status = "NO_WITNESS_SKIPS"
    else:
        status = "ENTRY_BLOCK_NOT_AN_EXIT"
    return {
        "paper_only": True,
        "exit_relabeled": False,
        "treated_as_security_pass": False,
        "edge_claimed": False,
        "witness_rows": sum(counts.values()),
        "reasons": reasons,
        "status": status,
    }


def write_witness_skip(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.witness_skip.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_witness_skip(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "witness_skip.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_promotion_gate(root: Path) -> dict[str, Any]:
    """The close-count gate. Thirty closes and a stored word are not a promotion."""
    from architecture.markets.paper_trader import performance

    closes = [row for row in _log_rows(root) if row.get("event") == "CLOSE"]
    perf = performance(closes) if closes else {}
    gate = str(perf.get("promotion_gate") or "")
    ci = perf.get("expectancy_ci95")
    ci_lower_positive = (
        isinstance(ci, list) and len(ci) == 2 and isinstance(ci[0], (int, float)) and float(ci[0]) > 0
    )
    stored = _load_trader_promotion_gate(root)
    stored_evaluate = stored == "EVALUATE"
    source_not_eligible = "NOT_ELIGIBLE" in gate
    if not closes:
        status = "NO_CLOSED_ROWS"
    elif stored_evaluate and source_not_eligible:
        status = "STORED_WORD_IS_NOT_A_PROMOTION"
    elif source_not_eligible:
        status = "SOURCE_NOT_ELIGIBLE"
    else:
        status = "REVIEW"
    return {
        "paper_only": True,
        "promoted": False,
        "edge_claimed": False,
        "dsr_supplied": False,
        "close_rows": len(closes),
        "source_not_eligible": source_not_eligible,
        "ci_lower_positive": ci_lower_positive,
        "stored_evaluate": stored_evaluate,
        "status": status,
    }


def write_promotion_gate(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.promotion_gate.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_promotion_gate(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "promotion_gate.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_kelly_count(root: Path) -> dict[str, Any]:
    """The stored OFF label. The n<30 sentence is not the live close count."""
    stale = other = numeric = missing = 0
    closes = 0
    for row in _log_rows(root):
        if row.get("event") == "CLOSE":
            closes += 1
            continue
        if row.get("event") != "OPEN":
            continue
        kelly = row.get("kelly")
        if isinstance(kelly, (int, float)):
            numeric += 1
        elif not isinstance(kelly, str) or not kelly:
            missing += 1
        elif kelly.startswith("OFF") and "n<30" in kelly:
            stale += 1
        else:
            other += 1
    opens = stale + other + numeric + missing
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif numeric:
        status = "NUMERIC_KELLY_PRESENT"
    elif missing == opens:
        status = "KELLY_FIELD_ABSENT"
    elif stale == opens and closes >= 30:
        status = "OFF_LABEL_COUNT_IS_STALE"
    elif stale == opens:
        status = "UNIFORM_OFF_LABEL"
    else:
        status = "MIXED"
    return {
        "paper_only": True,
        "kelly_switched_on": False,
        "label_rewritten": False,
        "edge_claimed": False,
        "open_rows": opens,
        "close_rows": closes,
        "stale_off_rows": stale,
        "other_rows": other,
        "numeric_rows": numeric,
        "missing_rows": missing,
        "status": status,
    }


def write_kelly_count(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.kelly_count.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_kelly_count(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "kelly_count.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_ruin_basis(root: Path) -> dict[str, Any]:
    """Five or more closes make the ruin code resample this book. That is not a forecast."""
    closes = sum(1 for row in _log_rows(root) if row.get("event") == "CLOSE")
    empirical_basis = closes >= 5
    if closes == 0:
        status = "NO_CLOSED_ROWS"
    elif empirical_basis:
        status = "RESAMPLE_NOT_A_FORECAST"
    else:
        status = "STRESS_PRIOR_NOT_THE_BOOK"
    return {
        "paper_only": True,
        "forecast_claimed": False,
        "probability_published": False,
        "edge_claimed": False,
        "close_rows": closes,
        "empirical_basis": empirical_basis,
        "status": status,
    }


def write_ruin_basis(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.ruin_basis.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_ruin_basis(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "ruin_basis.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _weights_doc(root: Path) -> dict[str, Any] | None:
    path = Path(root) / "reports" / "grok" / "PAPER" / "signal_weights.json"
    if not path.is_file():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return doc if isinstance(doc, dict) else {}


def _sign(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def measure_weight_band(root: Path) -> dict[str, Any]:
    """A hit-rate update inside the recorded band is not an edge and not a promotion."""
    from architecture.markets.signal_brain import DEFAULT_WEIGHTS

    doc = _weights_doc(root)
    if doc is None:
        return {
            "paper_only": True,
            "file_rewritten": False,
            "edge_claimed": False,
            "promoted": False,
            "rule_changed": False,
            "file_present": False,
            "version": None,
            "history_rows": None,
            "moved_rows": 0,
            "outside_rows": 0,
            "absent_rows": 0,
            "n_ge_10": 0,
            "shadow_nonzero": 0,
            "moved_names": [],
            "status": "NO_WEIGHT_FILE",
        }
    weights = doc.get("weights") if isinstance(doc.get("weights"), dict) else None
    stats = doc.get("stats") if isinstance(doc.get("stats"), dict) else {}
    history = doc.get("history") if isinstance(doc.get("history"), list) else None
    version = doc.get("version")
    version = version if isinstance(version, int) and not isinstance(version, bool) else None
    if weights is None:
        return {
            "paper_only": True,
            "file_rewritten": False,
            "edge_claimed": False,
            "promoted": False,
            "rule_changed": False,
            "file_present": True,
            "version": version,
            "history_rows": None if history is None else len(history),
            "moved_rows": 0,
            "outside_rows": 0,
            "absent_rows": 0,
            "n_ge_10": 0,
            "shadow_nonzero": 0,
            "moved_names": [],
            "status": "INCOMPLETE",
        }
    moved: list[str] = []
    outside = absent = n_ge = shadow_nonzero = 0
    for name, base in DEFAULT_WEIGHTS.items():
        current = weights.get(name)
        st = stats.get(name) if isinstance(stats.get(name), dict) else {}
        n = st.get("n")
        if isinstance(n, int) and not isinstance(n, bool) and n >= 10:
            n_ge += 1
        if isinstance(current, bool) or not isinstance(current, (int, float)):
            absent += 1
            continue
        lo = float(base) * 0.5
        hi = float(base) * 1.5
        if not (lo - 1e-9 <= float(current) <= hi + 1e-9):
            outside += 1
        if abs(float(current) - float(base)) > 1e-9:
            moved.append(name)
        if float(base) == 0.0 and abs(float(current)) > 1e-12:
            shadow_nonzero += 1
    return {
        "paper_only": True,
        "file_rewritten": False,
        "edge_claimed": False,
        "promoted": False,
        "rule_changed": False,
        "file_present": True,
        "version": version,
        "history_rows": None if history is None else len(history),
        "moved_rows": len(moved),
        "outside_rows": outside,
        "absent_rows": absent,
        "n_ge_10": n_ge,
        "shadow_nonzero": shadow_nonzero,
        "moved_names": sorted(moved),
        "status": "OUTSIDE_BAND" if outside or shadow_nonzero else "INSIDE_BAND",
    }


def write_weight_band(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.weight_band.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_weight_band(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "weight_band.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_book_descriptive(root: Path) -> dict[str, Any]:
    """Sharpe, Sortino, and expectancy on this book are not a deflated Sharpe."""
    from architecture.markets.paper_trader import performance

    closes = [row for row in _log_rows(root) if row.get("event") == "CLOSE"]
    if not closes:
        return {
            "paper_only": True,
            "dsr_claimed": False,
            "edge_claimed": False,
            "close_rows": 0,
            "sharpe_sign": None,
            "sortino_sign": None,
            "expectancy_sign": None,
            "source_not_eligible": False,
            "status": "NO_CLOSED_ROWS",
        }
    perf = performance(closes)
    gate = perf.get("promotion_gate")
    signs = {
        "sharpe_sign": _sign(perf.get("sharpe_per_trade")),
        "sortino_sign": _sign(perf.get("sortino_per_trade")),
        "expectancy_sign": _sign(perf.get("expectancy_usd")),
    }
    eligible = isinstance(gate, str) and gate.startswith("NOT_ELIGIBLE")
    complete = eligible and all(value is not None for value in signs.values())
    return {
        "paper_only": True,
        "dsr_claimed": False,
        "edge_claimed": False,
        "close_rows": len(closes),
        "source_not_eligible": eligible,
        **signs,
        "status": "DESCRIPTIVE_NOT_DSR" if complete else "INCOMPLETE",
    }


def write_book_descriptive(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.book_descriptive.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_book_descriptive(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "book_descriptive.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_weight_history(root: Path) -> dict[str, Any]:
    """A version number with a matching history length is not an edge."""
    doc = _weights_doc(root)
    if doc is None:
        return {
            "paper_only": True,
            "file_rewritten": False,
            "edge_claimed": False,
            "file_present": False,
            "version": None,
            "history_rows": None,
            "matches": False,
            "status": "NO_WEIGHT_FILE",
        }
    version = doc.get("version")
    version = version if isinstance(version, int) and not isinstance(version, bool) else None
    history = doc.get("history")
    rows = len(history) if isinstance(history, list) else None
    matches = version is not None and rows is not None and version >= 1 and rows == version - 1
    return {
        "paper_only": True,
        "file_rewritten": False,
        "edge_claimed": False,
        "file_present": True,
        "version": version,
        "history_rows": rows,
        "matches": matches,
        "status": "VERSION_HAS_A_HISTORY" if matches else "HISTORY_GAP",
    }


def write_weight_history(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.weight_history.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_weight_history(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "weight_history.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _iso_stamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def measure_lesson_stats(root: Path) -> dict[str, Any]:
    """Replay the close lesson. A matching count is not an edge and is not written back."""
    from architecture.markets.signal_brain import DEFAULT_WEIGHTS

    closes = [row for row in _log_rows(root) if row.get("event") == "CLOSE"]
    empty = {
        "paper_only": True,
        "file_rewritten": False,
        "stats_backfilled": False,
        "cutoff_changed": False,
        "edge_claimed": False,
        "close_rows": 0,
        "missing_brain": 0,
        "below_cutoff": 0,
        "counted_rows": 0,
        "matched_signals": 0,
        "file_ahead": 0,
        "file_behind": 0,
        "no_stat_names": [],
        "status": "NO_CLOSED_ROWS",
    }
    if not closes:
        return empty
    replay: dict[str, list[int]] = {}
    missing = below = counted = 0
    for row in closes:
        brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else None
        contribs = brain.get("contributions") if brain else None
        pnl = row.get("realized_pnl_usd")
        side = row.get("side")
        if (not isinstance(contribs, list) or isinstance(pnl, bool)
                or not isinstance(pnl, (int, float)) or side not in ("LONG", "SHORT")):
            missing += 1
            continue
        win = float(pnl) > 0
        direction = 1 if side == "LONG" else -1
        for item in contribs:
            if not isinstance(item, dict):
                continue
            score = item.get("score")
            name = item.get("signal")
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not isinstance(name, str):
                continue
            if abs(float(score)) < 0.1:
                below += 1
                continue
            counted += 1
            cell = replay.setdefault(name, [0, 0])
            cell[0] += 1
            cell[1] += int((float(score) * direction > 0) == win)
    doc = _weights_doc(root)
    stats = doc.get("stats") if isinstance(doc, dict) and isinstance(doc.get("stats"), dict) else {}
    matched = ahead = behind = 0
    no_stat: list[str] = []
    if isinstance(doc, dict):
        for name in DEFAULT_WEIGHTS:
            cell = replay.get(name)
            st = stats.get(name) if isinstance(stats.get(name), dict) else None
            if cell is None and st is None:
                no_stat.append(name)
                continue
            file_n = st.get("n") if st else None
            file_hits = st.get("hits") if st else None
            replay_n, replay_hits = cell if cell else (0, 0)
            if file_n == replay_n and file_hits == replay_hits:
                matched += 1
            elif isinstance(file_n, int) and not isinstance(file_n, bool) and file_n > replay_n:
                ahead += 1
            else:
                behind += 1
        for name in stats:
            if name not in DEFAULT_WEIGHTS:
                behind += 1
    if doc is None:
        status = "NO_WEIGHT_FILE"
    elif missing:
        status = "INCOMPLETE"
    elif ahead:
        status = "FILE_AHEAD_OF_THE_LOG"
    elif behind:
        status = "FILE_BEHIND_THE_LOG"
    else:
        status = "STATS_MATCH_THE_LOG"
    return {
        "paper_only": True,
        "file_rewritten": False,
        "stats_backfilled": False,
        "cutoff_changed": False,
        "edge_claimed": False,
        "close_rows": len(closes),
        "missing_brain": missing,
        "below_cutoff": below,
        "counted_rows": counted,
        "matched_signals": matched,
        "file_ahead": ahead,
        "file_behind": behind,
        "no_stat_names": sorted(no_stat),
        "status": status,
    }


def write_lesson_stats(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.lesson_stats.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_lesson_stats(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "lesson_stats.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_reentry_gap(root: Path) -> dict[str, Any]:
    """A later open of a closed symbol is not a cooldown and not an edge."""
    last_close: dict[str, datetime] = {}
    gaps: list[float] = []
    symbols: set[str] = set()
    missing_stamp = 0
    for row in _log_rows(root):
        sym = row.get("symbol")
        event = row.get("event")
        if not isinstance(sym, str) or event not in ("OPEN", "CLOSE"):
            continue
        if event == "CLOSE":
            stamp = _iso_stamp(row.get("closed_at"))
            if stamp is None:
                missing_stamp += 1
                continue
            last_close[sym] = stamp
            continue
        prev = last_close.get(sym)
        if prev is None:
            continue
        stamp = _iso_stamp(row.get("ts") or row.get("opened_at"))
        if stamp is None or stamp <= prev:
            missing_stamp += 1
            continue
        gaps.append((stamp - prev).total_seconds() / 3600)
        symbols.add(sym)
    if missing_stamp:
        status = "INCOMPLETE"
    elif gaps:
        status = "REENTRY_NOT_BLOCKED"
    else:
        status = "NO_REENTRY"
    return {
        "paper_only": True,
        "cooldown_added": False,
        "edge_claimed": False,
        "reentry_rows": len(gaps),
        "distinct_symbols": len(symbols),
        "min_gap_hours": None if not gaps else round(min(gaps), 2),
        "missing_stamp": missing_stamp,
        "status": status,
    }


def write_reentry_gap(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.reentry_gap.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_reentry_gap(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "reentry_gap.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_entry_version(root: Path) -> dict[str, Any]:
    """An open keeps the weight version it entered with. That version is not the live file."""
    versions: dict[str, int] = {}
    last: dict[str, tuple[str, int | None]] = {}
    open_rows = missing = at_live = 0
    for row in _log_rows(root):
        sym = row.get("symbol")
        event = row.get("event")
        if not isinstance(sym, str) or event not in ("OPEN", "CLOSE"):
            continue
        if event == "CLOSE":
            last[sym] = ("CLOSE", None)
            continue
        brain = row.get("brain") if isinstance(row.get("brain"), dict) else None
        version = brain.get("weights_version") if brain else None
        version = version if isinstance(version, int) and not isinstance(version, bool) else None
        open_rows += 1
        if version is None:
            missing += 1
        else:
            key = str(version)
            versions[key] = versions.get(key, 0) + 1
        last[sym] = ("OPEN", version)
    doc = _weights_doc(root)
    live = doc.get("version") if isinstance(doc, dict) else None
    live = live if isinstance(live, int) and not isinstance(live, bool) else None
    if live is not None:
        at_live = versions.get(str(live), 0)
    still = [
        {"symbol": sym, "weights_version": version}
        for sym, (event, version) in sorted(last.items()) if event == "OPEN"
    ]
    if open_rows == 0:
        status = "NO_OPEN_ROWS"
    elif missing:
        status = "VERSION_MISSING"
    else:
        status = "ENTRY_VERSION_HELD"
    return {
        "paper_only": True,
        "version_rewritten": False,
        "edge_claimed": False,
        "open_rows": open_rows,
        "missing_version": missing,
        "distinct_versions": len(versions),
        "live_file_version": live,
        "opens_at_live_version": at_live,
        "version_counts": versions,
        "still_open": still,
        "status": status,
    }


def write_entry_version(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.entry_version.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_entry_version(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "entry_version.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _is_num(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def measure_weight_path(root: Path) -> dict[str, Any]:
    """Compare a logged entry weight with the prior history snapshot. A gap is not an edge."""
    from architecture.markets.signal_brain import DEFAULT_WEIGHTS

    doc = _weights_doc(root)
    by_version: dict[int, dict[str, Any]] = {}
    if isinstance(doc, dict) and isinstance(doc.get("history"), list):
        for item in doc["history"]:
            if not isinstance(item, dict) or not isinstance(item.get("weights"), dict):
                continue
            version = item.get("version")
            if _is_num(version) and float(version).is_integer():
                by_version[int(version)] = item["weights"]
    matched = mismatch = absent = no_history = unversioned = opens = 0
    absent_names: set[str] = set()
    mismatch_names: set[str] = set()
    mismatch_versions: set[int] = set()
    for row in _log_rows(root):
        if row.get("event") != "OPEN":
            continue
        opens += 1
        brain = row.get("brain") if isinstance(row.get("brain"), dict) else {}
        version = brain.get("weights_version")
        if not _is_num(version) or not float(version).is_integer():
            unversioned += 1
            continue
        version = int(version)
        snapshot: dict[str, Any] | None
        if version == 1:
            snapshot = dict(DEFAULT_WEIGHTS)
        else:
            snapshot = by_version.get(version - 1)
        if snapshot is None:
            no_history += 1
            continue
        contribs = brain.get("contributions") if isinstance(brain.get("contributions"), list) else []
        for item in contribs:
            if not isinstance(item, dict) or not isinstance(item.get("signal"), str) or not _is_num(item.get("weight")):
                continue
            expected = snapshot.get(item["signal"])
            if not _is_num(expected):
                absent += 1
                absent_names.add(item["signal"])
                continue
            if abs(float(item["weight"]) - float(expected)) <= 1e-9:
                matched += 1
            else:
                mismatch += 1
                mismatch_names.add(item["signal"])
                mismatch_versions.add(version)
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif doc is None and any(True for _ in by_version) is False and unversioned == opens:
        status = "VERSION_MISSING"
    elif no_history:
        status = "HISTORY_GAP"
    elif mismatch or absent:
        status = "PATH_DIFFERS"
    elif matched:
        status = "PATH_MATCHES"
    else:
        status = "VERSION_MISSING"
    return {
        "paper_only": True,
        "history_rewritten": False,
        "absence_filled": False,
        "edge_claimed": False,
        "open_rows": opens,
        "matched_weights": matched,
        "numeric_mismatch": mismatch,
        "absent_keys": absent,
        "no_history": no_history,
        "absent_names": sorted(absent_names),
        "mismatch_names": sorted(mismatch_names),
        "mismatch_versions": sorted(mismatch_versions),
        "status": status,
    }


def write_weight_path(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.weight_path.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_weight_path(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "weight_path.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_paper_route(root: Path) -> dict[str, Any]:
    """ACCEPTED_PAPER is the paper router. It is not a broker fill."""
    accepted = missing = other = opens = 0
    for row in _log_rows(root):
        if row.get("event") != "OPEN":
            continue
        opens += 1
        route = row.get("oms")
        if route is None:
            missing += 1
        elif route == "ACCEPTED_PAPER":
            accepted += 1
        else:
            other += 1
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif other:
        status = "OTHER_ROUTE"
    elif accepted:
        status = "PAPER_ROUTE_NOT_A_FILL"
    else:
        status = "OMS_FIELD_ABSENT"
    return {
        "paper_only": True,
        "broker_claimed": False,
        "route_changed": False,
        "edge_claimed": False,
        "open_rows": opens,
        "accepted_paper": accepted,
        "missing_rows": missing,
        "other_rows": other,
        "status": status,
    }


def write_paper_route(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.paper_route.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_paper_route(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "paper_route.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_posterior_inputs(root: Path) -> dict[str, Any]:
    """A stored posterior without the bull and bear inputs is not a probability."""
    stored = missing = posterior = bull = bear = opens = 0
    for row in _log_rows(root):
        if row.get("event") != "OPEN":
            continue
        opens += 1
        brain = row.get("brain") if isinstance(row.get("brain"), dict) else {}
        debate = brain.get("council_debate")
        if not isinstance(debate, dict):
            missing += 1
            continue
        stored += 1
        if "posterior_prob_up" in debate:
            posterior += 1
        if "bull_prob" in debate:
            bull += 1
        if "bear_prob" in debate:
            bear += 1
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif stored == 0:
        status = "NO_STORED_DEBATE"
    elif posterior and bull == 0 and bear == 0:
        status = "POSTERIOR_WITHOUT_INPUTS"
    elif bull or bear:
        status = "INPUTS_STORED"
    else:
        status = "NO_POSTERIOR_KEY"
    return {
        "paper_only": True,
        "value_copied": False,
        "treated_as_probability": False,
        "edge_claimed": False,
        "open_rows": opens,
        "stored_rows": stored,
        "missing_rows": missing,
        "posterior_rows": posterior,
        "bull_rows": bull,
        "bear_rows": bear,
        "status": status,
    }


def write_posterior_inputs(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.posterior_inputs.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_posterior_inputs(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "posterior_inputs.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def _blend_of_composite(comp: float, bull_n: int, bear_n: int) -> dict[str, Any] | None:
    """The live debate function. A stored number is compared with it and not copied."""
    if bull_n < 1 or bear_n < 1:
        return None
    from architecture.markets.council_gate import soroush_blind_debate_and_bl

    bull = max(0.05, min(0.95, 0.5 + 0.4 * comp))
    bear = max(0.05, min(0.95, 0.5 - 0.4 * comp))
    fresh = soroush_blind_debate_and_bl(
        symbol="RECOMPUTE",
        bull_prob=bull,
        bear_prob=bear,
        bull_evidence_refs=[f"r{i}" for i in range(bull_n)],
        bear_evidence_refs=[f"r{i}" for i in range(bear_n)],
        devils_advocate_dissent="recompute",
    )
    posterior = fresh.get("posterior_prob_up")
    odds = fresh.get("log_odds")
    if not _is_num(posterior) or not _is_num(odds):
        return None
    return {"posterior": float(posterior), "log_odds": float(odds)}


def measure_posterior_blend(root: Path) -> dict[str, Any]:
    """A stored posterior that matches the live blend is still a rescaling, not a probability."""
    opens = stored = missing = blend_match = blend_differ = odds_match = odds_differ = 0
    for row in _log_rows(root):
        if row.get("event") != "OPEN":
            continue
        opens += 1
        brain = row.get("brain") if isinstance(row.get("brain"), dict) else {}
        debate = brain.get("council_debate")
        if not isinstance(debate, dict):
            missing += 1
            continue
        stored += 1
        comp = brain.get("composite")
        bull_n = debate.get("bull_refs_count")
        bear_n = debate.get("bear_refs_count")
        posterior = debate.get("posterior_prob_up")
        odds = debate.get("log_odds")
        if (not _is_num(comp) or not isinstance(bull_n, int) or isinstance(bull_n, bool)
                or not isinstance(bear_n, int) or isinstance(bear_n, bool)
                or not _is_num(posterior) or not _is_num(odds)):
            blend_differ += 1
            odds_differ += 1
            continue
        expected = _blend_of_composite(float(comp), bull_n, bear_n)
        if expected is None:
            blend_differ += 1
            odds_differ += 1
            continue
        if abs(float(posterior) - expected["posterior"]) <= 1e-4:
            blend_match += 1
        else:
            blend_differ += 1
        if abs(float(odds) - expected["log_odds"]) <= 1e-4:
            odds_match += 1
        else:
            odds_differ += 1
    if opens == 0:
        status = "NO_OPEN_ROWS"
    elif stored == 0:
        status = "NO_STORED_DEBATE"
    elif blend_differ or odds_differ:
        status = "NOT_THE_BLEND"
    elif blend_match == stored and odds_match == stored:
        status = "BLEND_OF_A_RESCALE"
    else:
        status = "INCOMPLETE"
    return {
        "paper_only": True,
        "value_copied": False,
        "treated_as_probability": False,
        "formula_changed": False,
        "edge_claimed": False,
        "open_rows": opens,
        "stored_rows": stored,
        "missing_rows": missing,
        "blend_match": blend_match,
        "blend_differ": blend_differ,
        "odds_match": odds_match,
        "odds_differ": odds_differ,
        "status": status,
    }


def write_posterior_blend(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.posterior_blend.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_posterior_blend(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "posterior_blend.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_partial_field(root: Path) -> dict[str, Any]:
    """A missing partial flag is not a partial close and is not backfilled."""
    closes = absent = true_rows = false_rows = other = 0
    for row in _log_rows(root):
        if row.get("event") != "CLOSE":
            continue
        closes += 1
        if "partial" not in row:
            absent += 1
        elif row.get("partial") is True:
            true_rows += 1
        elif row.get("partial") is False:
            false_rows += 1
        else:
            other += 1
    if closes == 0:
        status = "NO_CLOSED_ROWS"
    elif absent == closes:
        status = "PARTIAL_FIELD_ABSENT"
    else:
        status = "PARTIAL_FIELD_PRESENT"
    return {
        "paper_only": True,
        "backfilled": False,
        "partial_inferred": False,
        "edge_claimed": False,
        "close_rows": closes,
        "absent_rows": absent,
        "true_rows": true_rows,
        "false_rows": false_rows,
        "other_rows": other,
        "status": status,
    }


def write_partial_field(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.partial_field.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_partial_field(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "partial_field.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def measure_close_route(root: Path) -> dict[str, Any]:
    """ACCEPTED_PAPER on a close is the paper router. It is not a broker fill."""
    accepted = missing = other = closes = 0
    for row in _log_rows(root):
        if row.get("event") != "CLOSE":
            continue
        closes += 1
        route = row.get("oms")
        if route is None:
            missing += 1
        elif route == "ACCEPTED_PAPER":
            accepted += 1
        else:
            other += 1
    if closes == 0:
        status = "NO_CLOSED_ROWS"
    elif other:
        status = "OTHER_ROUTE"
    elif accepted:
        status = "CLOSE_ROUTE_NOT_A_FILL"
    else:
        status = "OMS_FIELD_ABSENT"
    return {
        "paper_only": True,
        "broker_claimed": False,
        "route_changed": False,
        "edge_claimed": False,
        "close_rows": closes,
        "accepted_paper": accepted,
        "missing_rows": missing,
        "other_rows": other,
        "status": status,
    }


def write_close_route(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.close_route.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_close_route(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "close_route.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap


def write_skip_census(root: Path) -> dict[str, Any]:
    snap = {
        "schema": "ahos.paper.skip_census.v1",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        **measure_skip_census(root),
    }
    path = Path(root) / "reports" / "grok" / "PAPER" / "skip_census.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap
