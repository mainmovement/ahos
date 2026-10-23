"""Tests for the 4 Golden Ideas:
1. M65 Persian Teaching Mode & Hooman Decision Journal
2. Free Macro & Positioning Intelligence Overlay (DXY, DFII10, CFTC COT, EIA)
3. Strategy Red Team & 2x/3x Cost Stress Tester
4. M-PORT One-Click Portable Hardware Auto-Tier & Migration Pack
"""
from __future__ import annotations

from architecture.learning.strategy_red_team import (
    ATTACK_VECTORS_5,
    evaluate_strategy_red_team,
    run_strategy_red_team_suite,
)
from architecture.learning.teaching_mode_m65 import (
    PERSIAN_QUANT_GLOSSARY,
    build_teaching_lesson_from_cycle,
    generate_teaching_journal_snapshot,
)
from architecture.markets.macro_overlays import evaluate_macro_overlays
from scripts.export_portable_migration_pack import (
    build_portable_migration_pack,
    select_auto_tier,
)


def test_m65_teaching_mode_and_hooman_journal() -> None:
    snap = generate_teaching_journal_snapshot()
    assert snap["paper_only"] is True
    assert snap["real_trading"] is False
    assert snap["lessons_count"] >= 4
    assert snap["journal_entries_count"] >= 3
    assert "ATR" in PERSIAN_QUANT_GLOSSARY
    assert "Two-Source Witness" in PERSIAN_QUANT_GLOSSARY

    unresolved_lesson = build_teaching_lesson_from_cycle(
        {"market": "GOLD", "symbol": "XAUUSD", "witness_state": "UNRESOLVED", "pnl_usd": 0.0}
    )
    assert "UNKNOWN != SAFE" in unresolved_lesson.key_takeaway_fa


def test_macro_overlays_corroboration_and_conflict_hold() -> None:
    snap = evaluate_macro_overlays()
    assert snap["paper_only"] is True
    assert snap["gold_macro_bias"] == "BULLISH_TAILWIND"
    assert snap["oil_macro_bias"] == "BULLISH_TAILWIND"
    assert snap["factors_count"] == 4
    assert "DXY" in snap["macro_summary_fa"]

    # Single-source factor must trigger CONFLICT_HOLD
    unverified = evaluate_macro_overlays(
        {
            "dxy_index": 104.0,
            "dxy_change_z": -0.5,
            "dxy_sources": ("only_one_source",),
            "real_yield_10y_pct": 1.8,
            "real_yield_change_z": -0.4,
            "real_yield_sources": ("fred_dfii10", "treasury_gov_tips"),
            "cot_gold_net_percentile": 65.0,
            "cot_oil_net_percentile": 55.0,
            "cot_sources": ("cftc_a", "cftc_b"),
            "eia_crude_surprise_mbbl": -2.0,
            "eia_sources": ("eia_a", "fred_b"),
        }
    )
    assert unverified["gold_macro_bias"] == "CONFLICT_HOLD"
    assert unverified["oil_macro_bias"] == "CONFLICT_HOLD"


def test_strategy_red_team_5_attack_vectors() -> None:
    assert len(ATTACK_VECTORS_5) == 5
    suite = run_strategy_red_team_suite()
    assert suite["paper_only"] is True
    assert suite["auto_promote"] is False
    assert suite["survived_count"] == 2
    assert suite["vetoed_count"] == 1
    assert suite["top_survivor_id"] == "strat-regime-hmm-v2"

    # Lookahead leak immediately vetoes strategy
    leaked = evaluate_strategy_red_team(
        {
            "strategy_id": "strat-leaky",
            "title": "Leaky Strategy",
            "returns": [0.005] * 12,
            "cost_bps": 2.0,
            "lookahead_leak_detected": True,
        }
    )
    assert leaked.verdict == "VETOED_FRAGILE"


def test_run_all_lightweight_exporters_manifest() -> None:
    import json
    from pathlib import Path

    from scripts.run_all_lightweight_exporters import MANIFEST_REL, run_all_exports

    manifest = run_all_exports()
    assert manifest["paper_only"] is True
    assert manifest["real_trading"] is False
    assert manifest["steps_count"] >= 17
    assert manifest["files_count"] >= 22
    path = Path(__file__).resolve().parents[1] / MANIFEST_REL
    assert path.is_file()
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["execution_mode"] == "PAPER_ONLY"
    assert any(e.get("exists") for e in on_disk["exports"])


def test_mport_auto_tier_and_migration_pack() -> None:
    t8 = select_auto_tier(8.0, 8)
    assert t8["auto_tier"] == "TIER_8GB_SAFE"
    assert t8["allow_local_next_build"] is False

    t16 = select_auto_tier(16.0, 8)
    assert t16["auto_tier"] == "TIER_16GB_BALANCED"

    t32 = select_auto_tier(32.0, 16)
    assert t32["auto_tier"] == "TIER_32GB_ULTRA"
    assert t32["heavy_features_allowed"] is True

    pack = build_portable_migration_pack()
    assert pack["paper_only"] is True
    assert pack["portable_ready"] is True
    assert pack["safety_verification"]["m70_6_safety_lock"] == "LOCKED_CLEAN"
