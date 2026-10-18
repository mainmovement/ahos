"""Replay-labelled gate supplements."""
from architecture.markets.gate_inputs import LABEL, tier_gate_kwargs
from architecture.markets.tier_gate import evaluate_tier_gate


def test_replay_inputs_make_cost_and_walk_forward_measurable():
    kw = tier_gate_kwargs()
    assert LABEL in kw["declared_cost_model"]
    report = evaluate_tier_gate(market="gold", trades=[], months_of_data=0.1, **kw)
    unmeasurable = set(report.unmeasurable)
    assert "cost_model" not in unmeasurable
    assert "walk_forward" not in unmeasurable
    assert report.promoted is False
