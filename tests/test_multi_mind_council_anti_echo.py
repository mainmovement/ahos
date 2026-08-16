#!/usr/bin/env python3
"""Tests for Multi-Mind Council Synthesis & Anti-Echo-Chamber Engineering (Phase XXII)."""
import sys, time
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from architecture.council import synthesize_multi_mind_council, run_council, validate_report
from architecture.knowledge.anti_echo import AntiEchoEngine, EchoChamberAuditResult


def test_anti_echo_copied_reasoning_detection():
    engine = AntiEchoEngine(text_similarity_threshold=0.80)
    # Three models returning almost identical copy-pasted phrases
    responses = [
        {"agent_id": "model_1", "text": "This token is poised for a massive 100x breakout based on liquidity.", "sources": ["https://twitter.com/post1"]},
        {"agent_id": "model_2", "text": "This token is poised for a massive 100x breakout based on liquidity depth.", "sources": ["https://twitter.com/post1"]},
        {"agent_id": "model_3", "text": "This token is poised for a massive 100x breakout based on liquidity.", "sources": ["https://twitter.com/post1"]},
    ]
    res = engine.audit_responses(responses, evidence_count=0)
    assert res.copied_reasoning_detected is True
    assert res.source_monoculture_detected is True
    assert res.epistemic_verdict == "INSUFFICIENT_EVIDENCE"
    assert "NULL THESIS INVERSION" in res.contrarian_thesis


def test_council_evidence_over_consensus_law():
    """If 10 models agree but zero evidence refs exist -> verdict must remain INSUFFICIENT_EVIDENCE."""
    models_agreeing = [
        {"provider": f"model_{i}", "claims": {"opportunity": "HIGH_PUMP"}, "evidence_refs": []}
        for i in range(10)
    ]
    rep = synthesize_multi_mind_council(
        artifact_ref="art:test_token",
        task_class="opportunity_evaluation",
        provider_responses=models_agreeing
    )
    # Consensus without evidence is rejected by epistemic law
    assert rep["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert rep["advisory_only"] is True


def test_council_disagreement_recorded():
    responses = [
        {"provider": "model_bull", "claims": {"direction": "UP"}, "evidence_refs": ["ev:obs1"]},
        {"provider": "model_bear", "claims": {"direction": "DOWN"}, "evidence_refs": ["ev:obs1"]}
    ]
    rep = synthesize_multi_mind_council(
        artifact_ref="art:test_token",
        task_class="opportunity_evaluation",
        provider_responses=responses
    )
    assert rep["verdict"] == "DISAGREEMENT"
    assert rep["agreement_matrix"]["direction"]["state"] == "CONFLICT"


def test_council_offline_floor_deterministic():
    """When zero AI models are available, Council returns OFFLINE with DETERMINISTIC_ONLY floor."""
    rep = synthesize_multi_mind_council(
        artifact_ref="art:test",
        task_class="eval",
        provider_responses=[]
    )
    assert rep["council_status"] == "OFFLINE"
    assert rep["verdict"] == "INSUFFICIENT_EVIDENCE"
    assert rep["deterministic_floor"] == "ACTIVE"
