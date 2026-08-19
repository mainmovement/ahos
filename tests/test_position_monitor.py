#!/usr/bin/env python3
"""The other half of the loop: reviewing positions already held.

`evaluate_position` and `advise_position` both existed and both worked, and
neither was called by anything outside the test suite. The pipeline announced
tokens and then went quiet, so "when do I sell?" had no answer that arrived on
its own -- and THESIS_STRENGTHENING / THESIS_INVALIDATED, registered as
decisional in the Telegram router, were emitted nowhere.
"""
import importlib
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

NOW = 1_760_000_000.0


@pytest.fixture()
def manager(monkeypatch, tmp_path):
    """A real manager on a throwaway DB -- the paper ledger is append-only."""
    monkeypatch.setenv("AHOS_DATA_DIR", str(tmp_path))
    import config.paths
    importlib.reload(config.paths)
    import architecture.positions.manager as mod
    importlib.reload(mod)
    return mod.PaperPositionManager()


def _position(manager, symbol="HELD", entry=1.0, age_h=1.0, address=None):
    # position_id hashes chain:address:allocation:ts, so two positions opened
    # at the same instant with the same address collide on the primary key.
    return manager.open_position(
        chain="solana", token_address=address or (symbol[:1] * 44), symbol=symbol,
        entry_price_usd=entry, allocated_usd=20.0, strategy_id="S1",
        now=NOW - age_h * 3600.0,
    )


def _monitor(manager, market):
    from architecture.positions.monitor import PositionMonitor
    from architecture.decision.advisor import DecisionAdvisor
    lookup = market if callable(market) else (lambda chain, addr: market)
    return PositionMonitor(manager, DecisionAdvisor(), lookup)


def _review(manager, market):
    return _monitor(manager, market).review_all(now=NOW)[0]


# ------------------------------------------------- the book can be listed --

def test_open_positions_can_be_listed_at_all(manager):
    """There was no way to ask "what am I holding?".

    `evaluate_position` took one id, so a caller had to already know every id
    in the book -- which is why nothing ever reviewed it.
    """
    assert manager.open_positions() == []
    _position(manager, symbol="ONE")
    _position(manager, symbol="TWO")
    assert {p.symbol for p in manager.open_positions()} == {"ONE", "TWO"}


def test_closed_positions_are_not_reviewed(manager):
    pos = _position(manager)
    manager.evaluate_position(pos.position_id, current_price_usd=1.60,
                              last_obs_ts=NOW, now=NOW)          # take profit
    assert all(p.position_id != pos.position_id
               for p in manager.open_positions())


# ------------------------------------------------------- the exit decision --

def test_a_stop_loss_reaches_the_user(manager):
    _position(manager)
    review = _review(manager, {"price_usd": 0.60, "liquidity_usd": 250_000.0})
    assert review.action == "EXIT"
    assert review.urgency == "IMMEDIATE"
    assert review.alerts and review.alerts[0].cls == "RISK_INCREASING"


def test_reaching_the_target_raises_the_class_that_was_never_emitted(manager):
    _position(manager)
    review = _review(manager, {"price_usd": 1.60, "liquidity_usd": 250_000.0})
    assert review.action == "REDUCE"
    assert review.alerts[0].cls == "THESIS_STRENGTHENING"


def test_a_rug_is_an_invalidation_not_a_stop_loss(manager):
    """The strongest statement about a position: the reason to hold is gone."""
    _position(manager)
    review = _review(manager, {"price_usd": 0.90, "liquidity_usd": 500.0})
    assert review.action == "EXIT"
    assert review.alerts[0].cls == "THESIS_INVALIDATED"


def test_a_honeypot_found_after_entry_is_a_security_event(manager):
    _position(manager)
    review = _review(manager, {"price_usd": 1.10, "liquidity_usd": 250_000.0,
                               "is_honeypot": True})
    assert review.alerts[0].cls == "SECURITY_EVENT"
    assert review.alerts[0].severity == "HIGH"


def test_a_position_inside_its_plan_does_not_nag(manager):
    """An alert on every cycle is noise, and noise gets muted."""
    _position(manager)
    review = _review(manager, {"price_usd": 1.05, "liquidity_usd": 250_000.0})
    assert review.action == "HOLD"
    assert review.alerts == []


# --------------------------------------------------------- honest silence --

def test_a_missing_price_never_becomes_a_guess(manager):
    _position(manager)
    review = _review(manager, {"price_usd": None})
    assert review.action == "NO_DATA"
    assert review.alerts == []
    assert review.unknowns


def test_a_provider_failure_is_reported_not_swallowed(manager):
    """An unmonitored position is worse than one reported as unmonitorable."""
    _position(manager)

    def boom(chain, addr):
        raise ConnectionError("network unreachable")

    review = _review(manager, boom)
    assert review.action == "NO_DATA"
    assert any("ConnectionError" in u for u in review.unknowns)


def test_every_alert_carries_its_reasoning(manager):
    """A blocking or urging verdict without reasons is unaccountable."""
    _position(manager)
    for market in ({"price_usd": 0.60, "liquidity_usd": 250_000.0},
                   {"price_usd": 1.60, "liquidity_usd": 250_000.0},
                   {"price_usd": 0.90, "liquidity_usd": 500.0}):
        review = _review(manager, market)
        for alert in review.alerts:
            assert alert.reasons
            assert alert.evidence


# ------------------------------------------------ wired into the pipeline --

def test_the_pipeline_actually_reviews_the_book(manager):
    """Feature completeness is not reachability: it must run in the cycle."""
    from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
    from telegram_ai.adapter import MockTelegramAdapter

    _position(manager, symbol="MOON")
    monitor = _monitor(manager, {"price_usd": 0.55, "liquidity_usd": 180_000.0})
    telegram = MockTelegramAdapter()
    orchestrator = OpportunityPipelineOrchestrator(
        telegram_adapter=telegram, target_chat_id=1, position_monitor=monitor)

    report = orchestrator.run_pipeline(chain="solana", limit=3, now=NOW)

    assert len(report.position_reviews) == 1
    assert report.position_reviews[0].action == "EXIT"
    sent = " ".join(str(m) for m in telegram.sent_messages)
    assert "MOON" in sent
    assert "حد ضرر" in sent
    assert "تصمیم نهایی با کاربر است." in sent


def test_an_empty_book_does_not_break_discovery(manager):
    """A fresh install holds nothing; the discovery half must still run."""
    from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
    monitor = _monitor(manager, {"price_usd": 1.0})
    report = OpportunityPipelineOrchestrator(
        position_monitor=monitor).run_pipeline(chain="solana", limit=3, now=NOW)
    assert report.position_reviews == []


def test_monitoring_is_optional(manager):
    """Without a monitor the pipeline must still complete, not crash."""
    from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
    report = OpportunityPipelineOrchestrator().run_pipeline(
        chain="solana", limit=3, now=NOW)
    assert report.position_reviews == []


def test_a_broken_monitor_cannot_kill_the_cycle(manager):
    """Discovery must survive a failure in review; they are independent."""
    from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator

    class Broken:
        def review_all(self, now=None):
            raise RuntimeError("monitor exploded")

    report = OpportunityPipelineOrchestrator(
        position_monitor=Broken()).run_pipeline(chain="solana", limit=3, now=NOW)
    assert report.position_reviews == []
    assert report.candidates_collected >= 0


def test_a_stale_stored_price_never_drives_an_exit(manager):
    _position(manager)
    review = _review(manager, {"price_usd": 0.10, "liquidity_usd": 100.0,
                               "retrieved_ts": NOW - 5 * 3600})
    assert review.action == "NO_DATA"
    assert review.alerts == []
    assert "تازه" in " ".join(review.unknowns)


def test_production_runtime_constructs_the_paper_monitor():
    src = (ROOT_DIR / "architecture" / "runtime" / "__main__.py").read_text(
        encoding="utf-8")
    assert "build_position_monitor" in src
    assert "position_monitor=position_monitor" in src
