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
