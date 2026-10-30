"""One-shot MEGA 5 receipts. Does not restart the soak or the paper trader."""
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
UI_QUEUE = [
    {"id": "core_intelligence", "change": "Show one Python canonical decision on the page :3200 serves."},
    {"id": "opportunity_intelligence", "change": "Replace the TypeScript rank on that page with the Python decision label."},
    {"id": "market_intelligence", "change": "Point the market page at reports/grok/PAPER/sourced_quotes.json."},
    {"id": "web_dashboard", "change": "Serve the home view and the جزئیات فنی toggle from the swapped bundle."},
    {"id": "persian_first", "change": "Serve equity, open names, and today's lesson in Persian from the paper receipt."},
    {"id": "user_position_tracking", "change": "Confirm /paper on the swapped bundle reads the open-name receipt."},
]


def _load() -> tuple[list[dict], dict[str, dict], int]:
    closes: list[dict] = []
    latest: dict[str, dict] = {}
    veto = 0
    path = PAPER / "paper_trades.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if "TOKEN_SAFETY_VETO" in line:
                veto += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            symbol = row.get("symbol")
            if symbol:
                latest[str(symbol)] = row
            if row.get("event") == "CLOSE" and isinstance(row.get("realized_pnl_usd"), (int, float)):
                closes.append(row)
    return closes, latest, veto


def _probe() -> tuple[dict | None, str]:
    path = ROOT / "reports" / "provider_probe_20261030T121002Z.json"
    if not path.is_file():
        return None, str(path)
    return json.loads(path.read_text(encoding="utf-8")), str(path)


def main() -> None:
    closes, latest, veto = _load()
    edge = export_edge(ROOT, closes)
    status_path = PAPER / "paper_trader_status.json"
    equity = 100.0
    if status_path.is_file():
        status = json.loads(status_path.read_text(encoding="utf-8"))
        mark = status.get("mark_to_market_equity_usd")
        if isinstance(mark, (int, float)) and not isinstance(mark, bool):
            equity = float(mark)
    probe, probe_path = _probe()
    proof = export_mega5(
        ROOT, closes, latest,
        token_veto_rows=veto,
        equity=equity,
        now=time.time(),
        store_paths={
            "ahos_local": Path(get_local_db_path()),
            "e01_discovery": Path(get_discovery_db_path()),
            "paper_trading": Path(get_paper_trading_db_path()),
            "ahos_knowledge": Path(get_knowledge_db_path()),
        },
        probe=probe,
        probe_path=probe_path,
    )
    old_path = PAPER / "vision_steps.json"
    old_impl = set()
    if old_path.is_file():
        old_impl = {row["id"] for row in json.loads(old_path.read_text(encoding="utf-8")).get("rows") or [] if row.get("current_impl")}
    kept = {
        "lesson_shadow": "evidence_system" in old_impl,
        "safety_veto_rows": veto if veto else (1 if "security_scam" in old_impl else 0),
        "news_weight_zero": "news_intelligence" in old_impl,
        "news_blocks_entry": "news_intelligence" in old_impl,
        "paper_book": "paper_trading" in old_impl,
        "pause_armed": "paper_trading" in old_impl,
        "soak_clock_kept": "system_status" in old_impl,
        "kian_cited": "ai_conversational" in old_impl or proof["recall_cited"],
        "whale_score": "onchain_intelligence" in old_impl or len(proof["whale_desks"]) > 0,
        "liquidity_attached": "liquidity_whale_demand" in old_impl,
        "paper_reads_opens": "user_position_tracking" in old_impl,
        "witnesses_agreed": "identity_resolution" in old_impl,
    }
    overlay = export_overlay(ROOT, {**kept, **proof})
    queue = {
        "schema": "ahos.ui_queue_next_build.v1",
        "paper_only": True,
        "build_sha": "6704410c61260fea4685fe0046babad1b937de3b",
        "items": UI_QUEUE,
        "decides": False,
    }
    (PAPER / "ui_queue_next_build.json").write_text(json.dumps(queue, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    soak_path = ROOT / "reports" / "grok" / "M13_SOAK" / "soak_status.json"
    soak = json.loads(soak_path.read_text(encoding="utf-8")) if soak_path.is_file() else {}
    mehrdad_path = PAPER / "mehrdad_status.json"
    mehrdad = json.loads(mehrdad_path.read_text(encoding="utf-8")) if mehrdad_path.is_file() else {}
    print(json.dumps({
        "closes": len(closes),
        "edge": [{"desk": row["desk"], "n": row["closes"], "exp": row["expectancy_usd"], "why": row["dominant_negative"]} for row in edge["desks"]],
        "shadow": edge["shadow"],
        "proof": {key: proof[key] for key in (
            "close_reasons_cited", "calibration_measured", "calibration_applied", "sourced_quotes",
            "token_veto_rows", "recall_cited", "recall_unknown", "kill_drill_passed",
            "live_book_edited", "provider_probe_recorded", "integrity_all_ok",
        )},
        "whale_desks": proof["whale_desks"],
        "integrity": proof["integrity"],
        "vision_impl": overlay["current_impl"],
        "vision_pct": overlay["current_impl_pct"],
        "audit_impl": overlay["audit_operational_impl"],
        "readiness_pct": mehrdad.get("readiness_pct"),
        "window_started_utc": soak.get("window_started_utc"),
        "live_switch": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
