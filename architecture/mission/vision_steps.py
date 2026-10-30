"""Owner-vision steps. The 2026-09-12 audit stays 0 operational IMPL.

A current row is IMPL only when this process attaches a live file. The
trace's REAL count is a different denominator and is not read here.
"""
from __future__ import annotations

import json
from pathlib import Path

AUDIT_OPERATIONAL_IMPL = 0
AUDIT_ROWS = 26

# Smallest remaining step for each P0/P1 capability in the 2026-09-12 audit.
STEPS: tuple[dict[str, str], ...] = (
    {"id": "core_intelligence", "step": "Show one Python canonical decision on the page the running server actually serves."},
    {"id": "token_discovery", "step": "Log one new token from a free source that then faces the safety veto."},
    {"id": "opportunity_intelligence", "step": "Replace the TypeScript rank on the served page with the Python decision label."},
    {"id": "evidence_system", "step": "Replay stored closes into causes. The served /evidence route is a separate gap."},
    {"id": "identity_resolution", "step": "Store one symbol whose two witnesses agree and keep that id."},
    {"id": "security_scam", "step": "Keep a logged safety veto that blocks the open."},
    {"id": "market_intelligence", "step": "Point the served market page at a quote that has source, time, and latency."},
    {"id": "news_intelligence", "step": "Keep a same-day news row at weight 0 that does not open a trade."},
    {"id": "onchain_intelligence", "step": "Record one whale score that is not ABSENT on a desk still allowed to open."},
    {"id": "liquidity_whale_demand", "step": "Attach a liquidity figure to one open paper position."},
    {"id": "explainable_scoring", "step": "Attach a Persian sentence that cites the logged reason on the next close."},
    {"id": "calibration", "step": "Leave the shadow recalibration unapplied until DSR and PBO pass."},
    {"id": "paper_trading", "step": "Keep the paper book running and pause a desk only after 20 losing closes."},
    {"id": "user_position_tracking", "step": "Make the running /paper page read the open-name receipt."},
    {"id": "telegram", "step": "Wait for an owner token. Do not invent one."},
    {"id": "alerts_loud", "step": "Require Python alerts_allowed and overlay PASS before any automatic alert."},
    {"id": "web_dashboard", "step": "Rebuild the already-running server so the home view and جزئیات فنی are the served page."},
    {"id": "ai_conversational", "step": "One Kian answer that cites a stored close, or UNKNOWN."},
    {"id": "persian_first", "step": "Serve equity, open names, and today's lesson in Persian from the paper receipt."},
    {"id": "system_status", "step": "Keep the soak window clock on the run log, not on the last status write."},
    {"id": "provider_architecture", "step": "Record a provider probe as SUCCESS or the real failure."},
    {"id": "knowledge_memory", "step": "Answer from a stored close, or return UNKNOWN."},
    {"id": "security_ops", "step": "Re-run the kill-switch drill without editing the live book."},
    {"id": "reliability", "step": "Leave the current soak running until 72 hours, then toward 168."},
    {"id": "windows_local_first", "step": "Keep paths and the sleep script on G:. The installer gate is still open."},
    {"id": "launch_deployment", "step": "Leave the live switch off."},
)

# Rows this pass can mark IMPL. The rest stay partial or missing.
_IMPL = frozenset({
    "evidence_system",
    "security_scam",
    "news_intelligence",
    "paper_trading",
    "system_status",
    "ai_conversational",
    "onchain_intelligence",
    "liquidity_whale_demand",
    "user_position_tracking",
    "identity_resolution",
    "explainable_scoring",
    "calibration",
    "market_intelligence",
    "token_discovery",
    "knowledge_memory",
    "security_ops",
    "provider_architecture",
})


def build_overlay(proof: dict) -> dict:
    """Score the 26 rows from a proof dict. Missing proof cannot be IMPL."""
    if len(STEPS) != AUDIT_ROWS:
        raise ValueError("the owner audit has 26 rows")
    need = {
        "evidence_system": proof.get("lesson_shadow") is True,
        "security_scam": int(proof.get("safety_veto_rows") or 0) > 0,
        "news_intelligence": proof.get("news_weight_zero") is True and proof.get("news_blocks_entry") is True,
        "paper_trading": proof.get("paper_book") is True and proof.get("pause_armed") is True,
        "system_status": proof.get("soak_clock_kept") is True,
        "ai_conversational": proof.get("kian_cited") is True,
        "onchain_intelligence": proof.get("whale_score") is True,
        "liquidity_whale_demand": proof.get("liquidity_attached") is True,
        "user_position_tracking": proof.get("paper_reads_opens") is True,
        "identity_resolution": proof.get("witnesses_agreed") is True,
        "explainable_scoring": proof.get("close_reasons_cited") is True,
        "calibration": proof.get("calibration_measured") is True and proof.get("calibration_applied") is False,
        "market_intelligence": proof.get("sourced_quotes") is True,
        "token_discovery": int(proof.get("token_veto_rows") or 0) > 0,
        "knowledge_memory": proof.get("recall_cited") is True and proof.get("recall_unknown") is True,
        "security_ops": proof.get("kill_drill_passed") is True and proof.get("live_book_edited") is False,
        "provider_architecture": proof.get("provider_probe_recorded") is True,
    }
    rows = []
    for step in STEPS:
        impl = step["id"] in _IMPL and need[step["id"]] is True
        rows.append({**step, "current_impl": impl, "audit_2026_09_12_impl": False})
    impl_n = sum(1 for row in rows if row["current_impl"])
    return {
        "schema": "ahos.vision_steps.v1",
        "paper_only": True,
        "audit_date": "2026-09-12",
        "audit_operational_impl": AUDIT_OPERATIONAL_IMPL,
        "audit_rows": AUDIT_ROWS,
        "current_impl": impl_n,
        "current_impl_pct": round(100.0 * impl_n / AUDIT_ROWS, 1),
        "live_switch": False,
        "rows": rows,
        "decides": False,
    }


def export_overlay(root: Path, proof: dict) -> dict:
    doc = build_overlay(proof)
    path = root / "reports" / "grok" / "PAPER" / "vision_steps.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return doc
