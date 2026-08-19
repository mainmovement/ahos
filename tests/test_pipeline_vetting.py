"""The autonomous cycle must vet before it announces.

Why this file exists
--------------------
The pipeline announced any candidate scoring >= 75.0 as «فرصت ویژه» straight to
Telegram. It never consulted exitability, the cognitive panel or the advisor --
those ran only when the user typed a question by hand.

That is not a cosmetic gap. Historically, a token with a 30% sell tax scored **100** on the opportunity
model despite being TRAPPED. The canonical scorer now also penalizes that tax,
but the autonomous path must retain its independent exitability and council
vetoes as defense in depth.

The unattended path -- the one that messages the user without being asked --
was the single least-defended path in the system, and the specification's
central demand is precisely that a pick be verified sellable before it is
recommended.

These tests pin that the full chain runs, that a veto suppresses the
announcement, and that a genuine opportunity still gets through. A safety
filter that blocks everything is as useless as one that blocks nothing.
"""
from __future__ import annotations

import time

import pytest

from architecture.pipeline.orchestrator import OpportunityPipelineOrchestrator
from architecture.providers.contracts import (
    NormalizedTokenCandidate, MarketMetrics, SecuritySignals)
from architecture.scoring.engine import OpportunityScorer
from telegram_ai.adapter import MockTelegramAdapter

NOW = time.time()


def candidate(symbol: str, **security_overrides) -> NormalizedTokenCandidate:
    """A fully evidenced token that scores 100 unless a trap override applies."""
    security = dict(
        is_honeypot=False, sell_tax_pct=1.0, buy_tax_pct=1.0,
        liquidity_locked_pct=95.0, has_mint_authority=False,
        has_freeze_authority=False, is_contract_verified=True,
        is_ownership_renounced=True, top10_holder_concentration_pct=12.0,
        deployer_past_rug_count=0)
    security.update(security_overrides)
    cand = NormalizedTokenCandidate(
        chain="solana", address=symbol, symbol=symbol, name=symbol,
        metrics=MarketMetrics(
            price_usd=1.0, liquidity_usd=200_000.0, volume_1h=120_000.0,
            volume_24h=1_500_000.0, txns_1h_buys=1_400, txns_1h_sells=300,
            price_change_1h=45.0, price_change_24h=90.0, fdv_usd=3_000_000.0),
        security=SecuritySignals(**security),
        source_provider="dexscreener", retrieved_ts=NOW)
    cand.identify_unknowns()
    return cand


@pytest.fixture
def orchestrator():
    return OpportunityPipelineOrchestrator(
        telegram_adapter=MockTelegramAdapter(), target_chat_id="1")


def _vet(orchestrator, cand):
    report = OpportunityScorer().evaluate(cand, now=NOW)
    advice, suppressed = orchestrator._vet(cand, report, NOW)
    return report, advice, suppressed


# ------------------------------------------------------ the proven exploit --

def test_a_high_scoring_trap_is_not_announced(orchestrator):
    """The regression that motivated this file. Score 100, sell tax 30%."""
    report, advice, suppressed = _vet(orchestrator, candidate("TRAP", sell_tax_pct=30.0))

    assert report.opportunity_score < 75.0, \
        "the canonical score layer stopped penalizing the known sell-tax trap"
    assert advice.action != "ENTER", \
        "a token whose funds cannot be withdrawn was approved for entry"
    assert suppressed, "suppression happened without recording a reason"


def test_the_suppression_reason_names_the_sell_tax(orchestrator):
    _, _, suppressed = _vet(orchestrator, candidate("TRAP", sell_tax_pct=30.0))
    joined = " ".join(suppressed)
    assert "مالیات فروش" in joined, f"reason did not cite the tax: {suppressed}"


@pytest.mark.parametrize("label,overrides", [
    ("sell tax", {"sell_tax_pct": 30.0}),
    ("mint authority live", {"has_mint_authority": True}),
    ("holder concentration", {"top10_holder_concentration_pct": 92.0}),
    ("deployer has rugged", {"deployer_past_rug_count": 2}),
    ("honeypot", {"is_honeypot": True}),
])
def test_known_traps_are_all_rejected(orchestrator, label, overrides):
    _, advice, _ = _vet(orchestrator, candidate("BAD", **overrides))
    assert advice.action != "ENTER", f"{label} was approved for entry"


# --------------------------------------------------- the filter still works --

def test_a_genuine_opportunity_is_still_approved(orchestrator):
    """A filter that rejects everything is as useless as one that rejects
    nothing. This is the other half of the guarantee."""
    _, advice, suppressed = _vet(orchestrator, candidate("CLEAN"))
    assert advice.action == "ENTER", \
        f"a clean, deep, exitable token was rejected: {suppressed}"
    assert advice.suggested_size_usd, "approved with no position size"


def test_approval_carries_its_reasoning(orchestrator):
    """The spec requires the pick be announced WITH the reason for it."""
    _, advice, _ = _vet(orchestrator, candidate("CLEAN"))
    assert advice.reasons, "approved with no stated reasoning"


# ------------------------------------------------------------- the message --

def test_rendered_verdict_is_readable_not_a_data_dump(orchestrator):
    """advice.panel is a dict holding ten lens objects. Rendering it whole
    dumped the entire structure into the chat window."""
    _, advice, _ = _vet(orchestrator, candidate("CLEAN"))
    text = orchestrator._render_verdict_fa(advice)

    assert "lens_id" not in text, "raw panel payload leaked into the message"
    assert "citation_ref" not in text
    assert "{" not in text and "}" not in text, "a dict was stringified into the text"
    assert len(text) < 1500, f"message is {len(text)} chars; a dict likely leaked"


def test_rendered_verdict_states_decision_exit_and_council(orchestrator):
    _, advice, _ = _vet(orchestrator, candidate("CLEAN"))
    text = orchestrator._render_verdict_fa(advice)
    assert "ENTER" in text
    assert "امکان خروج" in text
    assert "شورای تحلیلی" in text
    assert "دلیل انتخاب" in text


# -------------------------------------------------------- resilience rules --

def test_a_failing_analyser_does_not_crash_the_cycle(orchestrator, monkeypatch):
    """One broken probe must not take down the unattended run."""
    class Boom:
        def analyze(self, *a, **k):
            raise RuntimeError("probe exploded")

    monkeypatch.setattr(orchestrator, "whales", Boom())
    _, advice, suppressed = _vet(orchestrator, candidate("CLEAN"))
    assert advice is not None, "cycle died because one analyser failed"
    assert any("whales" in s for s in suppressed), \
        "an analyser failed silently; failure must be recorded"


def test_a_failing_exitability_probe_is_not_read_as_approval(orchestrator, monkeypatch):
    """The dangerous direction: if the check that proves funds can be
    withdrawn cannot run, that is unknown -- never a pass."""
    class Boom:
        def analyze(self, *a, **k):
            raise RuntimeError("probe exploded")

    monkeypatch.setattr(orchestrator, "exitability", Boom())
    _, advice, suppressed = _vet(orchestrator, candidate("CLEAN"))
    assert any("exitability" in s for s in suppressed)
    assert advice.exit_verdict != "EXITABLE", \
        "a crashed exitability probe was reported as a clean exit"


# ------------------------------------------------------------ wiring guard --

def test_the_specialist_chain_is_actually_wired_into_the_pipeline():
    """Guards the class of bug this whole file addresses: an engine that
    exists, is tested, and is never called from the unattended path."""
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "architecture" / "pipeline"
           / "orchestrator.py").read_text(encoding="utf-8")
    for engine in ("ExitabilityAnalyzer", "CognitivePanel", "DecisionAdvisor",
                   "ViralityTracker", "WhaleTracker"):
        assert engine in src, f"{engine} is not wired into the pipeline"


def test_announcement_requires_enter_not_merely_a_high_score():
    """The literal condition in the announce branch must test the vetted
    action. Reverting it to a bare score comparison fails here."""
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "architecture" / "pipeline"
           / "orchestrator.py").read_text(encoding="utf-8")
    assert 'getattr(vetted_advice, "action", None) == "ENTER"' in src, \
        "the announce path no longer gates on the vetted decision"


# ================================================================ end-to-end ==
#
# Everything above calls _vet directly. That proves the vetting logic, but the
# bug being fixed was one of *reachability*: engines that worked perfectly and
# were simply never called. Testing the helper cannot catch a regression that
# stops calling the helper. So these last tests drive the real run_pipeline()
# and read what actually landed in the chat.

class _FakeCollector:
    """Stands in for the live collector. Emits the observation records that
    run_pipeline rehydrates into candidates."""

    def __init__(self, cands):
        self._cands = cands

    def collect_candidates(self, chain="solana", limit=10, now=None):
        from architecture.collector.engine import CollectedObservationRecord
        out = []
        for i, c in enumerate(self._cands):
            out.append(CollectedObservationRecord(
                obs_id=f"obs-{i}", token_address=c.address, chain=c.chain,
                symbol=c.symbol, name=c.name, provider_source=c.source_provider,
                retrieved_ts=NOW, raw_evidence_hash="0" * 64,
                confidence_level="HIGH",
                metrics=dict(vars(c.metrics)), security=dict(vars(c.security)),
                unknown_fields=[]))
        return out


def _run(cands):
    adapter = MockTelegramAdapter()
    orch = OpportunityPipelineOrchestrator(
        collector=_FakeCollector(cands), telegram_adapter=adapter,
        target_chat_id="1")
    report = orch.run_pipeline(chain="solana", limit=10, now=NOW)
    return report, adapter.sent_messages


def test_end_to_end_the_trap_never_reaches_the_chat():
    """The real cycle, the real send path, the real proven exploit."""
    report, sent = _run([candidate("TRAP", sell_tax_pct=30.0)])

    assert report.top_opportunity.opportunity_score < 75.0, \
        "the canonical score layer stopped penalizing the known sell-tax trap"
    announcements = [m for m in sent if "فرصت ویژه" in m["text"]]
    assert not announcements, \
        f"a TRAPPED token was announced to the user: {announcements}"
    assert report.suppressed_by_veto, "suppressed without recording why"


def test_end_to_end_a_clean_token_does_reach_the_chat():
    report, sent = _run([candidate("CLEAN")])

    announcements = [m for m in sent if "فرصت ویژه" in m["text"]]
    assert len(announcements) == 1, \
        f"a clean opportunity was not announced: {report.suppressed_by_veto}"
    assert report.vetted_advice.action == "ENTER"


def test_end_to_end_the_announcement_carries_its_reasoning():
    """«با ذکر دلیل انتخاب» -- an unexplained signal is exactly what this
    project refuses to emit."""
    _, sent = _run([candidate("CLEAN")])
    text = next(m["text"] for m in sent if "فرصت ویژه" in m["text"])

    assert "دلیل انتخاب" in text, "announced a pick with no reasoning attached"
    assert "امکان خروج" in text, "announced without stating exit viability"
    assert "lens_id" not in text, "raw panel payload leaked into the chat"
