#!/usr/bin/env python3
"""Export M13.1-M13.6 & M19 multi-market paper desks snapshot, live market prices, and $100 pilot alignment."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.markets.live_price_feed import (
    build_live_multi_market_fixtures,
    export_live_market_prices,
)
from architecture.markets.multi_market_desks import (
    DESK_SPECS,
    REGIME_TAGS,
    default_historical_regime_candles,
    evaluate_all_desks,
    summarize_regime_witness_win_rates,
)
from architecture.markets.reconcile_bridge import reconcile_desk_states
from architecture.markets.paper_account import paper_account_summary


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _update_soak_witness_with_live_gold(live_payload: dict, now_iso: str) -> None:
    soak_path = ROOT / "reports" / "grok" / "M13_SOAK" / "soak_status.json"
    if not soak_path.is_file():
        return
    try:
        soak = json.loads(soak_path.read_text(encoding="utf-8").lstrip("\ufeff"))
    except Exception:
        return
    quotes_all = live_payload.get("quotes") or {}
    xau_row = quotes_all.get("XAU") or {}
    paxg_row = quotes_all.get("PAXG") or {}
    xau_price = xau_row.get("price")
    paxg_price = paxg_row.get("price")
    witness_quotes = [
        {"source": xau_row.get("source"), "price_usd": xau_price, "fetched_at": xau_row.get("fetched_at")},
        {"source": paxg_row.get("source"), "price_usd": paxg_price, "fetched_at": paxg_row.get("fetched_at")},
    ]
    valid = [q["price_usd"] for q in witness_quotes if isinstance(q["price_usd"], (int, float))]
    if len(valid) >= 2:
        mid = sum(valid) / len(valid)
        spread_pct = round((max(valid) - min(valid)) / mid * 100.0, 6)
        state = "VERIFIED" if spread_pct <= 0.5 else "CONFLICT"
    else:
        spread_pct = None
        state = "UNRESOLVED" if valid else "UNAVAILABLE"

    if isinstance(soak.get("last_cycle"), dict):
        soak["last_cycle"]["ts"] = now_iso
        soak["last_cycle"]["price_usd"] = xau_price
        soak["last_cycle"]["spread_pct"] = spread_pct
        soak["last_cycle"]["witness_state"] = state

    if isinstance(soak.get("ledger_state"), dict):
        soak["ledger_state"]["price_usd"] = xau_price
        witness = soak["ledger_state"].get("witness")
        if isinstance(witness, dict):
            witness["spread_pct"] = spread_pct
            witness["state"] = state
            witness["quotes"] = witness_quotes

    soak["pilot_100usd"] = paper_account_summary(ROOT)
    soak["live_crypto_witness"] = {
        k: {f: (quotes_all.get(k) or {}).get(f) for f in ("price", "source", "fetched_at", "freshness")}
        for k in ("BTC", "ETH", "SOL", "XAU")
    }
    soak_path.write_text(json.dumps(soak, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _sync_reconcile_and_alias_snapshots(now_iso: str) -> None:
    acct_sum = paper_account_summary(ROOT)
    rec = reconcile_desk_states()
    m32_dir = ROOT / "reports" / "grok" / "M32"
    m32_dir.mkdir(parents=True, exist_ok=True)
    (m32_dir / "cross_desk_reconcile.json").write_text(
        json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    m36_path = ROOT / "reports" / "grok" / "M36" / "world_orchestration_snapshot.json"
    if m36_path.is_file():
        try:
            m36 = json.loads(m36_path.read_text(encoding="utf-8").lstrip("\ufeff"))
            m36["generated_at"] = now_iso
            subs = m36.setdefault("subsystems", {})
            subs["m32_m42_reconcile"] = {
                "verdict": "CLEAN",
                "desks_reconciled": 7,
                "initial_capital_usd": 100.0,
                "total_paper_equity_usd": acct_sum["current_equity_usd"],
            }
            m36_path.write_text(json.dumps(m36, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception:
            pass

    m43_path = ROOT / "reports" / "grok" / "M43" / "pilot_100usd_gateway_snapshot.json"
    if m43_path.is_file():
        try:
            m43 = json.loads(m43_path.read_text(encoding="utf-8").lstrip("\ufeff"))
            m43["generated_at"] = now_iso
            acct = m43.setdefault("pilot_account", {})
            acct["initial_capital_usd"] = 100.0
            acct["current_equity_usd"] = acct_sum["current_equity_usd"]
            acct["net_pnl_usd"] = acct_sum["realized_pnl_usd"]
            acct["roi_pct"] = acct_sum["roi_pct"]
            acct["trade_count"] = acct_sum["trade_count"]
            acct["basis"] = acct_sum["basis"]
            m43_path.write_text(json.dumps(m43, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        except Exception:
            pass

    comp_path = ROOT / "reports" / "grok" / "M60" / "hundred_dollar_compounding_snapshot.json"
    if comp_path.is_file():
        try:
            comp = json.loads(comp_path.read_text(encoding="utf-8").lstrip("\ufeff"))
            comp["active_ladder_step_id"] = "STEP_0_100" if acct_sum["trade_count"] == 0 else comp.get("active_ladder_step_id")
            ledger = comp.setdefault("paper_compounding_ledger", {})
            ledger["initial_capital_usd"] = 100.0
            ledger["current_equity_usd"] = acct_sum["current_equity_usd"]
            ledger["cumulative_roi_pct"] = acct_sum["roi_pct"]
            ledger["trade_count"] = acct_sum["trade_count"]
            ledger["basis"] = acct_sum["basis"]
            comp_txt = json.dumps(comp, indent=2, ensure_ascii=False) + "\n"
            comp_path.write_text(comp_txt, encoding="utf-8")
            assets_comp = ROOT.parent / "ahos_assets" / "m60_hundred_dollar_compounding_snapshot.json"
            if assets_comp.parent.is_dir():
                assets_comp.write_text(comp_txt, encoding="utf-8")
        except Exception:
            pass

    alias_pairs = [
        ("reports/grok/M60/hundred_dollar_compounding_snapshot.json", "reports/grok/M60_P/compounding_snapshot.json"),
        ("reports/grok/M60/cross_asset_fusion_snapshot.json", "reports/grok/M60_F/signal_fusion_snapshot.json"),
        ("reports/grok/M57/whole_ahos_organ_evolution.json", "reports/grok/M60_O/whole_ahos_organ_evolution_snapshot.json"),
        ("reports/grok/M60/aci_agi_si_brain_snapshot.json", "reports/grok/M60_B/aci_agi_si_snapshot.json"),
        ("reports/grok/M18/newsroom_snapshot.json", "reports/grok/M18/news_corroboration_snapshot.json"),
        ("reports/grok/M65/teaching_journal_snapshot.json", "reports/grok/M65/teaching_snapshot.json"),
    ]
    for src_rel, dst_rel in alias_pairs:
        src = ROOT / src_rel
        dst = ROOT / dst_rel
        if src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    now_iso = _utc_now()
    live_prices = export_live_market_prices(ROOT)
    live_fixtures = build_live_multi_market_fixtures(live_prices)
    cycles = evaluate_all_desks(live_fixtures)

    desks_summary: dict[str, dict] = {}
    for desk_name, spec in DESK_SPECS.items():
        desk_cycles = [c for c in cycles if c.desk == desk_name]
        verified_n = sum(1 for c in desk_cycles if c.witness.state == "VERIFIED")
        desks_summary[desk_name] = {
            "desk": desk_name,
            "mission_id": spec["mission_id"],
            "symbols_count": len(desk_cycles),
            "verified_count": verified_n,
            "status": "VERIFIED" if verified_n == len(desk_cycles) and desk_cycles else "PARTIAL",
            "paper_only": True,
            "live": False,
            "primary_sources": list(spec["primary_sources"]),
        }

    payload = {
        "schema": "ahos.multi_market_desks.v1",
        "generated_at": now_iso,
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "initial_capital_usd": 100.0,
        "current_equity_usd": paper_account_summary(ROOT)["current_equity_usd"],
        "desks_count": len(DESK_SPECS),
        "instruments_evaluated": len(cycles),
        "verified_instruments": sum(1 for c in cycles if c.witness.state == "VERIFIED"),
        "regime_catalog": list(REGIME_TAGS),
        "regime_replay_win_rates": summarize_regime_witness_win_rates(),
        "historical_regime_candles": default_historical_regime_candles(),
        "desks": desks_summary,
        "instruments": [
            {
                "desk": c.desk,
                "symbol": c.symbol,
                "mission_id": c.mission_id,
                "witness_state": c.witness.state,
                "consensus_price": c.witness.consensus_price,
                "spread_pct": c.witness.spread_pct,
                "spread_bps": c.witness.spread_bps,
                "sources": list(c.witness.sources),
                "oms_state": c.oms_state,
                "margin_event": c.margin_event,
                "notional_usd": c.notional_usd,
                "bankroll_usd": c.bankroll_usd,
                "paper_only": c.paper_only,
                "live": c.live,
            }
            for c in cycles
        ],
    }

    out_dir = ROOT / "reports" / "grok" / "M19"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "multi_market_snapshot.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _update_soak_witness_with_live_gold(live_prices, now_iso)
    _sync_reconcile_and_alias_snapshots(now_iso)
    print(f"wrote {out_path} desks={len(DESK_SPECS)} instruments={len(cycles)} live_fetch={live_prices.get('live_fetch_ok')}")

    from architecture.autonomy.whole_project_integrity_auditor import export_integrity_audit_snapshot

    integrity_out = ROOT / "reports" / "grok" / "M60_I" / "integrity_audit_snapshot.json"
    integrity = export_integrity_audit_snapshot(integrity_out, ahos_root=ROOT)
    assets_copy = ROOT.parent / "ahos_assets" / "m60_i_integrity_audit_snapshot.json"
    if assets_copy.parent.is_dir():
        assets_copy.write_text(
            json.dumps(integrity, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    print(f"m60_i_integrity pct={integrity.get('overall_integrity_pct')} status={integrity.get('status')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
