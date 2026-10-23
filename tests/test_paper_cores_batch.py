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
