#!/usr/bin/env python3
"""P0 — Lane-B security authority (One-Brain sub-PR 1).

Regression tests proving that the Lane-B production pipeline enforces the
canonical doctrine BEFORE ranking / alerting:

    UNKNOWN security  => recommendation <= WATCH  (never a positive opportunity)
    security veto     => excluded from positive ranking + opportunity alerting
    explicit PASS     => normal opportunity path preserved

These tests do NOT modify Lane-A, scoring math, databases, or execution mode.
"""
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
from architecture.collector.engine import CollectorEngine
from architecture.scoring.engine import OpportunityScorer
from architecture.alerts.engine import AlertEngine
from architecture.providers.contracts import (
    NormalizedTokenCandidate, MarketMetrics, SecuritySignals, ProviderResponse,
)
from architecture.providers.registry import ProviderRouter
from architecture.security.gate import (
    SecurityGate, SecurityDisposition,
    VERDICT_VETO, VERDICT_PASS_WITH_UNKNOWN, VERDICT_PASS,
    CAP_AVOID, CAP_WATCH, CAP_PASS,
)
from architecture.security import assert_safe_environment
from architecture.intelligence.evidence import materialize_evidence
from telegram_ai.adapter import MockTelegramAdapter


class _MockDiscoveryProvider:
    def __init__(self, name, candidates):
        self.provider_id = name
        self.capabilities = ["discovery"]
        self.candidates = candidates

    def fetch_candidate_tokens(self, chain, limit=10):
        return ProviderResponse(self.provider_id, "OK", tokens=self.candidates[:limit])

    def fetch_token_metrics(self, chain, address):
        return ProviderResponse(self.provider_id, "OK", tokens=[])


def _strong_metrics():
    # Deliberately strong market factors so ONLY the security gate can hold it back.
    return MarketMetrics(
        price_usd=0.10,
        liquidity_usd=90000.0,
        volume_1h=45000.0,
        txns_1h_buys=95,
        txns_1h_sells=15,
    )


def _run(cand, tmp_path, chain="solana", db_name="sec_gate.sqlite"):
    router = ProviderRouter()
    router.providers["dexscreener"] = _MockDiscoveryProvider("dexscreener", [cand])
    router.providers["geckoterminal"] = _MockDiscoveryProvider("geckoterminal", [])
    collector = CollectorEngine(db_path=str(tmp_path / db_name), router=router)
    adapter = MockTelegramAdapter()
    orch = OpportunityPipelineOrchestrator(
        collector=collector,
        scorer=OpportunityScorer(),
        alert_engine=AlertEngine(score_threshold=70.0),
        telegram_adapter=adapter,
        target_chat_id=123456,
    )
    report = orch.run_pipeline(chain=chain, limit=5)
    return report, adapter


# ----------------------------------------------------------------- TEST 1 --
def test_unknown_security_cannot_produce_positive_opportunity(tmp_path):
    """UNKNOWN security + strong market factors => WATCH cap, no OPPORTUNITY."""
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="SolUnknownSec111111111111111111111111111",
        symbol="UNK",
        name="Unknown Security",
        source_provider="dexscreener",
        retrieved_ts=time.time(),
        metrics=_strong_metrics(),
        security=SecuritySignals(),  # everything UNKNOWN (is_honeypot is None)
        social_presence={"twitter": "https://x.com/unk"},
    )
    report, _ = _run(cand, tmp_path)
    top = report.top_opportunity
    assert top is not None
    assert top.security_disposition == VERDICT_PASS_WITH_UNKNOWN
    assert top.recommendation_cap == CAP_WATCH
    # A positive opportunity alert must NOT fire even if the numeric score is high.
    assert not any(a.cls == "OPPORTUNITY" for a in report.alerts)


# ----------------------------------------------------------------- TEST 2 --
def test_unknown_security_cannot_trigger_positive_telegram(tmp_path):
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="SolUnknownTg1111111111111111111111111111",
        symbol="UNKTG",
        name="Unknown Security TG",
        source_provider="dexscreener",
        retrieved_ts=time.time(),
        metrics=_strong_metrics(),
        security=SecuritySignals(),
    )
    report, adapter = _run(cand, tmp_path, db_name="sec_gate_tg.sqlite")
    assert report.telegram_messages_sent == 0
    assert not any("فرصت ویژه" in m["text"] for m in adapter.sent_messages)


# ----------------------------------------------------------------- TEST 3 --
def test_confirmed_veto_cannot_reach_positive_ranking(tmp_path):
    """Affirmed critical failure (mint authority) => VETO, not a positive opportunity,
    even though honeypot=False and market factors are strong."""
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="SolMintVeto11111111111111111111111111111",
        symbol="MINT",
        name="Mint Authority Active",
        source_provider="dexscreener",
        retrieved_ts=time.time(),
        metrics=_strong_metrics(),
        security=SecuritySignals(is_honeypot=False, has_mint_authority=True),
    )
    report, _ = _run(cand, tmp_path, db_name="sec_gate_veto.sqlite")
    top = report.top_opportunity
    assert top is not None
    assert top.security_disposition == VERDICT_VETO
    assert top.recommendation_cap == CAP_AVOID
    assert not any(a.cls == "OPPORTUNITY" for a in report.alerts)


# ----------------------------------------------------------------- TEST 4 --
def test_veto_disposition_suppresses_opportunity_alert():
    """AlertEngine must not emit an OPPORTUNITY alert for a vetoed candidate,
    while the legacy (no-disposition) call path is preserved."""
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="SolAlertVeto1111111111111111111111111111",
        symbol="AV",
        name="Alert Veto",
        source_provider="dexscreener",
        retrieved_ts=time.time(),
        metrics=_strong_metrics(),
        security=SecuritySignals(is_honeypot=False, is_contract_verified=True,
                                 is_ownership_renounced=True),
    )
    rep = OpportunityScorer().evaluate(cand)
    engine = AlertEngine(score_threshold=70.0)

    veto = SecurityDisposition(verdict=VERDICT_VETO, recommendation_cap=CAP_AVOID,
                               veto_reasons=("mint_authority_active",))
    gated = engine.evaluate_opportunity(rep, cand, disposition=veto)
    assert not any(a.cls == "OPPORTUNITY" for a in gated)

    unknown = SecurityDisposition(verdict=VERDICT_PASS_WITH_UNKNOWN,
                                  recommendation_cap=CAP_WATCH,
                                  unknown_critical=("honeypot",))
    gated_unknown = engine.evaluate_opportunity(rep, cand, disposition=unknown)
    assert not any(a.cls == "OPPORTUNITY" for a in gated_unknown)

    # Legacy path (no disposition supplied) is unchanged.
    legacy = engine.evaluate_opportunity(rep, cand)
    assert any(a.cls == "OPPORTUNITY" for a in legacy)


# ----------------------------------------------------------------- TEST 5 --
def test_explicit_pass_preserves_normal_opportunity_path(tmp_path):
    cand = NormalizedTokenCandidate(
        chain="solana",
        address="SolPassGem111111111111111111111111111111",
        symbol="PASS",
        name="Clean Pass Gem",
        source_provider="dexscreener",
        retrieved_ts=time.time(),
        metrics=_strong_metrics(),
        security=SecuritySignals(
            is_honeypot=False,
            is_contract_verified=True,
            is_ownership_renounced=True,
            top10_holder_concentration_pct=20.0,
        ),
        social_presence={"twitter": "https://x.com/pass"},
    )
    report, adapter = _run(cand, tmp_path, db_name="sec_gate_pass.sqlite")
    top = report.top_opportunity
    assert top is not None
    assert top.security_disposition == VERDICT_PASS
    assert top.recommendation_cap == CAP_PASS
    assert any(a.cls == "OPPORTUNITY" for a in report.alerts)
    assert report.telegram_messages_sent >= 1
    assert any("PASS" in m["text"] for m in adapter.sent_messages)


# ----------------------------------------------------------------- TEST 6 --
def test_gate_semantics_are_compatible_with_lane_a():
    """The Lane-B gate reuses Lane-A's canonical verdict vocabulary and the
    'honeypot => VETO / UNKNOWN => WATCH' mapping (semantic parity, no import
    of Lane-A into architecture/)."""
    from discovery import security_gate as lane_a  # test-only import

    # Verdict + cap vocabulary is identical to the canonical Lane-A gate.
    honeypot_true = lane_a.evaluate([
        {"check_key": "honeypot", "value": "TRUE", "severity": "CRITICAL"},
    ])
    assert honeypot_true["verdict"] == VERDICT_VETO == "SECURITY_VETO"
    assert honeypot_true["recommendation_cap"] == CAP_AVOID == "AVOID"

    unknown = lane_a.evaluate([])  # no checks => UNKNOWN critical
    assert unknown["verdict"] == VERDICT_PASS_WITH_UNKNOWN == "PASS_WITH_UNKNOWN"
    assert unknown["recommendation_cap"] == CAP_WATCH == "WATCH"

    # Lane-B gate produces the same dispositions from Evidence.
    gate = SecurityGate()
    hp_cand = NormalizedTokenCandidate(
        chain="solana", address="A" * 40, symbol="HP", name="Honeypot",
        source_provider="dexscreener", retrieved_ts=time.time(),
        metrics=MarketMetrics(liquidity_usd=50000.0, volume_1h=10000.0),
        security=SecuritySignals(is_honeypot=True),
    )
    hp_disp = gate.evaluate(materialize_evidence(hp_cand))
    assert hp_disp.verdict == VERDICT_VETO
    assert "honeypot" in hp_disp.veto_reasons

    unk_cand = NormalizedTokenCandidate(
        chain="solana", address="B" * 40, symbol="UK", name="Unknown",
        source_provider="dexscreener", retrieved_ts=time.time(),
        metrics=MarketMetrics(liquidity_usd=50000.0, volume_1h=10000.0),
        security=SecuritySignals(),
    )
    unk_disp = gate.evaluate(materialize_evidence(unk_cand))
    assert unk_disp.verdict == VERDICT_PASS_WITH_UNKNOWN
    assert unk_disp.recommendation_cap == CAP_WATCH


# ----------------------------------------------------------------- TEST 7 --
def test_paper_only_and_zero_money_invariants_remain_green():
    """The security repair must not touch the PAPER_ONLY / zero-money invariant."""
    audit = assert_safe_environment()
    assert audit["paper_only_enforced"] is True
    assert audit["zero_real_trading"] is True
    # The gate is advisory disposition only — it exposes no execution vocabulary.
    disp = SecurityDisposition(verdict=VERDICT_PASS, recommendation_cap=CAP_PASS)
    assert disp.recommendation_cap in (CAP_PASS, CAP_WATCH, CAP_AVOID)
    assert not hasattr(disp, "order")
