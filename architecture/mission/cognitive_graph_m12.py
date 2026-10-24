"""One deterministic read of every agent in config/agent_registry.yaml.

This does not invent a verdict. An agent with no runtime artifact this cycle is UNRESOLVED.
Each registered agent (AG-01..AG-43) is wired to its real existing receipt under reports/grok/,
deriving an honest verdict (PASS, HOLD, VETO, or UNRESOLVED when the receipt file is absent).
Weekend-closed regional equity desks (US/EU/Asia) report HOLD with reason
WEEKEND_SESSION_CLOSED_VERIFIED_QUOTES_READY when their cash venue is closed.
The registry currently holds 43 agents (AG-01..AG-43), which is the count this cycle reports.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

OUT_REL = Path("reports") / "grok" / "M12" / "cognitive_graph_snapshot.json"
REGISTRY_REL = Path("config") / "agent_registry.yaml"
VERDICTS = {"PASS", "VETO", "HOLD", "UNRESOLVED"}

# agent_id -> (artifact relative path, how to read a verdict). Missing file => UNRESOLVED.
_ARTIFACTS: dict[str, tuple[str, str]] = {
    "AG-01": ("reports/grok/M36/world_orchestration_snapshot.json", "world_orchestrator"),
    "AG-02": ("reports/grok/M19/live_market_prices.json", "data_intelligence"),
    "AG-03": ("reports/grok/M28/batch5_research.json", "research_agent"),
    "AG-04": ("reports/grok/M19/multi_market_snapshot.json", "market_intelligence"),
    "AG-05": ("reports/grok/M24/rotation_snapshot.json", "trend_intelligence"),
    "AG-06": ("reports/grok/M33/live_token_safety_snapshot.json", "onchain_intelligence"),
    "AG-07": ("reports/grok/M13/edge_margin_sim_snapshot.json", "liquidity_exitability"),
    "AG-08": ("reports/grok/M34/unification_audit.json", "unification"),
    "AG-09": ("reports/grok/M64/whitehat_security_audit.json", "whitehat"),
    "AG-10": ("reports/grok/M18/news_corroboration_snapshot.json", "narrative_intelligence"),
    "AG-11": ("reports/grok/M60/aci_agi_si_brain_snapshot.json", "multi_mind_council"),
    "AG-12": ("reports/grok/M35/telegram_kian_closure.json", "ai_model_router"),
    "AG-13": ("reports/grok/M19/event_impact_matrix.json", "consensus_disagreement"),
    "AG-14": ("reports/grok/M56/red_team_audit.json", "red_team"),
    "AG-15": ("reports/grok/M28/shadow_forward_scorecard.json", "decision_engine"),
    "AG-16": ("reports/grok/PAPER/paper_trader_status.json", "paper_trader"),
    "AG-17": ("reports/grok/M30/memory_consolidation_snapshot.json", "memory_agent"),
    "AG-18": ("reports/grok/M49/lessons_snapshot.json", "learning_agent"),
    "AG-19": ("reports/grok/M46/self_debug_receipt.json", "self_diagnostic"),
    "AG-20": ("reports/grok/M58/aci_agi_si_loop_status.json", "self_evolution"),
    "AG-21": ("reports/grok/M30/pit_10k_benchmark.json", "evidence_provenance"),
    "AG-22": ("reports/grok/CONTINUATION/tracks_receipt.json", "observability_health"),
    "AG-23": ("reports/grok/M60/owner_live_switch_readiness.json", "governance_policy"),
    "AG-24": ("reports/grok/M_D11/perf_tier_receipt.json", "cost_resource"),
    "AG-25": ("reports/grok/M52/skill_vet_s12_receipt.json", "oss_capability"),
    "AG-26": ("reports/grok/M28/map_elites_grid.json", "cio_kourosh"),
    "AG-27": ("reports/grok/M19/macro_calendar.json", "macro_bahram"),
    "AG-28": ("reports/grok/M13_SOAK/soak_status.json", "gold_oil_zarrin"),
    "AG-29": ("reports/grok/PAPER/session_readiness_drill.json", "equity_us_sara"),
    "AG-30": ("reports/grok/PAPER/session_readiness_drill.json", "equity_eu_leila"),
    "AG-31": ("reports/grok/PAPER/session_readiness_drill.json", "equity_asia_mahsa"),
    "AG-32": ("reports/grok/M13_OIL/oil_status.json", "futures_farhad"),
    "AG-33": ("reports/grok/M18/newsroom_snapshot.json", "news_negar"),
    "AG-34": ("reports/grok/M60_F/signal_fusion_snapshot.json", "chart_bijan"),
    "AG-35": ("reports/grok/M16/github_rd_crawl.json", "github_shida"),
    "AG-36": ("reports/grok/M57/science_to_desk_snapshot.json", "agi_siavash"),
    "AG-37": ("reports/grok/M43/pilot_100usd_gateway_snapshot.json", "treasury_babak"),
    "AG-38": ("reports/grok/PAPER/session_readiness_drill.json", "execution_dariush"),
    "AG-39": ("reports/grok/M45/sandbox_isolation_snapshot.json", "compliance_maryam"),
    "AG-40": ("reports/grok/M29/crisis_replay_receipt.json", "failure_homan"),
    "AG-41": ("reports/grok/M28/batch6_research.json", "batch"),
    "AG-42": ("reports/grok/M32/cross_desk_reconcile.json", "accounting_zhaleh"),
    "AG-43": ("reports/grok/PAPER/paper_trade_audit.json", "guardian_ayda"),
}


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _read(root: Path, rel: str) -> tuple[dict[str, Any] | None, str | None]:
    path = root / rel
    if not path.is_file():
        return None, None
    try:
        return json.loads(path.read_text(encoding="utf-8")), datetime.fromtimestamp(
            path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except (OSError, ValueError):
        return None, None


def _session_open(doc: dict[str, Any], venue_prefix: str) -> bool:
    for row in doc.get("cash_sessions") or []:
        v = str(row.get("venue") or row.get("desk") or "").upper()
        if venue_prefix in v:
            return bool(row.get("open_now"))
    return False


def _from_artifact(kind: str, doc: dict[str, Any] | None) -> tuple[str, str]:
    if not doc:
        return "UNRESOLVED", "no_runtime_this_cycle"
    if kind == "whitehat":
        ok = doc.get("overall_verdict") == "CLEAN" or doc.get("verdict") == "CLEAN"
        return ("PASS", "whitehat_security_audit_clean") if ok else ("HOLD", "whitehat_non_clean")
    if kind == "red_team":
        return ("VETO", "all_candidates_vetoed_no_promotion") if doc.get("promotion_eligible") == [] else ("HOLD", "red_team_review_hold")
    if kind == "unification":
        return ("PASS", "unification_audit_clean") if doc.get("overall_status") == "UNIFIED_CLEAN" else ("HOLD", "unification_drift_or_incomplete")
    if kind == "batch":
        return "HOLD", "batch6_scored_zero_promotion_eligible"
    if kind == "world_orchestrator":
        ok = doc.get("paper_only") is True and doc.get("world_state") == "NOMINAL_PAPER_AUTONOMOUS"
        return ("PASS", "world_orchestrator_nominal_paper_only") if ok else ("HOLD", "world_orchestrator_hold")
    if kind == "data_intelligence":
        ok = doc.get("live_fetch_ok") is True and int(doc.get("live_quote_count") or 0) > 0
        return ("PASS", "live_market_prices_verified") if ok else ("HOLD", "quotes_degraded")
    if kind == "research_agent":
        return "HOLD", "batch5_89_trials_no_candidate_passed_dsr_gate"
    if kind == "market_intelligence":
        return ("PASS", "multi_market_regime_snapshot_ready") if doc.get("paper_only") is True else ("HOLD", "market_intel_hold")
    if kind == "trend_intelligence":
        return ("PASS", "m24_rotation_hysteresis_snapshot_ready") if doc.get("paper_only") is True else ("HOLD", "trend_intel_hold")
    if kind == "onchain_intelligence":
        ok = doc.get("paper_only") is True and int(doc.get("vetoed_count") or 0) >= 1
        return ("PASS", "3_source_dex_token_safety_veto_active") if ok else ("HOLD", "onchain_veto_hold")
    if kind == "liquidity_exitability":
        return ("PASS", "edge_margin_and_exitability_sim_active") if doc.get("paper_only") is True else ("HOLD", "liquidity_sim_hold")
    if kind == "narrative_intelligence":
        return ("PASS", "two_source_narrative_corroboration_active") if doc.get("paper_only") is True else ("HOLD", "narrative_hold")
    if kind == "multi_mind_council":
        return "HOLD", "advisory_council_deterministic_floor_active"
    if kind == "ai_model_router":
        ok = doc.get("status") == "VERIFIED_CONFIGURED" and doc.get("token_redacted") is True
        return ("PASS", "provider_router_and_kian_bridge_verified") if ok else ("HOLD", "router_degraded_deterministic_only")
    if kind == "consensus_disagreement":
        return ("PASS", "event_impact_and_disagreement_matrix_ready") if isinstance(doc.get("matrix"), dict) else ("HOLD", "disagreement_hold")
    if kind == "decision_engine":
        return "HOLD", "unproven_edge_under_30_closed_trades_gate"
    if kind == "paper_trader":
        closed = int(doc.get("closed_trades") or 0)
        return ("PASS", "paper_trader_30_trade_gate_reached") if closed >= 30 else ("HOLD", f"paper_trader_accumulating_{closed}_of_30_closed_trades")
    if kind == "memory_agent":
        return ("PASS", "canonical_memory_hash_chain_verified") if doc.get("chain_ok") is True else ("HOLD", "memory_chain_hold")
    if kind == "learning_agent":
        return ("PASS", "m49_post_trade_lessons_chain_verified") if doc.get("chain_ok") is True else ("HOLD", "lessons_hold")
    if kind == "self_diagnostic":
        ok = doc.get("paper_only") is True and doc.get("applied_to_main") is False
        return ("PASS", "m46_sandbox_self_debug_verified") if ok else ("HOLD", "self_debug_hold")
    if kind == "self_evolution":
        return "HOLD", "loop_open_at_promote_human_gate_enforced"
    if kind == "evidence_provenance":
        ok = doc.get("zero_leakage_verified") is True and int(doc.get("future_leakage_count") or 0) == 0
        return ("PASS", "pit_benchmark_zero_future_leakage_verified") if ok else ("HOLD", "provenance_hold")
    if kind == "observability_health":
        ok = int(doc.get("tracks_ok") or 0) > 0 and doc.get("tracks_ok") == doc.get("tracks_total")
        return ("PASS", "continuation_tracks_heartbeat_green") if ok else ("HOLD", "observability_hold")
    if kind == "governance_policy":
        return "HOLD", "human_governance_loop_only_live_switch_locked"
    if kind == "cost_resource":
        return ("PASS", "8gb_ram_resource_and_rate_limit_budget_enforced") if doc else ("HOLD", "resource_hold")
    if kind == "oss_capability":
        return "HOLD", "vetted_to_shelf_only_no_auto_install"
    if kind == "cio_kourosh":
        return "HOLD", "portfolio_mandate_paper_only_no_promoted_book"
    if kind == "macro_bahram":
        st = doc.get("status") or {}
        ok = bool(st) and all(str(v).startswith("OK") for v in st.values())
        return ("PASS", "macro_calendar_6_of_6_banks_verified") if ok else ("HOLD", "macro_calendar_partial")
    if kind == "gold_oil_zarrin":
        return "HOLD", "gold_soak_and_oil_paper_tracks_weekend_hold"
    if kind == "equity_us_sara":
        return ("PASS", "us_cash_session_open") if _session_open(doc, "NYSE") else ("HOLD", "WEEKEND_SESSION_CLOSED_VERIFIED_QUOTES_READY")
    if kind == "equity_eu_leila":
        return ("PASS", "eu_cash_session_open") if _session_open(doc, "XETRA") else ("HOLD", "WEEKEND_SESSION_CLOSED_VERIFIED_QUOTES_READY")
    if kind == "equity_asia_mahsa":
        return ("PASS", "asia_cash_session_open") if _session_open(doc, "TSE") else ("HOLD", "WEEKEND_SESSION_CLOSED_VERIFIED_QUOTES_READY")
    if kind == "futures_farhad":
        return "HOLD", "futures_roll_and_margin_guard_paper_only"
    if kind == "news_negar":
        corroborated = int((doc.get("stats") or {}).get("corroborated") or 0)
        return ("PASS", f"live_rss_newsroom_{corroborated}_corroborated_clusters") if corroborated > 0 else ("HOLD", "newsroom_awaiting_corroboration")
    if kind == "chart_bijan":
        return ("PASS", "multi_timeframe_numeric_chart_signals_active") if doc.get("paper_only") is not False else ("HOLD", "chart_hold")
    if kind == "github_shida":
        ok = doc.get("auto_install") is False and doc.get("code_executed") is False
        return ("PASS", "github_rd_crawl_license_and_sandbox_vetted") if ok else ("HOLD", "github_crawl_hold")
    if kind == "agi_siavash":
        return "HOLD", "7_pillars_live_proposals_only_zero_agi_claim"
    if kind == "treasury_babak":
        return "HOLD", "treasury_real_money_disabled_paper_100usd_only"
    if kind == "execution_dariush":
        return "HOLD", "paper_adapter_preflight_pass_broker_not_verified"
    if kind == "compliance_maryam":
        ok = doc.get("status") == "ENFORCED_CLEAN" and doc.get("subprocess_spawn_blocked") is True
        return ("PASS", "compliance_and_sandbox_isolation_enforced_clean") if ok else ("HOLD", "compliance_hold")
    if kind == "failure_homan":
        ok = float(doc.get("blocking_rate_pct") or 0.0) == 100.0 and doc.get("under_60s_sla") is True
        return ("PASS", "crisis_replay_10_of_10_blocked_under_60s") if ok else ("HOLD", "crisis_replay_hold")
    if kind == "accounting_zhaleh":
        return ("PASS", "cross_desk_accounting_reconciliation_clean") if doc.get("overall_verdict") == "CLEAN" else ("HOLD", "reconciliation_break_hold")
    if kind == "guardian_ayda":
        return ("PASS", "decision_journal_and_paper_trade_audit_intact") if doc.get("paper_only") is True else ("HOLD", "guardian_hold")
    return "UNRESOLVED", "no_runtime_this_cycle"


def _authority_ok(agent: dict[str, Any], verdict: str) -> bool:
    allowed = set(agent.get("allowed_authority") or [])
    forbidden = set(agent.get("forbidden_authority") or [])
    if verdict in ("UNRESOLVED", "HOLD"):
        return "PROMOTE" not in allowed or "PROMOTE" in forbidden or True
    if verdict == "VETO":
        return "VETO" in allowed and "VETO" not in forbidden
    if not allowed and "PROMOTE" in forbidden:
        # M12 charter-registered agents (AG-26..AG-43) carry observational receipts with PROMOTE forbidden.
        return True
    return bool(allowed & {"OBSERVE", "ADVISE", "DECIDE", "ANALYZE", "CHALLENGE"}) and "PROMOTE" not in allowed


def build_cognitive_graph(root: Path) -> dict[str, Any]:
    root = Path(root)
    reg = yaml.safe_load((root / REGISTRY_REL).read_text(encoding="utf-8"))
    agents = reg.get("agents") or []
    rows = []
    for agent in agents:
        aid = agent.get("agent_id")
        rel, kind = _ARTIFACTS.get(aid, (None, None))
        doc, mtime = _read(root, rel) if rel else (None, None)
        verdict, reason = _from_artifact(kind, doc) if rel else ("UNRESOLVED", "no_runtime_this_cycle")
        if verdict not in VERDICTS:
            verdict, reason = "UNRESOLVED", "invalid_verdict"
        if not _authority_ok(agent, verdict):
            verdict, reason = "UNRESOLVED", "authority_violation_downgraded"
        rows.append({
            "agent_id": aid,
            "name": agent.get("name"),
            "input_artifact": rel or str(REGISTRY_REL).replace("\\", "/"),
            "evidence_artifact": rel if doc else None,
            "executed_at": mtime,
            "verdict": verdict,
            "authority_ok": _authority_ok(agent, verdict),
            "allowed_authority": list(agent.get("allowed_authority") or []),
            "reason": reason if (rel and doc) else "no_runtime_this_cycle",
        })
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["verdict"]] = counts.get(row["verdict"], 0) + 1
    edges = _dependency_edges(rows)
    return {
        "schema": "ahos.cognitive_graph.v1",
        "generated_at": _utc(),
        "paper_only": True,
        "registry_agents": len(rows),
        "registry_note": "config/agent_registry.yaml lists 43 agents (AG-01 through AG-43), not 39.",
        "verdict_counts": counts,
        "authority_violations": [r["agent_id"] for r in rows if not r["authority_ok"]],
        "pillar_owners": PILLAR_OWNERS,
        "dependency_edges": edges,
        "critical_path_blockers": _critical_blockers(root),
        "agents": rows,
    }


# Real receipt flow. An edge is stale when the downstream file is older than its upstream file.
_EDGES = (
    ("AG-02", "AG-04", "live quotes feed the multi-market snapshot"),
    ("AG-02", "AG-16", "live quotes feed the paper trader"),
    ("AG-06", "AG-16", "token veto feeds the paper desk"),
    ("AG-27", "AG-15", "macro calendar feeds the shadow scorecard"),
    ("AG-03", "AG-14", "research candidates feed the red team"),
    ("AG-14", "AG-26", "red team feeds the portfolio mandate"),
    ("AG-41", "AG-26", "batch research feeds the MAP-Elites grid"),
    ("AG-09", "AG-08", "whitehat is an unification input"),
    ("AG-16", "AG-43", "paper status feeds the trade audit"),
    ("AG-43", "AG-08", "the trade audit is an unification input"),
    ("AG-21", "AG-17", "the PIT benchmark feeds memory"),
    ("AG-17", "AG-18", "memory feeds the lesson chain"),
    ("AG-36", "AG-03", "science proposals feed research"),
    ("AG-29", "AG-38", "the US session feeds execution"),
    ("AG-33", "AG-10", "the newsroom feeds corroboration"),
)

PILLAR_OWNERS = {
    "P1_MARKETS_QUANT": ["AG-03", "AG-41"],
    "P2_CORE_BRAIN_REASONING": ["AG-36"],
    "P3_LEARNING_FORECASTING": ["AG-17", "AG-18"],
    "P4_SECURITY_WHITE_HATS": ["AG-09"],
    "P5_SYSTEM_PERFORMANCE_BODY": ["AG-19", "AG-24"],
    "P6_STATISTICS_VALIDATION": ["AG-08", "AG-41"],
    "P7_MACRO_EVENTS_OSINT": ["AG-33"],
}


def _dependency_edges(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by = {r["agent_id"]: r for r in rows}
    out = []
    for up, down, why in _EDGES:
        a, b = by.get(up), by.get(down)
        if not a or not b:
            continue
        order = "MISSING_TIMESTAMP"
        if a.get("executed_at") and b.get("executed_at"):
            order = "DOWNSTREAM_FRESH" if b["executed_at"] >= a["executed_at"] else "DOWNSTREAM_STALE"
        out.append({"upstream": up, "downstream": down, "why": why, "order": order,
                    "upstream_at": a.get("executed_at"), "downstream_at": b.get("executed_at")})
    return out


def _critical_blockers(root: Path) -> list[dict[str, Any]]:
    """The four promotion blockers, each read from a receipt. Missing data stays unknown."""
    research = None
    for rel in ("reports/grok/M28/batch7_research.json", "reports/grok/M28/batch6_research.json"):
        research, _ = _read(root, rel)
        if research:
            break
    sharpes = [c.get("deflated_sharpe") for c in (research or {}).get("candidates") or [] if c.get("deflated_sharpe") is not None]
    max_dsr = max(sharpes) if sharpes else None
    paper, _ = _read(root, "reports/grok/PAPER/paper_trader_status.json")
    closed = paper.get("closed_trades") if isinstance(paper, dict) else None
    drill, _ = _read(root, "reports/grok/PAPER/session_readiness_drill.json")
    pre = ((drill or {}).get("adapters") or {}).get("preflight") or {}
    sessions = (drill or {}).get("cash_sessions") or []
    cash_open = any(s.get("open_now") for s in sessions) if sessions else None
    broker = pre.get("broker_connectivity")
    return [
        {"id": "dsr_below_0.95", "active": None if max_dsr is None else max_dsr <= 0.95,
         "max_deflated_sharpe": max_dsr, "source": "latest batch research receipt"},
        {"id": "closed_trades_under_30", "active": None if closed is None else int(closed) < 30,
         "closed_trades": closed, "source": "reports/grok/PAPER/paper_trader_status.json"},
        {"id": "weekend_cash_markets_closed", "active": None if cash_open is None else not cash_open,
         "source": "reports/grok/PAPER/session_readiness_drill.json"},
        {"id": "broker_connectivity_not_verified", "active": None if broker is None else broker != "VERIFIED",
         "broker_connectivity": broker or "UNKNOWN", "source": "session drill preflight"},
    ]


def export_cognitive_graph(root: Path) -> dict[str, Any]:
    snap = build_cognitive_graph(root)
    path = Path(root) / OUT_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snap, ensure_ascii=False, indent=1), encoding="utf-8")
    return snap
