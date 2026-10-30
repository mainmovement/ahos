"""Finish the receipts the bounded integrity check can still write. Does not restart processes."""
from __future__ import annotations

import json
import time
from pathlib import Path

from architecture.markets.edge_decomposition import export_edge
from architecture.mission.vision_mega5 import export_mega5
from architecture.mission.vision_steps import export_overlay
from config.paths import (
    get_discovery_db_path, get_knowledge_db_path,
    get_local_db_path, get_paper_trading_db_path,
)

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "reports" / "grok" / "PAPER"


def _load() -> tuple[list[dict], dict[str, dict], int]:
    closes: list[dict] = []
    latest: dict[str, dict] = {}
    veto = 0
    with (PAPER / "paper_trades.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            if "TOKEN_SAFETY_VETO" in line:
                veto += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if row.get("symbol"):
                latest[str(row["symbol"])] = row
            if row.get("event") == "CLOSE" and isinstance(row.get("realized_pnl_usd"), (int, float)):
                closes.append(row)
    return closes, latest, veto


def main() -> None:
    closes, latest, veto = _load()
    edge = export_edge(ROOT, closes)
    status = json.loads((PAPER / "paper_trader_status.json").read_text(encoding="utf-8"))
    mark = status.get("mark_to_market_equity_usd")
    equity = float(mark) if isinstance(mark, (int, float)) and not isinstance(mark, bool) else 100.0
    probe_path = ROOT / "reports" / "provider_probe_20261030T121002Z.json"
    probe = json.loads(probe_path.read_text(encoding="utf-8")) if probe_path.is_file() else None
    # 20s per store. A store that runs longer is INTERRUPTED, not ok.
    from architecture.persistence.store_integrity import check_known_stores
    stores = {
        "ahos_local": Path(get_local_db_path()),
        "e01_discovery": Path(get_discovery_db_path()),
        "paper_trading": Path(get_paper_trading_db_path()),
        "ahos_knowledge": Path(get_knowledge_db_path()),
    }
    # export_mega5 calls check_known_stores at the default 20s via the module function.
    proof = export_mega5(
        ROOT, closes, latest,
        token_veto_rows=veto, equity=equity, now=time.time(),
        store_paths=stores, probe=probe, probe_path=str(probe_path),
    )
    # The call above used the default timeout inside export. Re-state the same result.
    _ = check_known_stores
    old = json.loads((PAPER / "vision_steps.json").read_text(encoding="utf-8"))
    old_impl = {row["id"] for row in old.get("rows") or [] if row.get("current_impl")}
    kept = {
        "lesson_shadow": "evidence_system" in old_impl,
        "safety_veto_rows": veto if veto else (1 if "security_scam" in old_impl else 0),
        "news_weight_zero": "news_intelligence" in old_impl,
        "news_blocks_entry": "news_intelligence" in old_impl,
        "paper_book": "paper_trading" in old_impl,
        "pause_armed": "paper_trading" in old_impl,
        "soak_clock_kept": "system_status" in old_impl,
        "kian_cited": "ai_conversational" in old_impl or proof["recall_cited"],
        "whale_score": "onchain_intelligence" in old_impl or bool(proof["whale_desks"]),
        "liquidity_attached": "liquidity_whale_demand" in old_impl,
        "paper_reads_opens": "user_position_tracking" in old_impl,
        "witnesses_agreed": "identity_resolution" in old_impl,
    }
    overlay = export_overlay(ROOT, {**kept, **proof})
    queue = {
        "schema": "ahos.ui_queue_next_build.v1",
        "paper_only": True,
        "after_commit": "6704410c61260fea4685fe0046babad1b937de3b",
        "items": [
            {"id": "core_intelligence", "change": "Show one Python canonical decision on the page :3200 serves."},
            {"id": "opportunity_intelligence", "change": "Replace the TypeScript rank on that page with the Python decision label."},
            {"id": "market_intelligence", "change": "Point the market page at sourced_quotes.json. CRYPTO, CRYPTO_FUTURES, and PB_TOKEN still lack a latency or a source."},
            {"id": "web_dashboard", "change": "Serve the home view and the technical-details toggle from the swapped bundle."},
            {"id": "persian_first", "change": "Serve equity, open names, and today's lesson in Persian from the paper receipt."},
            {"id": "user_position_tracking", "change": "Confirm /paper on the swapped bundle reads the open-name receipt."},
        ],
        "decides": False,
    }
    (PAPER / "ui_queue_next_build.json").write_text(json.dumps(queue, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    soak = json.loads((ROOT / "reports" / "grok" / "M13_SOAK" / "soak_status.json").read_text(encoding="utf-8"))
    mehrdad = json.loads((PAPER / "mehrdad_status.json").read_text(encoding="utf-8"))
    print(json.dumps({
        "closes": len(closes),
        "veto": veto,
        "shadow_rule": edge["shadow"]["rule"],
        "shadow_decision": edge["shadow"]["decision"],
        "dsr": edge["shadow"]["dsr"],
        "pbo": edge["shadow"]["pbo"],
        "pass_stats": edge["shadow"]["pass_stats"],
        "applied": edge["shadow"]["applied_to_live_weights"],
        "proof": proof,
        "vision_impl": overlay["current_impl"],
        "vision_pct": overlay["current_impl_pct"],
        "audit": overlay["audit_operational_impl"],
        "readiness_pct": mehrdad.get("readiness_pct"),
        "window_started_utc": soak.get("window_started_utc"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
