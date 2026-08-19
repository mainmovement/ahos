"""Tests for AHOS Autonomous Hypothesis Engine (OSS-010)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import numpy as np
import pytest

from architecture.knowledge.duck_store import ColumnarKnowledgeStore
from strategy_lab.hypothesis_engine import AutonomousHypothesisEngine


def test_autonomous_hypothesis_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_hyp.db"
        store = ColumnarKnowledgeStore(db_path=db_path)
        engine = AutonomousHypothesisEngine(knowledge_store=store)

        np.random.seed(42)
        n = 150
        prices = 100.0 * np.exp(np.cumsum(np.random.normal(0.002, 0.015, n)))
        scores = np.random.uniform(40.0, 95.0, n)

        result = engine.evaluate_hypothesis(
            hypothesis_id="HYP-MOMENTUM-01",
            title="Momentum Volume Expansion",
            category="MOMENTUM",
            prices=prices,
            scores=scores,
            entry_thresh=75.0,
            stop_loss_pct=0.05,
            take_profit_pct=0.15,
        )

        assert result["hypothesis_id"] == "HYP-MOMENTUM-01"
        assert result["status"] in ["ACCEPTED", "REJECTED"]
        assert "annualized_sharpe" in result
        assert "oos_efficiency" in result
        assert "monte_carlo_stress" in result

        # Verify it was stored in knowledge store
        stats = store.summary_stats()
        assert stats["total_hypotheses"] == 1
