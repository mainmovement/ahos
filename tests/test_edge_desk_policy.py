from __future__ import annotations

import json
from pathlib import Path

from architecture.markets.edge_desk_policy import (
    build_desk_policy_from_edge_report,
    desk_entry_blocked_by_shadow_policy,
    export_desk_policy,
    load_desk_policy,
    notional_mult_from_desk_row,
)
from architecture.markets.paper_trade_gates import DESK_NOTIONAL_MULT, effective_desk_notional_mult


def test_notional_mult_shrinks_losing_desk():
    assert notional_mult_from_desk_row({"closes": 5, "realized_pnl_usd": -0.5}) < 1.0
    assert notional_mult_from_desk_row({"closes": 2, "realized_pnl_usd": -1.0}) == 1.0
    assert notional_mult_from_desk_row({"closes": 10, "realized_pnl_usd": 0.2}) == 1.0


def test_cent_scale_loss_uses_sample_size_not_a_two_dollar_cliff():
    mult = notional_mult_from_desk_row({"closes": 30, "realized_pnl_usd": -0.01})
    assert 0.15 <= mult < 0.40


def test_closed_book_equations_stay_unpromoted():
    from architecture.learning.walk_forward import closed_book_equations

    doc = closed_book_equations([-0.02, -0.01, 0.005] * 10)
    assert doc["promoted"] is False
    assert doc["applied_to_live_weights"] is False
    assert doc["mean_test"]["t"] < 0
    assert doc["deflated_sharpe"] is not None


def test_t_stat_shrinks_more_when_the_loss_is_tight():
    weak = notional_mult_from_desk_row({"closes": 30, "realized_pnl_usd": -0.30, "stdev_usd": 5.0})
    strong = notional_mult_from_desk_row({"closes": 30, "realized_pnl_usd": -0.30, "stdev_usd": 0.05})
    assert strong < weak
    assert weak > 0.5


def test_effective_mult_merges_edge_with_static(tmp_path: Path):
    edge = {
        "generated_at": "2026-10-29T00:00:00Z",
        "edge_status": "UNPROVEN_EDGE",
        "desks": [{"desk": "US_EQUITIES", "closes": 10, "realized_pnl_usd": -0.5}],
        "desks_recommend_shrink": [{"desk": "US_EQUITIES", "closes": 10, "realized_pnl_usd": -0.5}],
    }
    export_desk_policy(tmp_path, edge)
    m, src = effective_desk_notional_mult(tmp_path, "US_EQUITIES")
    assert src == "edge_merged"
    assert m < DESK_NOTIONAL_MULT["US_EQUITIES"]
    assert load_desk_policy(tmp_path)["schema"] == "ahos.desk_policy.v1"


def test_build_policy_marks_shadow_advisory(tmp_path: Path):
    edge = build_desk_policy_from_edge_report(
        {
            "generated_at": "2026-10-29T00:00:00Z",
            "edge_status": "UNPROVEN_EDGE",
            "desks": [{"desk": "GOLD", "closes": 4, "realized_pnl_usd": -0.35}],
            "desks_recommend_shrink": [{"desk": "GOLD", "closes": 4, "realized_pnl_usd": -0.35}],
        }
    )
    gold = next(d for d in edge["desks"] if d["desk"] == "GOLD")
    assert gold["shadow_only_advisory"] is True
    path = tmp_path / "reports/grok/PAPER/desk_policy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(edge), encoding="utf-8")
def test_shadow_block_off_by_default(tmp_path: Path):
    export_desk_policy(
        tmp_path,
        {
            "generated_at": "2026-10-29T00:00:00Z",
            "edge_status": "UNPROVEN_EDGE",
            "desks": [{"desk": "CRYPTO", "closes": 5, "realized_pnl_usd": -1.0}],
            "desks_recommend_shrink": [{"desk": "CRYPTO", "closes": 5, "realized_pnl_usd": -1.0}],
        },
    )
    blocked, reason = desk_entry_blocked_by_shadow_policy(tmp_path, "CRYPTO")
    assert not blocked and reason is None


def test_shadow_block_when_env_set(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("AHOS_PAPER_DESK_SHADOW_BLOCK", "1")
    export_desk_policy(
        tmp_path,
        {
            "generated_at": "2026-10-29T00:00:00Z",
            "edge_status": "UNPROVEN_EDGE",
            "desks": [{"desk": "CRYPTO", "closes": 5, "realized_pnl_usd": -1.0}],
            "desks_recommend_shrink": [{"desk": "CRYPTO", "closes": 5, "realized_pnl_usd": -1.0}],
        },
    )
    blocked, reason = desk_entry_blocked_by_shadow_policy(tmp_path, "CRYPTO")
    assert blocked and reason == "DESK_EDGE_SHADOW_BLOCK"
