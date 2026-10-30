import json
from datetime import datetime, timezone

from architecture.markets.family_vote_scorecard import (
    build_weekly_family_scorecard,
    record_family_votes,
)
from architecture.markets.paper_trade_gates import (
    MIN_AGREEING_FAMILIES,
    MIN_EXPECTED_PROFIT_TO_FEE_RATIO,
)
from architecture.markets import signal_brain as sb


def _sig(name, score, available=True, evidence=None):
    return {"name": name, "score": score, "available": available, "evidence": evidence or {}}


def test_scorecard_is_counterfactual_and_does_not_change_weights(tmp_path):
    weights = tmp_path / "reports" / "grok" / "PAPER" / "signal_weights.json"
    weights.parent.mkdir(parents=True)
    weights.write_text('{"weights":{"news":0.09}}', encoding="utf-8")
    sigs = [_sig("news", 0.4), _sig("candles", -0.3), _sig("macro", 0.0)]
    record_family_votes(tmp_path, ts="2026-10-26T00:00:00Z", symbol="BTC", desk="CRYPTO", price=100.0, sigs=sigs)
    record_family_votes(tmp_path, ts="2026-10-26T04:10:00Z", symbol="BTC", desk="CRYPTO", price=110.0, sigs=sigs)
    record_family_votes(tmp_path, ts="2026-10-26T08:20:00Z", symbol="BTC", desk="CRYPTO", price=100.0, sigs=sigs)
    # A second print inside the 4h window must not become a second trial.
    record_family_votes(tmp_path, ts="2026-10-26T01:00:00Z", symbol="BTC", desk="CRYPTO", price=101.0, sigs=sigs)
    now = datetime(2026, 10, 28, tzinfo=timezone.utc)
    doc = build_weekly_family_scorecard(tmp_path, now=now)
    assert doc["counterfactual"] is True
    assert doc["composite_weight"] == 0.0
    assert doc["week"] == "2026-W44"
    news = doc["families"]["news"]["4h"]
    wicks = doc["families"]["candle_wicks"]["4h"]
    assert news["hits"] == 1
    assert news["misses"] == 1
    assert news["hit_rate"] == 0.5
    assert wicks["hits"] == 1
    assert wicks["misses"] == 1
    assert doc["families"]["macro_central_bank"]["4h"]["hits"] == 0
    assert doc["families"]["macro_central_bank"]["4h"]["hit_rate"] is None
    assert json.loads(weights.read_text(encoding="utf-8"))["weights"]["news"] == 0.09
    assert sb.DEFAULT_WEIGHTS["cftc_cot"] == 0.0
    assert MIN_AGREEING_FAMILIES == 2
    assert MIN_EXPECTED_PROFIT_TO_FEE_RATIO == 2.0


def test_pending_and_late_prints_are_not_hits(tmp_path):
    sigs = [_sig("news", 0.2)]
    record_family_votes(tmp_path, ts="2026-10-28T00:00:00Z", symbol="ETH", desk="CRYPTO", price=10.0, sigs=sigs)
    record_family_votes(tmp_path, ts="2026-10-26T00:00:00Z", symbol="ETH", desk="CRYPTO", price=10.0, sigs=sigs)
    record_family_votes(tmp_path, ts="2026-10-26T12:00:00Z", symbol="ETH", desk="CRYPTO", price=12.0, sigs=sigs)
    now = datetime(2026, 10, 28, 2, tzinfo=timezone.utc)
    doc = build_weekly_family_scorecard(tmp_path, now=now)
    cell = doc["families"]["news"]
    assert cell["4h"]["pending"] == 1
    assert cell["4h"]["no_print_in_window"] == 2
    assert cell["4h"]["hits"] == 0
    assert cell["24h"]["pending"] == 1
    assert cell["24h"]["no_print_in_window"] == 1


def test_research_advisory_sign_is_scored_at_weight_zero(tmp_path):
    research = _sig("research_overlay", 0.0, available=False, evidence={"advisory_vote_score": -0.3, "composite_weight": 0.0})
    record_family_votes(tmp_path, ts="2026-10-26T00:00:00Z", symbol="BRENT", desk="OIL", price=80.0, sigs=[research])
    record_family_votes(tmp_path, ts="2026-10-26T04:10:00Z", symbol="BRENT", desk="OIL", price=70.0, sigs=[research])
    doc = build_weekly_family_scorecard(tmp_path, now=datetime(2026, 10, 27, tzinfo=timezone.utc))
    cell = doc["families"]["research"]["4h"]
    assert cell["hits"] == 1
    assert cell["hit_rate"] == 1.0
    assert doc["composite_weight"] == 0.0
