#!/usr/bin/env python3
"""Export EDGE_REPORT.md + edge_report.json from live closed paper trades (PAPER_ONLY)."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.learning.walk_forward import deflated_sharpe, sharpe
from architecture.markets.paper_trade_audit import (
    export_paper_trade_audit_snapshot,
    measure_exit_reason_census,
    measure_fee_identity,
    measure_signal_dissent,
    measure_symbol_book,
    _log_rows,
)
from architecture.markets.paper_trader import INITIAL_CAPITAL_USD, performance


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_dsr_context(root: Path) -> tuple[int, list[float]]:
    n_trials = 99
    sharpes: list[float] = []
    m28 = root / "reports" / "grok" / "M28"
    for path in sorted(m28.glob("batch*_research.json")):
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        n_trials = max(n_trials, int(doc.get("n_trials_counted_in_dsr") or n_trials))
        for cand in doc.get("candidates") or []:
            if isinstance(cand, dict) and cand.get("oos_sharpe") is not None:
                sharpes.append(float(cand["oos_sharpe"]))
    return n_trials, sharpes


def _dominant_signal_pnl(closes: list[dict]) -> list[dict]:
    by_signal: dict[str, dict] = defaultdict(lambda: {"closes": 0, "pnl_usd": 0.0, "wins": 0})
    missing = 0
    for row in closes:
        pnl = float(row.get("realized_pnl_usd") or 0)
        brain = row.get("entry_brain") if isinstance(row.get("entry_brain"), dict) else {}
        contribs = [c for c in (brain.get("contributions") or []) if isinstance(c, dict)]
        if not contribs:
            missing += 1
            name = "MISSING"
        else:
            best = max(contribs, key=lambda c: abs(float(c.get("weight") or 0) * float(c.get("score") or 0)))
            name = str(best.get("signal") or "MISSING")
        cell = by_signal[name]
        cell["closes"] += 1
        cell["pnl_usd"] += pnl
        if pnl > 0:
            cell["wins"] += 1
    rows = []
    for name in sorted(by_signal):
        cell = by_signal[name]
        n = cell["closes"]
        rows.append(
            {
                "signal": name,
                "closes": n,
                "realized_pnl_usd": round(cell["pnl_usd"], 4),
                "win_rate": round(cell["wins"] / n, 3) if n else None,
            }
        )
    return rows, missing


def build_edge_report(root: Path) -> dict:
    closes = [r for r in _log_rows(root) if r.get("event") == "CLOSE"]
    perf = performance(closes)
    symbol_book = measure_symbol_book(root)
    fees = measure_fee_identity(root)
    dissent = measure_signal_dissent(root)
    exits = measure_exit_reason_census(root)
    sig_pnl, sig_missing = _dominant_signal_pnl(closes)

    returns = [float(r.get("realized_pnl_usd") or 0) / INITIAL_CAPITAL_USD for r in closes]
    n_trials, trial_sharpes = _load_dsr_context(root)
    dsr = deflated_sharpe(returns, n_trials, trial_sharpes) if len(returns) >= 10 else None
    sr = round(sharpe(returns), 4) if len(returns) >= 2 else None

    ci = perf.get("expectancy_ci95") or [None, None]
    ci_lower = ci[0] if isinstance(ci, list) and ci else None
    pbo_live: float | None = None
    promotion = {
        "n_closed": len(closes),
        "expectancy_ci95_lower": ci_lower,
        "dsr": dsr,
        "dsr_threshold": 0.95,
        "pbo_live_book": pbo_live,
        "pbo_threshold": 0.5,
        "pbo_note": "CSCV PBO needs multiple pre-registered trial paths; the live $100 book is one policy.",
        "research_pbo_batch8_admitted_only": 0.4889,
        "edge_status": "UNPROVEN_EDGE",
        "eligible": bool(
            len(closes) >= 30
            and ci_lower is not None
            and ci_lower > 0
            and dsr is not None
            and dsr > 0.95
            and pbo_live is not None
            and pbo_live < 0.5
        ),
    }

    desks = symbol_book.get("desks") or []
    shrink = [
        d
        for d in desks
        if float(d.get("realized_pnl_usd") or 0) < 0 and int(d.get("closes") or 0) >= 3
    ]
    keep = [d for d in desks if d not in shrink]

    export_paper_trade_audit_snapshot(root)

    return {
        "schema": "ahos.edge_report.v1",
        "generated_at": _utc_now(),
        "paper_only": True,
        "edge_status": "UNPROVEN_EDGE",
        "promotion_gate": promotion,
        "performance": perf,
        "per_trade_sharpe": sr,
        "deflated_sharpe": dsr,
        "n_trials_counted_in_dsr": n_trials,
        "trial_sharpes_used": len(trial_sharpes),
        "fee_drag": {
            "close_fees_usd": fees.get("close_fees_usd"),
            "open_fee_usd": fees.get("open_fee_usd"),
            "net_pnl_usd": fees.get("net_pnl_usd"),
            "implied_gross_usd": fees.get("implied_gross_usd"),
        },
        "desks": desks,
        "desks_recommend_shrink": shrink,
        "desks_recommend_keep": keep,
        "dominant_signal_attribution": sig_pnl,
        "dominant_signal_missing_rows": sig_missing,
        "signal_dissent": dissent,
        "exit_reasons": exits,
        "symbols": symbol_book.get("symbols"),
    }


def _md(report: dict) -> str:
    p = report["promotion_gate"]
    perf = report["performance"]
    fee = report["fee_drag"]
    lines = [
        "# EDGE_REPORT — live paper book (PAPER_ONLY)",
        "",
        f"Generated: `{report['generated_at']}` · Closed trades: **{p['n_closed']}** · Status: **`{report['edge_status']}`**",
        "",
        "## Promotion gate (TS-PG / Master Map)",
        "",
        f"| Check | Value | Pass threshold |",
        f"|-------|-------|----------------|",
        f"| Closed trades | {p['n_closed']} | ≥ 30 |",
        f"| Expectancy CI95 lower (USD) | {p['expectancy_ci95_lower']} | > 0 |",
        f"| Deflated Sharpe (DSR) | {p['dsr']} | > 0.95 |",
        f"| Live-book PBO | {p['pbo_live_book']} | < 0.50 (N/A single book) |",
        f"| Research PBO (batch8 admitted only) | {p['research_pbo_batch8_admitted_only']} | advisory, not live book |",
        f"| **Eligible** | **{p['eligible']}** | all of the above |",
        "",
        "## Performance (closed trades, net of fees in `realized_pnl_usd`)",
        "",
        f"- Hit rate: **{perf.get('hit_rate')}**",
        f"- Expectancy USD: **{perf.get('expectancy_usd')}** (CI95 {perf.get('expectancy_ci95')})",
        f"- Profit factor: **{perf.get('profit_factor')}**",
        f"- Sharpe per trade (descriptive, not DSR): **{report.get('per_trade_sharpe')}**",
        f"- Max drawdown on sequence: **{perf.get('max_drawdown_pct')}%**",
        "",
        "## Fee drag",
        "",
        f"- Close fees USD: **{fee.get('close_fees_usd')}**",
        f"- Open fees USD (all opens): **{fee.get('open_fee_usd')}**",
        f"- Net realized USD: **{fee.get('net_pnl_usd')}**",
        f"- Implied gross (net + close fees): **{fee.get('implied_gross_usd')}**",
        "",
        "## Per-desk PnL (after fees in log)",
        "",
        "| Desk | Closes | Realized USD | Action |",
        "|------|--------|--------------|--------|",
    ]
    for d in report.get("desks") or []:
        action = "SHRINK / shadow-only" if d in (report.get("desks_recommend_shrink") or []) else "keep (monitor)"
        lines.append(
            f"| {d.get('desk')} | {d.get('closes')} | {d.get('realized_pnl_usd')} | {action} |"
        )
    lines.extend(["", "## Dominant-signal attribution (largest |weight×score| at entry)", ""])
    lines.append("| Signal | Closes | Win rate | Realized USD |")
    lines.append("|--------|--------|----------|--------------|")
    for row in report.get("dominant_signal_attribution") or []:
        lines.append(
            f"| {row.get('signal')} | {row.get('closes')} | {row.get('win_rate')} | {row.get('realized_pnl_usd')} |"
        )
    if report.get("dominant_signal_missing_rows"):
        lines.append(f"\nRows without entry_brain contributions: **{report['dominant_signal_missing_rows']}**")
    lines.extend(
        [
            "",
            "## Honesty",
            "",
            f"- DSR uses cumulative **`n_trials_counted_in_dsr`** from strategy-lab batches and OOS Sharpes stored in M28 research JSON — not a fresh search on these {p['n_closed']} closes.",
            "- Do **not** treat positive closed-trade count or descriptive Sharpe as edge.",
            "- Desks marked **SHRINK** lost after fees with ≥3 closes; disable or cap size in paper only after owner review (no live path).",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    report = build_edge_report(ROOT)
    json_path = ROOT / "reports" / "grok" / "PAPER" / "edge_report.json"
    md_path = ROOT / "EDGE_REPORT.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(_md(report), encoding="utf-8")
    print(f"edge_status={report['edge_status']} closes={report['promotion_gate']['n_closed']} dsr={report.get('deflated_sharpe')} eligible={report['promotion_gate']['eligible']}")
    print(f"wrote {md_path}")
    print(f"wrote {json_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
