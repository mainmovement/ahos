"""Stage 4 comprehensive closure tests covering all newly upgraded REAL modules."""
from __future__ import annotations

from pathlib import Path

from architecture.ai.grammar_adapter import query_grammar_structured
from architecture.health.self_debug import run_self_debug_worktree_cycle
from architecture.learning.exam import run_heldout_5domain_exam
from architecture.learning.memory_consolidation import run_pit_10k_benchmark
from architecture.learning.teaching_mode_m65 import generate_teaching_journal_snapshot
from architecture.markets import paper_trader as pt
from architecture.markets import signal_brain as sb
from architecture.markets.council_gate import soroush_blind_debate_and_bl
from architecture.markets.crisis import run_m29_crisis_suite
from architecture.markets.oms import CCXTPaperAdapter, IBKRPaperAdapter
from architecture.markets.rotation_m24 import run_m24_rotation_scenarios
from architecture.markets.token_safety_live import veto_check
from architecture.mission.controller import run_rca_gate_promote_cycle
from architecture.security.skill_vet import vet_skill_s1_to_s12
from architecture.university.registry import ask_university, estimate_ability_theta, irt_2pl_prob


def test_m13_6_and_ts4_token_safety_fail_closed() -> None:
    # Single source must be VETOED_FAIL_CLOSED
    single = veto_check(
        "UNI",
        "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984",
        getter=lambda u: {"result": {"0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": {"is_honeypot": "0", "buy_tax": "0", "sell_tax": "0", "is_open_source": "1", "is_mintable": "0"}}} if "goplus" in u else None,
    )
    assert single["allowed"] is False
    assert single["verdict"] == "VETOED_FAIL_CLOSED"

    # Two agreeing clean security sources + liquidity >= $100k passes
    def mock_good(url: str):
        if "goplus" in url:
            return {"result": {"0x1f9840a85d5af5bf1d1762f925bdaddc4201f984": {"is_honeypot": "0", "buy_tax": "0.0", "sell_tax": "0.0", "is_open_source": "1", "is_mintable": "0", "holder_count": "10000"}}}
        if "honeypot.is" in url:
            return {"simulationSuccess": True, "honeypotResult": {"isHoneypot": False}, "simulationResult": {"buyTax": 0.0, "sellTax": 0.0}, "contractCode": {"openSource": True}}
        if "dexscreener" in url:
            return {"pairs": [{"liquidity": {"usd": 500000.0}, "volume": {"h24": 1200000.0}, "priceUsd": "6.97"}]}
        return None

    clean = veto_check("UNI", "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984", getter=mock_good)
    assert clean["allowed"] is True
    assert clean["verdict"] == "ELIGIBLE_PAPER_TOKEN"
    assert clean["sources_verified"] == 3


def test_ts1_hmm_pelt_and_ts5_garch11_and_ts3_adv_cap() -> None:
    bars = [[100.0 + i * 0.1, 100.2 + i * 0.1, 99.8 + i * 0.1, 100.1 + i * 0.1, 1000.0] for i in range(120)]
    reg = sb.vol_regime(bars)
    assert reg["hmm_state"] in ("LOW", "NORMAL", "HIGH")
    assert reg["garch11_vol"] is not None and reg["ewma_vol"] is not None
    assert "filtered_HMM+PELT+GARCH11" in reg["spec"]

    adv = sb.adv_cap_check(25.0, {"price": 100.0, "vol_24h": 5_000_000.0}, bars)
    assert adv["allowed"] is True
    assert adv["cap_1pct_usd"] == 50_000.0
    adv_breach = sb.adv_cap_check(100_000.0, {"price": 100.0, "vol_24h": 5_000_000.0}, bars)
    assert adv_breach["allowed"] is False


def test_m24_rotation_and_m21_mc_ruin(tmp_path: Path) -> None:
    rot = run_m24_rotation_scenarios(tmp_path)
    by_id = {s["scenario_id"]: s for s in rot["scenarios"]}
    assert by_id["day4_eu_equity"]["rotated"] is True
    assert by_id["eu_equity_to_gold"]["rotated"] is True
    assert by_id["anti_churn_blocked"]["rotated"] is False

    mc = pt.mc_risk_of_ruin([], 100.0, paths=500)
    assert mc["paths"] == 500
    assert 0.0 <= mc["ruin_probability"] <= 1.0


def test_m15_soroush_blind_swap_and_black_litterman() -> None:
    res = soroush_blind_debate_and_bl(
        symbol="BTC",
        bull_prob=0.68,
        bear_prob=0.35,
        bull_evidence_refs=["mtf_trend:yahoo", "order_flow:okx"],
        bear_evidence_refs=["macro:dxy"],
        devils_advocate_dissent="Macro tightening could reverse intraday crypto bounce",
    )
    assert res["approved_paper"] is True
    assert res["swap_consistency"] >= 0.90
    assert res["brier_judge"] <= res["brier_best_analyst"]
    assert res["ece_judge"] <= 0.08


def test_m20_ccxt_and_ibkr_paper_adapters() -> None:
    ccxt_ad = CCXTPaperAdapter("okx_paper", sandbox=True, allow_withdraw=False)
    ok_c = ccxt_ad.submit_order(symbol="BTCUSDT", side="buy", notional_usd=15.0)
    assert ok_c.oms_state == "ACCEPTED_PAPER" and ok_c.live is False
    bad_c = ccxt_ad.submit_order(symbol="BTCUSDT", side="buy", notional_usd=15.0, live=True)
    assert bad_c.oms_state == "REJECTED_LIVE_FORBIDDEN"

    ibkr_ad = IBKRPaperAdapter("DU123456", sandbox=True)
    ok_i = ibkr_ad.submit_order(symbol="SPY", side="buy", notional_usd=15.0)
    assert ok_i.oms_state == "ACCEPTED_PAPER"
    bad_i = IBKRPaperAdapter("U999999_LIVE", sandbox=True).submit_order(symbol="SPY", side="buy", notional_usd=15.0)
    assert bad_i.oms_state == "REJECTED_LIVE_FORBIDDEN"


def test_m14_m46_m70_5_self_debug_worktree(tmp_path: Path) -> None:
    m14 = run_rca_gate_promote_cycle(
        proposal_id="p1",
        fault_summary="timeout",
        evidence_refs=["ev1"],
        gate_passed=True,
        root=tmp_path,
    )
    assert m14["promoted"] is False and m14["state"] == "AWAITING_OWNER_SIGNATURE"

    m46 = run_self_debug_worktree_cycle(
        error="err with sk-1234567890abcdef",
        evidence_refs=["ev1"],
        candidates=[
            {"id": "c_bad", "target_branch": "debug/bad", "target_paths": ["HOLD.flag"], "patched_code": "x=1", "test_code": "def test_a(): assert True"},
            {"id": "c_ok", "target_branch": "debug/ok", "target_paths": ["calc.py"], "patched_code": "def f(x): return x + 1\n", "test_code": "from module_under_test import f\ndef test_f(): assert f(2) == 3\n"},
        ],
        root=tmp_path,
    )
    assert "[REDACTED]" in m46["redacted_error"]
    assert m46["winner_candidate_id"] == "c_ok"
    assert m46["applied_to_main"] is False and m46["pushed"] is False


def test_m16_irt_asku_and_m50_heldout_exam(tmp_path: Path) -> None:
    assert 0.49 < irt_2pl_prob(0.0, 1.2, 0.0) < 0.51
    ab = estimate_ability_theta([{"a": 1.4, "b": -0.5, "correct": True}, {"a": 1.5, "b": 0.0, "correct": True}, {"a": 1.2, "b": 0.5, "correct": False}])
    assert -3.0 <= ab["theta"] <= 3.0

    asku = ask_university("two source witness deflated sharpe", root=tmp_path)
    assert asku["asku_ref"].startswith("asku_")
    assert asku["ranked_claims_count"] >= 10

    ex = run_heldout_5domain_exam(root=tmp_path)
    assert ex["domains_count"] == 5 and ex["leaked"] is False and ex["promoted"] is False
    assert ex["tag"] == "[OBSERVED]" and ex["overall_score"] == 1.0


def test_m29_crisis_m30_pit_10k_m52_s12_and_m70_2(tmp_path: Path) -> None:
    c29 = run_m29_crisis_suite(tmp_path)
    assert c29["crises_tested"] == 10 and c29["blocked_count"] == 10 and c29["under_60s_sla"] is True

    m30 = run_pit_10k_benchmark(root=tmp_path, n_items=10_000, n_queries=200)
    assert m30["items_indexed"] == 10_000
    assert m30["future_leakage_count"] == 0 and m30["zero_leakage_verified"] is True
    assert m30["recall_at_10"] >= 0.80

    s52 = vet_skill_s1_to_s12("def run_skill(xs):\n    return sum(xs)\n", spdx="MIT", root=tmp_path)
    assert s52["accepted_to_shelf"] is True and s52["checks_passed"] == 12
    assert s52["installed"] is False and s52["merged"] is False

    bad52 = vet_skill_s1_to_s12("import urllib.request\ndef run_skill(xs): return 0\n", spdx="MIT")
    assert bad52["accepted_to_shelf"] is False and bad52["checks"]["S-4_zero_network_egress"] is False

    g70 = query_grammar_structured("test", {"summary_fa": str, "paper_only": bool})
    assert g70["grammar_valid"] is True and g70["output"]["paper_only"] is True

    m65 = generate_teaching_journal_snapshot(root=tmp_path)
    assert m65["paper_only"] is True and m65["lessons_count"] >= 4
