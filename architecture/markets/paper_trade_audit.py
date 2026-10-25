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
    promotion_gate = _load_trader_promotion_gate(root)
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
        "promotion_gate_fa": (
            "هنوز واجد ارتقا نیست: کمتر از ۳۰ معاملهٔ بسته یا DSR/PBO پاس نشده — لبهٔ سودآوری اثبات‌نشده."
            if promotion_gate and "NOT_ELIGIBLE" in str(promotion_gate)
            else str(promotion_gate or "نامشخص")
        ),
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
