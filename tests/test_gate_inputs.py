"""Replay-labelled gate supplements."""
from architecture.markets.gate_inputs import LABEL, tier_gate_kwargs
from architecture.markets.tier_gate import evaluate_tier_gate


def test_replay_inputs_make_cost_and_walk_forward_measurable():
    kw = tier_gate_kwargs(market="gold")
    assert LABEL in kw["declared_cost_model"]
    assert "2x slippage" in kw["declared_cost_model"]
    report = evaluate_tier_gate(market="gold", trades=[], months_of_data=0.1, **kw)
    unmeasurable = set(report.unmeasurable)
    assert "cost_model" not in unmeasurable
    assert "walk_forward" not in unmeasurable
    assert report.promoted is False


def test_oil_replay_block_is_measurable_on_cost_and_wf():
    kw = tier_gate_kwargs(market="oil")
    assert "oil" in kw["declared_cost_model"] or "CL=F" in kw["declared_cost_model"]
    report = evaluate_tier_gate(market="oil", trades=[], months_of_data=0.01, **kw)
    unmeasurable = set(report.unmeasurable)
    assert "cost_model" not in unmeasurable
    assert "walk_forward" not in unmeasurable
