"""Paper cores for the open non-page missions. No network and no file deletion."""
from __future__ import annotations

import pytest

from architecture.ai.command_inbox import route_command
from architecture.execution.gateway import PaperOrder
from architecture.health.lab_gate import lab_status
from architecture.health.ops_guard import ops_command
from architecture.health.quarantine import delete_paths, plan
from architecture.health.safety_lock import safety_lock
from architecture.learning.benchmark import BenchPoint, record
from architecture.learning.exam import grade
from architecture.learning.mistakes import from_loss
from architecture.learning.transfer import transfer
from architecture.learning.university import register
from architecture.markets.allocator import allocate
from architecture.markets.arena import rank
from architecture.markets.council_gate import advise
from architecture.markets.crisis import shock
from architecture.markets.marathon import evaluate
from architecture.markets.news_desk import corroborate
from architecture.markets.oms import route
from architecture.markets.readiness import pilot_gate
from architecture.markets.risk_v2 import bound_notional, fractional_kelly
from architecture.markets.token_gate import consider
from architecture.mission.controller import MissionController
from architecture.mission.nightly import build_comprehensive_nightly_digest_fa, render, render_fa
from architecture.mission.teams import register_team
from architecture.security.negahban import scan
from architecture.security.skill_vet import vet
from architecture.security.update_proposal import propose
from architecture.security.whitehat import task
from architecture.treasury.requests import TransferRequest
from architecture.treasury.testnet import submit_testnet
from architecture.treasury.withdrawal import request_withdrawal


def _req(network: str = "owner-whitelist") -> TransferRequest:
    return TransferRequest(
        "w1", 10.0, network, "paper note",
        "2026-10-18T00:00:00Z", "2026-10-18T06:00:00Z",
    )


def test_controller_cannot_promote_or_go_live():
    ctl = MissionController()
    assert ctl.start() == "RUNNING"
    assert ctl.pause() == "PAUSED"
    ctl.start()
    assert ctl.halt() == "HALT"
    assert ctl.start() == "HALT"
    assert ctl.promote() is False
    assert ctl.enable_live() is False
    assert ctl.live is False


def test_oms_books_only_a_paper_eligible_order():
    order = PaperOrder("gold", "buy", 100.0, False)
    assert route(order, "ELIGIBLE").state == "ACCEPTED_PAPER"
    assert route(PaperOrder("gold", "buy", 100.0, True), "ELIGIBLE").state == "REJECTED"
    assert route(order, "UNKNOWN").state == "REJECTED"


def test_risk_sizes_unknown_to_zero_and_respects_the_cap():
    assert fractional_kelly(win_rate=0.6, payoff=1.0, sample=10) == 0.0
    sized = fractional_kelly(win_rate=0.6, payoff=1.0, sample=40)
    assert 0 < sized <= 0.25
    assert bound_notional(5_000, 1_000) == 1_000
    assert bound_notional(5, 0) == 0.0


def test_crisis_halt_and_reports():
    assert shock([100.0], drop_pct=0.2).level == "HALT"
    assert shock([100.0], drop_pct=0.01).entries_allowed is True
    text = render(day="2026-10-18", trades=2, pnl_usd=3)
    assert "NO_PROVEN_EDGE" in text
    assert "کاغذی" in render_fa(day="2026-10-18", trades=2, pnl_usd=3)


def test_nightly_digest_exporter_writes_m31_snapshot(tmp_path, monkeypatch) -> None:
    import json
    from pathlib import Path

    import scripts.export_nightly_digest_snapshot as exp

    fake_root = tmp_path / "ahos"
    grok = fake_root / "reports" / "grok"
    (grok / "M13_SOAK").mkdir(parents=True)
    (grok / "M19").mkdir(parents=True)
    (grok / "M56").mkdir(parents=True)
    (grok / "M60").mkdir(parents=True)
    (grok / "M31").mkdir(parents=True)
    (grok / "M13_SOAK" / "soak_status.json").write_text(
        json.dumps({"status": "LIVE", "closed_trades": 2, "realized_pnl_usd": 1.25}),
        encoding="utf-8",
    )
    (grok / "M19" / "multi_market_snapshot.json").write_text(
        json.dumps({"desks_count": 7, "verified_instruments": 13}),
        encoding="utf-8",
    )
    (grok / "M56" / "tournament_snapshot.json").write_text(
        json.dumps({"leader_title": "Test", "leader_dsr": 1.1}),
        encoding="utf-8",
    )
    (grok / "M60" / "astra_snapshot.json").write_text(
        json.dumps({"overall_status": "SHADOW_PAPER_ACTIVE"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(exp, "ROOT", fake_root)
    assert exp.main() == 0
    snap = json.loads((grok / "M31" / "nightly_digest_snapshot.json").read_text(encoding="utf-8"))
    assert snap["schema"] == "ahos.nightly_digest.v1"
    assert snap["paper_only"] is True
    assert "خلاصهٔ اجرایی شبانه" in (grok / "M31" / "nightly_digest_fa.md").read_text(encoding="utf-8")


def test_comprehensive_nightly_digest_includes_golden_intel_sections() -> None:
    text = build_comprehensive_nightly_digest_fa(
        day="2026-10-23",
        trades=1,
        pnl_usd=0.5,
        macro_overlays={
            "gold_macro_bias": "BULLISH_TAILWIND",
            "oil_macro_bias": "BULLISH_TAILWIND",
            "macro_summary_fa": "خلاصهٔ کلان آزمایشی",
        },
        strategy_red_team={
            "survived_count": 2,
            "vetoed_count": 1,
            "top_survivor_verdict_fa": "تأیید تیم قرمز",
        },
        teaching_journal={
            "lessons_count": 4,
            "journal_entries_count": 3,
            "latest_lesson_title_fa": "درس آزمایشی",
            "latest_key_takeaway_fa": "نکتهٔ آزمایشی",
        },
    )
    assert "قطب‌نمای کلان" in text
    assert "تیم قرمز" in text
    assert "M65" in text


def test_comprehensive_nightly_digest_fa_uses_injected_snapshots() -> None:
    text = build_comprehensive_nightly_digest_fa(
        day="2026-10-23",
        trades=4,
        pnl_usd=1.5,
        gold_soak={"status": "SOAK_OK"},
        oil_soak={"status": "PAPER_IDLE"},
        multi_market={"desks_count": 7, "verified_instruments": 13},
        tournament={"leader_title": "Regime HMM", "leader_dsr": 1.42},
        astra={"overall_status": "SHADOW_PAPER_ACTIVE"},
    )
    assert "خلاصهٔ اجرایی شبانه" in text
    assert "M19" in text
    assert "M56" in text
    assert "M60" in text
    assert "live: false" in text


def test_comprehensive_nightly_digest_includes_aci_brain_and_organs() -> None:
    text = build_comprehensive_nightly_digest_fa(
        day="2026-10-23",
        trades=2,
        pnl_usd=0.0,
        aci_agi_si_brain={
            "current_stage_title_fa": "مرحلهٔ ۲ — ACI",
            "compounding_capability_index": 42.97,
            "loops": {
                "self_deciding": {},
                "self_fault_finding": {},
                "self_debugging": {},
                "self_updating": {},
            },
        },
        whole_ahos_organs={"organs_covered_count": 8, "average_university_exam_score_pct": 94.1, "trading_only": False},
    )
    assert "تکامل تدریجی مغز" in text
    assert "94.1" in text
    assert "8/8" in text


def test_comprehensive_nightly_digest_includes_four_brain_autonomous_coder() -> None:
    text = build_comprehensive_nightly_digest_fa(
        day="2026-10-24",
        trades=1,
        pnl_usd=0.0,
        autonomous_coder={
            "bridge_port_8787_status": "OFFLINE",
            "m70_6_safety_lock_status": "LOCKED_CLEAN",
            "four_brain_engine": {
                "brain_2_local_oss_tier": "8GB_SAFE_API_OFFLOAD",
                "brain_3_sandbox_verifier": "SANDBOX_SINGLE_FILE_PYTEST_PASS",
                "brain_4_memory_science_context": 2,
                "synthesized_patches_verified": 1,
                "persian_briefs_generated": 1,
            },
        },
    )
    assert "۴ مغز کدنویس" in text
    assert "M60.C" in text


def test_update_exam_skill_and_inbox():
    assert propose(expected_hash="a", actual_hash="b", cve=False, rollback="revert").accepted is False
    assert propose(expected_hash="a", actual_hash="a", cve=True, rollback="revert").lockfile_changed is False
    assert grade({"q": "yes"}, {"q": "yes"}, training_ids={"q"}).leaked is True
    clean = grade({"q": "yes"}, {"q": "yes"}, training_ids=set())
    assert clean.score == 1.0 and clean.promoted is False
    assert vet(spdx="", requested_install=False).accepted is False
    assert vet(spdx="Apache-2.0", requested_install=True).installed is False
    item = route_command("withdraw")
    assert item.state == "WAITING_FOR_OWNER" and item.executed is False


def test_allocation_arena_pilot_and_news():
    assert allocate({"gold": 0.4}).accepted is False
    assert allocate({"gold": 0.5, "oil": 0.5}).live_budget == 0.0
    assert rank({"a": 1.0, "b": 2.0}).promoted is False
    assert pilot_gate(owner_approved=True, paper_months=3, live_requested=True).live is False
    ready = pilot_gate(owner_approved=True, paper_months=3, live_requested=False)
    assert ready.review is True and ready.live is False
    assert corroborate([("a", "up")]).state == "UNKNOWN"
    assert corroborate([("a", "up"), ("b", "down")]).state == "CONFLICT"
    assert corroborate([("a", "up"), ("b", "up")]).claim == "up"
    assert advise(votes_to_promote=3, votes=3, tier="T0").promoted is False


def test_lab_quarantine_scan_and_ops():
    assert lab_status(low_priv_configured=True).spawned is False
    assert plan(["slills", "slills"]).deleted == 0
    with pytest.raises(PermissionError):
        delete_paths(["slills"])
    assert scan("sk-supersecret").level == "HALT"
    assert scan("plain").findings == 0
    assert ops_command("push") == "REFUSED"
    assert ops_command("local_status") == "ALLOWED"
    assert safety_lock(paper_only=False) == "HALT"
    assert task("exploit") == "REFUSED"


def test_learning_loops_and_tokens():
    reg = register([
        ("https://a.example", ""),
        ("https://a.example", "MIT"),
        ("https://b.example", "Apache-2.0"),
    ])
    assert reg.fetched == 0
    assert reg.dropped == 1
    assert reg.kept == ("https://a.example", "https://b.example")
    assert from_loss(case_id="c", pnl_usd=-2).threshold_changed is False
    _hist, changed = record([], "bench", 0.5)
    assert changed is False and isinstance(_hist[0], BenchPoint)
    assert transfer(source="gold", target="oil", changes_gate=True).gate_changed is False
    assert consider(source="dextools", security="PASS").state == "REFUSED_SOURCE"
    assert consider(source="dexscreener", security="UNKNOWN").trades is False
    assert consider(source="goplus", security="PASS").state == "PAPER_WATCH"
    assert register_team(authority="TRADE", auto_create=False).accepted is False
    assert register_team(authority="NONE", auto_create=False).accepted is True
    assert evaluate(trades=2, trials=4).dsr is None
    assert evaluate(trades=40, trials=2).promoted is False


def test_testnet_and_withdrawal_do_not_send():
    denied = submit_testnet(_req("mainnet"), seen_ids=set(), spent_ahos_usd=0, spent_broker_usd=0)
    assert denied.accepted is False and denied.executes is False
    ok = submit_testnet(_req("testnet"), seen_ids=set(), spent_ahos_usd=0, spent_broker_usd=0)
    assert ok.accepted is True and ok.executes is False
    absent = request_withdrawal(_req(), owner_present=False, seen_ids=set(), spent_ahos_usd=0, spent_broker_usd=0)
    assert absent.reason == "owner absent"
    present = request_withdrawal(_req(), owner_present=True, seen_ids=set(), spent_ahos_usd=0, spent_broker_usd=0)
    assert present.accepted is True and present.executes is False
