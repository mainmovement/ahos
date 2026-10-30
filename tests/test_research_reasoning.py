from architecture.markets.paper_trade_gates import MIN_AGREEING_FAMILIES, MIN_EXPECTED_PROFIT_TO_FEE_RATIO
from architecture.university.latent_dynamics_shadow import evaluate
from architecture.university.research_reasoning import ask, debate_setup, self_repair, strategy_search


def _close(i, name="candles", side="LONG", pnl=0.2):
    return {
        "desk": "CRYPTO",
        "side": side,
        "notional_usd": 10.0,
        "realized_pnl_usd": pnl,
        "closed_at": f"2026-10-{i:02d}T00:00:00Z",
        "reason": "STOP",
        "entry_brain": {"signals": [{"name": name, "score": 0.4 if side == "LONG" else -0.4, "available": True, "evidence": {}}]},
    }


def test_the_latent_path_is_scored_and_does_not_write_a_weight():
    closes = [_close(i) for i in range(1, 21)]
    doc = evaluate(closes)
    assert doc["n_steps"] > 0
    assert doc["applied_to_live_weights"] is False
    assert doc["upstream_executed"] is False
    assert doc["predicted_score"]["CRYPTO"] is not None


def test_the_debate_weight_stays_zero_without_calling_gemini():
    doc = debate_setup({"agreeing_families": ["candle_wicks"], "weight": 0}, gemini=None)
    assert doc["advisory_vote"]["weight"] == 0.0
    assert doc["advisory_vote"]["decides"] is False
    assert doc["gemini_status"] == "NOT_CALLED"
    assert doc["hardware"]["ram_gb"] is not None
    assert doc["hardware"]["tier"] in {"T8", "T16", "T32", "GPU"}
    failed = debate_setup({"weight": 0}, gemini=lambda _req: (_ for _ in ()).throw(RuntimeError("down")))
    assert failed["gemini_status"] == "ERROR"
    assert failed["advisory_vote"]["weight"] == 0.0
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0


def test_the_family_grid_is_archived_when_the_sample_is_short():
    doc = strategy_search([_close(i) for i in range(1, 4)])
    assert doc["decision"] == "ARCHIVE"
    assert doc["reason"] == "INSUFFICIENT_REPLAY"
    assert doc["applied_to_live_weights"] is False


def test_a_repair_is_not_applied_without_the_red_team_and_an_unknown_question_stays_unknown():
    repair = self_repair(["feed stale"], tests_passed=True, red_team=None)
    assert repair["applied"] is False
    passed = self_repair(["feed stale"], tests_passed=True, red_team="SURVIVED_RED_TEAM")
    assert passed["applied"] is True
    answer = ask([{"citation": "paper_close:CRYPTO:2026-10-01", "text": "CRYPTO NEWS_TRAP STOP"}], "why news trap")
    assert answer["status"] == "CITED"
    assert answer["citations"]
    missing = ask([{"citation": "x", "text": "gold"}], "why funding")
    assert missing["status"] == "UNKNOWN"
    assert missing["answer"] == "UNKNOWN"
