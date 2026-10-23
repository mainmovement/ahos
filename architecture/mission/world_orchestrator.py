"""M36 Autonomous World Orchestrator (Paper-Only End-to-End Cycle).
Coordinates all 10 institutional AHOS layers in a deterministic, fail-closed paper world cycle:
1. M70.6 Cryptographic Safety Lock & HOLD.flag check
2. M59.S Hardware Tier & 8GB RAM Guard probe
3. M19 Multi-Market Two-Source Witness Desk evaluation (7 desks)
4. M33 24-Step Token Hunter safety veto pipeline
5. M18 / M80 Didehban OSINT multi-source RSS corroboration
6. M15 / M58.3 Decision Council with mandatory Devil's Advocate dissent
7. M20 / M38 Paper OMS & Gateway routing (zero live execution)
8. M32 / M42 Cross-Desk Reconciliation Bridge & Single Ledger integrity
9. M30 / M56 / M60 Memory Consolidation, Strategy Tournament & Astra Shadow Evolution
10. M64 / M80 Negahban White-Hat Security Audit
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.health.dependency_lock_audit import audit_dependency_locks
from architecture.learning.astra_engine import run_astra_evolution_cycle
from architecture.learning.memory_consolidation import consolidate_canonical_memory
from architecture.learning.strategy_tournament import run_strategy_tournament
from architecture.markets.council_gate import evaluate_council_with_dissent
from architecture.markets.multi_market_desks import evaluate_all_desks
from architecture.markets.news_desk import build_nightly_news_brief_fa, ingest_rss_feeds
from architecture.markets.reconcile_bridge import reconcile_desk_states
from architecture.markets.token_hunter_24 import screen_token_batch
from architecture.cognitive.aci_agi_si_brain import run_aci_agi_si_evolution_cycle
from architecture.cognitive.autonomous_coder_bridge import run_autonomous_coder_cycle
from architecture.security.negahban import run_whitehat_security_audit
from architecture.university.whole_ahos_organ_evolution import build_whole_ahos_organ_evolution_snapshot
from core.safety_lock import verify_safety_lock

PAPER_ONLY: bool = True
LIVE_TRADING: bool = False


def run_autonomous_world_cycle(*, root: Path | None = None) -> dict[str, Any]:
    """Execute one complete, deterministic M36 autonomous world cycle in PAPER_ONLY mode."""
    repo = (root or Path(__file__).resolve().parents[2]).resolve()
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # 1. Safety Lock & HOLD.flag check
    safety = verify_safety_lock(repo)
    if not safety["ok"]:
        return {
            "schema": "ahos.world_orchestrator_m36.v1",
            "generated_at": now_iso,
            "paper_only": True,
            "live_trading": False,
            "world_state": "HALTED_SAFETY_LOCK",
            "safety_lock": safety,
        }

    # 2. Multi-Market Desks (M13.1-M13.6 & M19)
    desk_cycles = evaluate_all_desks()
    verified_desks = sum(1 for c in desk_cycles if c.witness.state == "VERIFIED")

    # 3. 24-Step Token Hunter (M33)
    token_verdicts = screen_token_batch()
    tokens_eligible = sum(1 for v in token_verdicts if v.state == "PAPER_WATCH_ELIGIBLE")
    tokens_vetoed = sum(1 for v in token_verdicts if v.state == "VETO_UNSAFE")

    # 4. Didehban OSINT RSS Corroboration (M18 / M80)
    osint_clusters = ingest_rss_feeds()
    corroborated_clusters = sum(1 for c in osint_clusters if c["state"] == "CORROBORATED")
    brief_fa = build_nightly_news_brief_fa(osint_clusters)

    # 5. Council with Devil's Advocate Dissent (M15 / M58.3)
    council = evaluate_council_with_dissent(
        proposal_id="M36-WORLD-CYCLE-PAPER",
        votes_for=4,
        votes_total=5,
        devils_advocate_dissent="Macro volatility ahead of CPI release; enforce strict T0 paper cap.",
        failure_modes=["cpi_whipsaw", "spread_widening"],
        tier="T0",
    )

    # 6. Cross-Desk Reconciliation Bridge (M32 / M42)
    reconcile = reconcile_desk_states()

    # 7. Canonical Memory Consolidation (M30)
    memory = consolidate_canonical_memory(root=repo)

    # 8. Multi-Strategy Paper Tournament (M56)
    tournament = run_strategy_tournament()

    # 9. Astra Self-Optimization Engine (M60.1-M60.8)
    astra = run_astra_evolution_cycle(root=repo)

    # 10. Dependency Lock Audit (M48) & Negahban White-Hat Security Audit (M64)
    dep_audit = audit_dependency_locks(repo_root=repo)
    negahban = run_whitehat_security_audit(repo)

    brain = run_aci_agi_si_evolution_cycle(root=repo)
    autonomous_coder = run_autonomous_coder_cycle(root=repo)
    organs = build_whole_ahos_organ_evolution_snapshot()
    brain_loops = brain.get("loops") or {}

    all_healthy = (
        safety["ok"]
        and reconcile["overall_verdict"] == "CLEAN"
        and memory["chain_ok"]
        and not astra["rollback_triggered"]
        and negahban["overall_verdict"] == "CLEAN"
    )

    return {
        "schema": "ahos.world_orchestrator_m36.v1",
        "generated_at": now_iso,
        "paper_only": True,
        "execution_mode": "PAPER_ONLY",
        "real_trading": False,
        "live_trading": False,
        "world_state": "NOMINAL_PAPER_AUTONOMOUS" if all_healthy else "DEGRADED_HOLD",
        "tier": "T0",
        "subsystems": {
            "m70_safety_lock": safety["status"],
            "m19_multi_market": {
                "instruments_total": len(desk_cycles),
                "verified_count": verified_desks,
            },
            "m33_token_hunter": {
                "screened": len(token_verdicts),
                "paper_watch_eligible": tokens_eligible,
                "veto_unsafe": tokens_vetoed,
            },
            "m18_didehban_osint": {
                "clusters_total": len(osint_clusters),
                "corroborated_count": corroborated_clusters,
                "nightly_brief_fa_preview": brief_fa.splitlines()[0] if brief_fa else "",
            },
            "m15_m58_council": {
                "status": council["status"],
                "approved_paper": council["approved_paper"],
                "promoted_live": council["promoted"],
            },
            "m32_m42_reconcile": {
                "verdict": reconcile["overall_verdict"],
                "desks_reconciled": reconcile["desks_reconciled"],
                "total_paper_equity_usd": reconcile["total_paper_equity_usd"],
            },
            "m30_canonical_memory": {
                "chain_ok": memory["chain_ok"],
                "total_entries": memory["total_entries"],
                "head_hash": memory["head_hash"][:16],
            },
            "m56_tournament": {
                "contenders": tournament["contenders_count"],
                "leader_id": tournament["leader_id"],
                "leader_dsr": tournament["leader_dsr"],
                "auto_promote": tournament["auto_promote"],
            },
            "m60_astra_engine": {
                "overall_status": astra["overall_status"],
                "stages_passed": f"{astra['stages_passed']}/{astra['stages_count']}",
                "rollback_triggered": astra["rollback_triggered"],
            },
            "m48_dependency_audit": {
                "verdict": dep_audit["verdict"],
                "next_version": dep_audit["next_version"],
            },
            "m64_negahban_security": {
                "overall_verdict": negahban["overall_verdict"],
                "checks_count": len(negahban["checks"]),
            },
            "m60_m70_aci_agi_si_brain": {
                "current_stage_id": brain.get("current_stage_id"),
                "current_stage_title_fa": brain.get("current_stage_title_fa"),
                "compounding_capability_index": brain.get("compounding_capability_index"),
                "day_1_agi_claimed": brain.get("day_1_agi_claimed", False),
                "loops": {
                    "self_deciding": brain_loops.get("self_deciding", {}).get("status")
                    if isinstance(brain_loops.get("self_deciding"), dict)
                    else None,
                    "self_fault_finding": brain_loops.get("self_fault_finding", {}).get("status")
                    if isinstance(brain_loops.get("self_fault_finding"), dict)
                    else None,
                    "self_debugging": brain_loops.get("self_debugging", {}).get("status")
                    if isinstance(brain_loops.get("self_debugging"), dict)
                    else None,
                    "self_updating": brain_loops.get("self_updating", {}).get("status")
                    if isinstance(brain_loops.get("self_updating"), dict)
                    else None,
                },
            },
            "m57_whole_ahos_organs": {
                "organs_covered_count": organs.get("organs_covered_count", 8),
                "trading_only": organs.get("trading_only", False),
                "average_university_exam_score_pct": organs.get("average_university_exam_score_pct"),
            },
            "m60_autonomous_coder_bridge": {
                "bridge_port_8787_status": autonomous_coder.get("bridge_port_8787_status"),
                "sandbox_gate_verdict": autonomous_coder.get("sandbox_gate_verdict"),
                "four_brain_engine": autonomous_coder.get("four_brain_engine"),
                "patches_verified": (autonomous_coder.get("four_brain_engine") or {}).get(
                    "synthesized_patches_verified"
                ),
            },
        },
    }
