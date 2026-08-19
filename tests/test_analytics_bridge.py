"""Tests for AHOS Analytics Bridge & Columnar Knowledge Store (OSS-001)."""

import tempfile
from pathlib import Path

import pytest

from architecture.intel.analytics_bridge import AnalyticsBridge
from architecture.knowledge.duck_store import ColumnarKnowledgeStore


def test_analytics_bridge_in_memory_query():
    bridge = AnalyticsBridge()
    data = [
        {"token": "SOL", "score": 0.85, "outcome": 1},
        {"token": "BONK", "score": 0.35, "outcome": 0},
        {"token": "JUP", "score": 0.72, "outcome": 1},
        {"token": "RAY", "score": 0.20, "outcome": 0},
    ]
    bridge.register_in_memory_data("test_scores", data)

    results = bridge.query_dicts(
        "SELECT token, score FROM test_scores WHERE score > 0.5 ORDER BY score DESC"
    )
    assert len(results) == 2
    assert results[0]["token"] == "SOL"
    assert results[1]["token"] == "JUP"
    bridge.close()


def test_analytics_bridge_brier_bins():
    bridge = AnalyticsBridge()
    data = [
        {"score": 0.85, "outcome": 1},
        {"score": 0.88, "outcome": 1},
        {"score": 0.15, "outcome": 0},
        {"score": 0.12, "outcome": 0},
    ]
    bridge.register_in_memory_data("brier_table", data)
    bins = bridge.compute_brier_calibration_bins(
        "brier_table", "score", "outcome", bins=10
    )
    assert len(bins) >= 2
    assert all("bin_idx" in b and "mean_predicted_prob" in b for b in bins)
    bridge.close()


def test_columnar_knowledge_store():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_knowledge.db"
        store = ColumnarKnowledgeStore(db_path=db_path)

        store.record_hypothesis_evaluation(
            hypothesis_id="HYP-001",
            title="Momentum Volume Breakout",
            category="MOMENTUM",
            status="ACCEPTED",
            sharpe_ratio=2.15,
            max_drawdown=0.12,
            win_rate=0.64,
            oos_efficiency=0.88,
            created_at_utc="2026-08-19T12:00:00Z",
            metadata={"timeframe": "1h", "asset": "SOL"},
        )

        store.record_hypothesis_evaluation(
            hypothesis_id="HYP-002",
            title="Overfitted Mean Reversion",
            category="MEAN_REVERSION",
            status="REJECTED",
            sharpe_ratio=0.82,
            max_drawdown=0.35,
            win_rate=0.48,
            oos_efficiency=0.31,
            created_at_utc="2026-08-19T12:30:00Z",
            metadata={"timeframe": "5m", "asset": "MEME"},
        )

        accepted = store.query_accepted_hypotheses(min_sharpe=1.5)
        assert len(accepted) == 1
        assert accepted[0]["hypothesis_id"] == "HYP-001"
        assert accepted[0]["metadata"]["timeframe"] == "1h"

        stats = store.summary_stats()
        assert stats["total_hypotheses"] == 2
        assert stats["accepted_count"] == 1
        assert stats["rejected_count"] == 1
