"""Tests for M32 Cross-Desk Reconcile Bridge, M48 Dependency Lock Audit, and M36 Autonomous World Orchestrator."""
from __future__ import annotations

from architecture.health.dependency_lock_audit import audit_dependency_locks
from architecture.markets.reconcile_bridge import reconcile_desk_states
from architecture.mission.world_orchestrator import run_autonomous_world_cycle


def test_m32_reconcile_bridge_clean_and_drift_detection() -> None:
    clean = reconcile_desk_states()
    assert clean["paper_only"] is True
    assert clean["overall_verdict"] == "CLEAN"
    assert clean["desks_reconciled"] == 7

    drifted = reconcile_desk_states(
        [
            {
                "desk": "GOLD",
                "mission_id": "M13-GOLD-SOAK",
                "ledger_equity_usd": 10000.0,
                "reported_equity_usd": 9950.0,
                "chain_ok": True,
            }
        ]
    )
    assert drifted["overall_verdict"] == "RECONCILE_DRIFT_HALT"


def test_m48_dependency_lock_audit_refuses_bad_proposals() -> None:
    audit = audit_dependency_locks(
        candidate_additions=[
            {
                "name": "ccxt-live-executor",
                "sha256": "abc",
                "rollback_plan": "git checkout",
                "cve_count": 0,
            },
            {
                "name": "vulnerable-pkg",
                "sha256": "def",
                "rollback_plan": "git checkout",
                "cve_count": 2,
            },
            {
                "name": "skfolio-clean",
                "sha256": "sha256:123456",
                "rollback_plan": "revert requirements",
                "cve_count": 0,
            },
        ]
    )
    assert audit["lockfile_mutated"] is False
    assert audit["arena_lockfile_present"] is True
    assert len(audit["rejected_proposals"]) == 2
    assert len(audit["accepted_proposals"]) == 1


def test_m36_autonomous_world_orchestrator_end_to_end() -> None:
    world = run_autonomous_world_cycle()
    assert world["paper_only"] is True
    assert world["live_trading"] is False
    assert world["world_state"] == "NOMINAL_PAPER_AUTONOMOUS"
    subs = world["subsystems"]
    assert subs["m70_safety_lock"] == "LOCKED_CLEAN"
    assert subs["m19_multi_market"]["verified_count"] == 13
    assert subs["m33_token_hunter"]["paper_watch_eligible"] == 2
    assert subs["m33_token_hunter"]["veto_unsafe"] == 2
    assert subs["m32_m42_reconcile"]["verdict"] == "CLEAN"
    assert subs["m30_canonical_memory"]["chain_ok"] is True
    assert subs["m56_tournament"]["auto_promote"] is False
    assert subs["m60_astra_engine"]["overall_status"] == "SHADOW_PAPER_ACTIVE"
    assert subs["m64_negahban_security"]["overall_verdict"] == "CLEAN"
    brain = subs["m60_m70_aci_agi_si_brain"]
    assert brain["day_1_agi_claimed"] is False
    assert brain["compounding_capability_index"] is not None
    assert brain["current_stage_id"]
    organs = subs["m57_whole_ahos_organs"]
    assert organs["organs_covered_count"] == 8
    assert organs["trading_only"] is False
