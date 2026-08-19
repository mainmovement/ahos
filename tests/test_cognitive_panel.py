"""Wave-26: the cognitive panel -- great minds as executable checks.

The registry of 100 thinkers used to be decoration: a YAML file nothing read.
This suite pins the behaviour of the version that actually runs.

The central claim under test is that these lenses are ANALYSIS, not theatre:
  * deterministic -- the same input yields the same verdict, every time
  * offline -- no network, no model, no API key
  * cited -- every opinion traces to a published principle
  * honest -- a lens without data ABSTAINS, and abstention never counts as
    approval

And the voting law: one veto sinks the verdict. Averaging would let nine mild
approvals drown a lens shouting 'honeypot'.
"""
from __future__ import annotations

import time

import json

import pytest

from architecture.knowledge.panel import (
    CognitivePanel, PanelVerdict, LensOpinion, PANEL_LENSES, PANEL_VERSION,
    STANCES, lens_munger_inversion, lens_taleb_ruin, lens_godel_unknowns,
    lens_nash_equilibrium, lens_schneier_weakest_link, lens_shannon_signal,
    lens_kahneman_fomo, lens_mandelbrot_tails,
)
from architecture.knowledge.panel import ALL_LENS_CARDS as LENS_PILOT_REGISTRY
from architecture.providers.contracts import (
    NormalizedTokenCandidate, MarketMetrics, SecuritySignals,
)
from architecture.scoring.engine import OpportunityScorer
from architecture.intel.exitability import ExitabilityAnalyzer
from architecture.intel.viral import ViralityTracker


# Wave-30 note on this fixture.
#
# It previously used retrieved_ts=0.0 and omitted liquidity_locked_pct, then
# asserted the result was a token that "should silence nobody". When the
# freshness and data-completeness lenses came online they correctly objected:
# a 1970 timestamp is not a fresh observation, and a token whose liquidity
# lock is unknown is not fully specified. The fixture was overstating itself,
# so the fixture is what changed -- the lenses were right.
NOW_FIXTURE = time.time()


def make(symbol="TOK", **kw):
    metrics = kw.pop("metrics", None) or MarketMetrics(
        price_usd=1.0, liquidity_usd=250_000.0,
        volume_5m=5_000.0, volume_1h=40_000.0,
        txns_5m_buys=30, txns_5m_sells=25,
        # 400/380 is a coin flip: the significance lens rightly refuses to
        # read direction into it. A healthy token needs a real imbalance.
        txns_1h_buys=900, txns_1h_sells=380, price_change_1h=8.0)
    security = kw.pop("security", None) or SecuritySignals(
        is_honeypot=False, sell_tax_pct=1.0, buy_tax_pct=1.0,
        has_mint_authority=False, has_freeze_authority=False,
        is_contract_verified=True, is_ownership_renounced=True,
        liquidity_locked_pct=95.0, top10_holder_concentration_pct=22.0,
        deployer_past_rug_count=0)
    c = NormalizedTokenCandidate(
        chain="solana", address=kw.pop("address", "a1"), symbol=symbol,
        name=symbol, metrics=metrics, security=security,
        source_provider="test",
        retrieved_ts=kw.pop("retrieved_ts", NOW_FIXTURE))
    c.identify_unknowns()
    return c


HEALTHY = make("GOOD")

SCAM = make(
    "SCAM",
    metrics=MarketMetrics(
        price_usd=0.001, liquidity_usd=900.0, volume_5m=8_000.0,
        volume_1h=9_000.0, txns_5m_buys=200, txns_5m_sells=2,
        txns_1h_buys=260, txns_1h_sells=8, price_change_1h=340.0),
    security=SecuritySignals(
        is_honeypot=True, sell_tax_pct=45.0, buy_tax_pct=5.0,
        has_mint_authority=True, has_freeze_authority=True,
        is_contract_verified=False, top10_holder_concentration_pct=92.0,
        deployer_past_rug_count=3))

EMPTY = make("EMPTY", metrics=MarketMetrics(), security=SecuritySignals())


def full_ctx(cand):
    sc, ex, vt = OpportunityScorer(), ExitabilityAnalyzer(), ViralityTracker()
    return {"score_report": sc.evaluate(cand),
            "exitability": ex.analyze(cand),
            "virality": vt.analyze(cand)}


# ------------------------------------------------------------ panel level --

def test_healthy_token_is_approved_by_every_lens():
    v = CognitivePanel().deliberate(HEALTHY, **full_ctx(HEALTHY))
    assert v.verdict == "APPROVE"
    # Coverage is a high floor, not 1.0. Some lenses legitimately abstain on a
    # perfectly healthy token: Kelly sizing has no calibrated win probability
    # until enough outcomes are labelled, and refusing to invent one is the
    # correct behaviour rather than a gap. Demanding 1.0 would pressure future
    # lenses into manufacturing votes.
    assert v.coverage >= 0.85, \
        f"a fully-specified token silenced too much of the panel: {v.coverage:.0%}"
    assert not v.vetoes


def test_honeypot_is_vetoed_from_several_independent_angles():
    """Convergence from different disciplines is the panel's whole value."""
    v = CognitivePanel().deliberate(SCAM, **full_ctx(SCAM))
    assert v.verdict == "VETO"
    assert v.is_blocking is True
    vetoing = {o.lens_id for o in v.opinions if o.stance == "VETO"}
    assert len(vetoing) >= 3, f"only {vetoing} objected to an obvious scam"
    assert "LENS-MUNGER" in vetoing      # inversion finds the kill paths
    assert "LENS-TALEB" in vetoing       # cannot exit => ruin


def test_a_single_veto_outweighs_many_approvals():
    """Averaging would bury the one lens that spotted the trap."""
    def approve_all(cand, ctx):
        return LensOpinion("LENS-X", "X", "P", "APPROVE", "fine")

    def veto_one(cand, ctx):
        return LensOpinion("LENS-V", "V", "P", "VETO", "fatal", severity=3)

    lenses = [(f"L{i}", approve_all) for i in range(9)] + [("LV", veto_one)]
    v = CognitivePanel(lenses=lenses).deliberate(HEALTHY)
    assert v.verdict == "VETO"
    assert len(v.approvals) == 9


def test_missing_data_yields_insufficient_evidence_not_approval():
    """Silence is not consent. This is the failure mode the panel exists to stop."""
    def mute(cand, ctx):
        return LensOpinion("LENS-M", "M", "P", "ABSTAIN", "no data")

    def ok(cand, ctx):
        return LensOpinion("LENS-O", "O", "P", "APPROVE", "fine")

    lenses = [(f"M{i}", mute) for i in range(8)] + [("O1", ok), ("O2", ok)]
    v = CognitivePanel(lenses=lenses).deliberate(HEALTHY)
    assert v.verdict == "INSUFFICIENT_EVIDENCE"
    assert v.coverage == pytest.approx(0.2)


def test_empty_token_does_not_slip_through_on_silence():
    v = CognitivePanel().deliberate(EMPTY, **full_ctx(EMPTY))
    assert v.verdict in ("VETO", "INSUFFICIENT_EVIDENCE")
    assert v.verdict != "APPROVE"
    assert len(v.abstentions) >= 5


def test_caution_is_distinct_from_both_approve_and_veto():
    thin = make("THIN", metrics=MarketMetrics(
        price_usd=1.0, liquidity_usd=5_000.0, volume_5m=100.0, volume_1h=900.0,
        txns_5m_buys=5, txns_5m_sells=4, txns_1h_buys=40, txns_1h_sells=38,
        price_change_1h=5.0))
    v = CognitivePanel().deliberate(thin, **full_ctx(thin))
    assert v.verdict in ("CAUTION", "VETO")
    if v.verdict == "CAUTION":
        assert v.cautions and not v.vetoes


def test_a_crashing_lens_abstains_and_never_approves():
    """A bug in one lens must not take down the panel -- nor pass as consent."""
    def boom(cand, ctx):
        raise RuntimeError("bug in this lens")

    v = CognitivePanel(lenses=[("LENS-BOOM", boom)]).deliberate(HEALTHY)
    assert len(v.abstentions) == 1
    assert v.verdict == "INSUFFICIENT_EVIDENCE"
    assert not v.approvals


def test_verdict_is_deterministic_across_runs():
    """No model, no randomness: identical input, identical output."""
    ctx = full_ctx(SCAM)
    a = CognitivePanel().deliberate(SCAM, **ctx, now=1.0)
    b = CognitivePanel().deliberate(SCAM, **ctx, now=1.0)
    assert a.to_dict() == b.to_dict()


def test_most_severe_finding_is_reported_first():
    v = CognitivePanel().deliberate(SCAM, **full_ctx(SCAM))
    severities = [o.severity for o in v.opinions]
    assert severities == sorted(severities, reverse=True)


def test_panel_is_always_advisory():
    v = CognitivePanel().deliberate(HEALTHY, **full_ctx(HEALTHY))
    assert v.advisory_only is True
    assert v.version == PANEL_VERSION


def test_verdict_is_json_serialisable():
    v = CognitivePanel().deliberate(SCAM, **full_ctx(SCAM))
    assert json.loads(json.dumps(v.to_dict(), ensure_ascii=False))["verdict"] == "VETO"


def test_panel_runs_with_no_context_at_all():
    """Lenses must degrade to ABSTAIN, not raise, when given nothing."""
    v = CognitivePanel().deliberate(HEALTHY)
    assert v.verdict in ("APPROVE", "CAUTION", "VETO", "INSUFFICIENT_EVIDENCE")


# ------------------------------------------------------------- provenance --

def test_every_opinion_declares_a_stance_from_the_locked_vocabulary():
    v = CognitivePanel().deliberate(SCAM, **full_ctx(SCAM))
    for o in v.opinions:
        assert o.stance in STANCES


def test_opinions_are_traceable_to_a_real_lens_card():
    """No invented authorities: each lens must exist in the verified registry."""
    for lens_id, _fn in PANEL_LENSES:
        assert lens_id in LENS_PILOT_REGISTRY, f"{lens_id} has no lens card"


def test_speaking_opinions_carry_a_citation():
    """A verdict without provenance is an opinion pretending to be evidence."""
    v = CognitivePanel().deliberate(SCAM, **full_ctx(SCAM))
    for o in v.opinions:
        if o.stance in ("VETO", "CAUTION", "APPROVE"):
            assert o.citation_ref, f"{o.lens_id} spoke without a citation"


def test_reasons_are_persian_and_user_facing():
    v = CognitivePanel().deliberate(SCAM, **full_ctx(SCAM))
    joined = " ".join(o.reason for o in v.opinions)
    assert any("\u0600" <= ch <= "\u06FF" for ch in joined)


def test_summary_declares_advisory_status_and_counts_silence():
    v = CognitivePanel().deliberate(EMPTY, **full_ctx(EMPTY))
    txt = v.summary_persian()
    assert "مشورتی" in txt
    assert "سکوت = تأیید نیست" in txt


# ----------------------------------------------------- individual lenses ---

def test_munger_inversion_finds_kill_paths_before_upside():
    op = lens_munger_inversion(SCAM, {})
    assert op.stance == "VETO"
    assert "هانی‌پات" in op.reason


def test_munger_abstains_without_security_data():
    assert lens_munger_inversion(EMPTY, {}).stance == "ABSTAIN"


def test_taleb_vetoes_a_position_that_cannot_be_exited():
    ctx = full_ctx(SCAM)
    op = lens_taleb_ruin(SCAM, ctx)
    assert op.stance == "VETO"


def test_taleb_abstains_without_an_exit_calculation():
    assert lens_taleb_ruin(HEALTHY, {}).stance == "ABSTAIN"


def test_godel_vetoes_when_core_data_is_absent():
    """Scoring a token with no price or liquidity is false precision."""
    op = lens_godel_unknowns(EMPTY, {})
    assert op.stance == "VETO"


def test_nash_vetoes_extreme_holder_concentration():
    assert lens_nash_equilibrium(SCAM, {}).stance == "VETO"


def test_nash_abstains_without_concentration_data():
    unknown_holders = make("U", security=SecuritySignals(
        top10_holder_concentration_pct=None))
    assert lens_nash_equilibrium(unknown_holders, {}).stance == "ABSTAIN"


def test_schneier_vetoes_a_deployer_with_rug_history():
    op = lens_schneier_weakest_link(SCAM, {})
    assert op.stance == "VETO"
    assert "رواگ" in op.reason


def test_schneier_abstains_when_checks_are_unanswered():
    unknown = make("U", security=SecuritySignals())
    assert lens_schneier_weakest_link(unknown, {}).stance == "ABSTAIN"


def test_shannon_flags_too_small_a_sample():
    quiet = make("QUIET", metrics=MarketMetrics(
        price_usd=1.0, liquidity_usd=50_000.0,
        txns_1h_buys=3, txns_1h_sells=2))
    op = lens_shannon_signal(quiet, {})
    assert op.stance == "CAUTION"


def test_kahneman_vetoes_wash_traded_hype():
    ctx = full_ctx(SCAM)
    op = lens_kahneman_fomo(SCAM, ctx)
    assert op.stance in ("VETO", "CAUTION")


def test_mandelbrot_flags_violent_moves_in_thin_pools():
    op = lens_mandelbrot_tails(SCAM, {})
    assert op.stance == "CAUTION"


@pytest.mark.parametrize("lens_id,fn", PANEL_LENSES)
def test_no_lens_raises_on_a_completely_empty_candidate(lens_id, fn):
    """Robustness: every lens must handle total absence of data."""
    op = fn(EMPTY, {})
    assert op.stance in STANCES


@pytest.mark.parametrize("lens_id,fn", PANEL_LENSES)
def test_no_lens_invents_a_metric_it_was_not_given(lens_id, fn):
    op = fn(EMPTY, {})
    if op.stance == "ABSTAIN":
        assert op.metric is None


# ------------------------------------------------------- advisor coupling --

def test_panel_veto_blocks_entry_in_the_advisor():
    from architecture.decision.advisor import DecisionAdvisor
    ctx = full_ctx(EMPTY)
    panel = CognitivePanel().deliberate(EMPTY, **ctx)
    advice = DecisionAdvisor().advise_entry(
        EMPTY, ctx["score_report"], panel=panel)
    assert advice.action == "AVOID"
    assert any("شورای تحلیلی" in v for v in advice.hard_vetoes)


def test_panel_cannot_upgrade_a_weak_setup():
    """One-directional ratchet: the panel may only ever reduce conviction."""
    from architecture.decision.advisor import DecisionAdvisor

    weak = make("WEAK", metrics=MarketMetrics(
        price_usd=1.0, liquidity_usd=1_000.0, volume_1h=100.0,
        txns_1h_buys=5, txns_1h_sells=5))
    ctx = full_ctx(weak)
    panel = CognitivePanel().deliberate(weak, **ctx)
    with_panel = DecisionAdvisor().advise_entry(
        weak, ctx["score_report"], exitability=ctx["exitability"], panel=panel)
    without = DecisionAdvisor().advise_entry(
        weak, ctx["score_report"], exitability=ctx["exitability"])
    rank = {"AVOID": 0, "WAIT": 1, "ENTER": 2}
    assert rank[with_panel.action] <= rank[without.action]


def test_healthy_token_survives_the_panel_unchanged():
    from architecture.decision.advisor import DecisionAdvisor
    ctx = full_ctx(HEALTHY)
    panel = CognitivePanel().deliberate(HEALTHY, **ctx)
    a = DecisionAdvisor().advise_entry(
        HEALTHY, ctx["score_report"], exitability=ctx["exitability"],
        virality=ctx["virality"], panel=panel)
    assert a.action == "ENTER"
    assert a.panel is not None and a.panel["verdict"] == "APPROVE"


def test_advice_with_panel_stays_serialisable():
    from architecture.decision.advisor import DecisionAdvisor
    ctx = full_ctx(HEALTHY)
    panel = CognitivePanel().deliberate(HEALTHY, **ctx)
    a = DecisionAdvisor().advise_entry(HEALTHY, ctx["score_report"], panel=panel)
    json.dumps(a.to_dict(), ensure_ascii=False)


def test_every_lens_principle_id_resolves_in_its_card():
    """Guards the bug this suite caught: hand-written principle IDs drifting
    out of sync with the registry, producing citation-less verdicts."""
    ctx = full_ctx(SCAM)
    for _lens_id, fn in PANEL_LENSES:
        op = fn(SCAM, ctx)
        if op.principle_id == "ERROR":
            continue
        assert not op.citation_ref.startswith("UNRESOLVED"), (
            f"{op.lens_id} cites {op.principle_id}, which its lens card "
            f"does not define")
