import json

from architecture.markets.paper_trade_gates import MIN_AGREEING_FAMILIES, MIN_EXPECTED_PROFIT_TO_FEE_RATIO
from architecture.university.behaviour_learning import (
    calibration_weekly,
    intelligence_metric,
    reliability_shadow,
    weekly_exam,
)
from architecture.university.learning_loop import university_case
from architecture.university.mistake_memory import review_open


def _loss(desk="CRYPTO", side="LONG", name="candles", cause_pnl=-1.0, fees=0.01, reason="STOP", when="2026-10-01T00:00:00Z", composite=0.4):
    return {
        "symbol": "BTC",
        "desk": desk,
        "side": side,
        "realized_pnl_usd": cause_pnl,
        "fees_usd": fees,
        "reason": reason,
        "closed_at": when,
        "kian_explain_fa": "توضیح",
        "entry_brain": {
            "composite": composite,
            "signals": [{"name": name, "score": 0.4, "available": True, "evidence": {}}],
        },
    }


def test_the_exam_scores_only_the_field_each_agent_may_use():
    closes = [_loss(when=f"2026-10-{day:02d}T00:00:00Z") for day in range(1, 4)]
    doc = weekly_exam(closes)
    scores = {row["agent_id"]: row for row in doc["scores"]}
    assert scores["AG-04"]["accuracy"] == 1.0
    assert scores["AG-33"]["correct"] == 0
    assert scores["AG-18"]["n"] == 3
    assert doc["applied_to_live_weights"] is False
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0


def test_a_decayed_hit_rate_stays_shadow_without_dsr():
    closes = [_loss(cause_pnl=1.0, when=f"2026-10-01T00:{i:02d}:00Z") for i in range(30)]
    doc = reliability_shadow(closes)
    row = doc["rows"][0]
    assert row["n"] == 30
    assert row["status"] == "SHADOW"
    assert row["dsr"] is None
    assert row["applied_to_live_weights"] is False
    assert doc["decides"] is False


def test_recalibration_is_not_applied_to_the_entry():
    closes = [_loss(composite=0.9, cause_pnl=-1.0, when=f"2026-10-{i:02d}T00:00:00Z") for i in range(1, 13)]
    doc = calibration_weekly(closes)
    cell = doc["by_desk"]["CRYPTO"]
    assert cell["brier"] is not None
    assert cell["applied_to_entry"] is False
    assert cell["reliability"][0]["n"] == 0 or cell["reliability"][-1]["n"] == 12


def test_a_repeated_news_trap_vetoes_and_two_do_not(tmp_path):
    path = tmp_path / "reports" / "grok" / "PAPER"
    path.mkdir(parents=True)
    cases = []
    for i in range(2):
        cases.append(university_case(_loss(name="news", when=f"2026-10-0{i+1}T00:00:00Z")))
    (path / "university_cases.jsonl").write_text("".join(json.dumps(row) + "\n" for row in cases), encoding="utf-8")
    quiet = review_open(tmp_path, "CRYPTO", "LONG", ["news"])
    assert quiet["action"] == "NONE"
    cases.append(university_case(_loss(name="news", when="2026-10-03T00:00:00Z")))
    (path / "university_cases.jsonl").write_text("".join(json.dumps(row) + "\n" for row in cases), encoding="utf-8")
    veto = review_open(tmp_path, "CRYPTO", "LONG", ["news"])
    assert veto["action"] == "VETO" and veto["cause"] == "NEWS_TRAP"
    assert veto["applied_to_live_weights"] is False
    shrink_cases = [university_case(_loss(when=f"2026-10-0{i}T00:00:00Z")) for i in range(1, 4)]
    (path / "university_cases.jsonl").write_text("".join(json.dumps(row) + "\n" for row in shrink_cases), encoding="utf-8")
    shrink = review_open(tmp_path, "CRYPTO", "LONG", ["candle_wicks"])
    assert shrink["action"] == "SHRINK" and shrink["factor"] == 0.5


def test_a_weaker_week_is_reported_instead_of_called_an_improvement():
    first = [_loss(cause_pnl=1.0, when=f"2026-10-{day:02d}T00:00:00Z") for day in range(5, 10)]
    second = [_loss(cause_pnl=-1.0, when=f"2026-10-{day:02d}T00:00:00Z") for day in range(12, 17)]
    doc = intelligence_metric(first + second)
    assert doc["status"] == "TREND_NOT_UP"
    assert any(reason.startswith("win_rate") for reason in doc["reasons"])
    assert doc["applied_to_live_weights"] is False
