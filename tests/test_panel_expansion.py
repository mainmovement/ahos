"""The council was a tenth of the bench it claimed.

What was wrong
--------------
Three layers each declared more capability than they delivered:

  * `config/cognitive_registry_100.yaml` listed 100 thinkers. Its only
    consumer in the whole codebase was a test asserting the file contains 100
    unique names. No production code read a principle from it; no decision
    ever changed because a name was in that file.
  * `lenses.LENS_PILOT_REGISTRY` held 30 lens data cards. Twenty of them had
    no opinion function -- inert data with a citation.
  * `panel.PANEL_LENSES` ran 10 lenses, and the domains the specification asks
    for most insistently -- offensive security, tokenomics, banking, pure
    mathematics, physics -- had no voice at all.

Wave-30 gives ten of the inert cards an executable opinion, each derived from
a principle already carried on its card with a citation. No lens role-plays a
person: each reads a real field and applies one stated rule, and abstains when
the field is missing rather than manufacturing a vote.

The tests below hold three lines simultaneously, because a safety filter is
easy to get wrong in either direction:
  1. the new lenses catch traps the old ten approved;
  2. a genuinely clean token still passes (a filter that blocks everything is
     as useless as one that blocks nothing);
  3. missing data produces silence, never a fabricated opinion.
"""
from __future__ import annotations

import time

import pytest

from architecture.knowledge.panel import (
    CognitivePanel, PANEL_LENSES, LENS_APPLIED_PRINCIPLE,
    CONVERGENT_CAUTION_THRESHOLD)
from architecture.knowledge.panel import ALL_LENS_CARDS as LENS_PILOT_REGISTRY
from architecture.knowledge.coverage import analyze_coverage
from architecture.providers.contracts import (
    NormalizedTokenCandidate, MarketMetrics, SecuritySignals)
from architecture.intel.exitability import ExitabilityAnalyzer
from architecture.scoring.engine import OpportunityScorer

NOW = time.time()
OLD_TEN = PANEL_LENSES[:10]
NEW_LENSES = [lens_id for lens_id, _ in PANEL_LENSES[10:]]


def candidate(retrieved_ts=None, **overrides) -> NormalizedTokenCandidate:
    """A clean, deep, liquid token. Overrides inject one defect at a time."""
    security = dict(
        is_honeypot=False, sell_tax_pct=2.0, buy_tax_pct=2.0,
        liquidity_locked_pct=95.0, liquidity_burned_pct=0.0,
        has_mint_authority=False, has_freeze_authority=False,
        is_contract_verified=True, is_ownership_renounced=True,
        top10_holder_concentration_pct=15.0, deployer_past_rug_count=0)
    metrics = dict(
        price_usd=1.0, liquidity_usd=250_000.0, volume_1h=150_000.0,
        volume_24h=1_800_000.0, txns_1h_buys=1_200, txns_1h_sells=400,
        price_change_1h=35.0, price_change_24h=80.0, fdv_usd=4_000_000.0)
    for key, value in overrides.items():
        (security if key in security else metrics)[key] = value
    cand = NormalizedTokenCandidate(
        chain="solana", address="A" * 44, symbol="T", name="T",
        metrics=MarketMetrics(**metrics), security=SecuritySignals(**security),
        source_provider="dexscreener",
        retrieved_ts=retrieved_ts if retrieved_ts is not None else NOW)
    cand.identify_unknowns()
    return cand


def deliberate(cand, lenses=None):
    exitability = ExitabilityAnalyzer().analyze(cand, position_usd=100.0)
    report = OpportunityScorer().evaluate(cand, now=NOW)
    panel = CognitivePanel(lenses=lenses) if lenses else CognitivePanel()
    return panel.deliberate(cand, score_report=report,
                            exitability=exitability, now=NOW)


# ------------------------------------------------------------ the new bench --

def test_the_panel_actually_grew():
    # Wave-30 brought the bench to 20; Wave-31 added the 19 team lenses.
    # Asserting a floor rather than an exact count so growth does not require
    # editing this test, while a silent shrink still fails.
    assert len(PANEL_LENSES) >= 20, "the second bench is not wired in"
    assert len({lens_id for lens_id, _ in PANEL_LENSES}) == len(PANEL_LENSES), \
        "duplicate lens in the panel"


def test_every_executable_lens_cites_a_principle_from_its_own_card():
    """A lens may not invent a basis. Its principle_id must exist on its card.

    This is the guard against the failure mode the panel is most exposed to:
    inventing authority by attaching a famous name to an arbitrary rule.
    """
    for lens_id, _ in PANEL_LENSES:
        card = LENS_PILOT_REGISTRY.get(lens_id)
        assert card is not None, f"{lens_id} has no data card"
        # The Wave-30 lenses declare their applied principle explicitly. The
        # Wave-31 team lenses each carry exactly one, so the card itself is
        # unambiguous and no separate declaration is needed.
        principle_id = LENS_APPLIED_PRINCIPLE.get(lens_id)
        if principle_id is None and len(card.verified_principles) == 1:
            principle_id = card.verified_principles[0]["principle_id"]
        assert principle_id, f"{lens_id} does not declare which principle it applies"
        known = {p.get("principle_id") for p in card.verified_principles}
        assert principle_id in known, \
            f"{lens_id} applies {principle_id}, absent from its card {known}"


def test_no_opinion_carries_an_unresolved_citation():
    verdict = deliberate(candidate())
    for opinion in verdict.opinions:
        assert not opinion.citation_ref.startswith("UNRESOLVED:"), \
            f"{opinion.lens_id} cites something its card does not contain"


# --------------------------------------------------- traps the old ten missed --

@pytest.mark.parametrize("label,kwargs,lens_id", [
    ("stale observation", {"retrieved_ts": NOW - 90 * 60}, "LENS-LAMPORT"),
    ("wash trading", {"volume_1h": 1_500_000.0, "price_change_1h": 2.0}, "LENS-PEARL"),
    ("half-unlocked liquidity", {"liquidity_locked_pct": 45.0}, "LENS-BUTERIN"),
    ("verified but mint retained", {"has_mint_authority": True}, "LENS-THOMPSON"),
])
def test_the_new_lenses_catch_what_the_old_ten_approved(label, kwargs, lens_id):
    """Each of these scores well and passes the original ten."""
    cand = candidate(**kwargs)
    new = deliberate(cand)
    assert new.verdict in ("VETO", "CONVERGENT_CAUTION"), \
        f"{label} was not blocked: {new.verdict}"
    speaker = next(o for o in new.opinions if o.lens_id == lens_id)
    assert speaker.stance in ("VETO", "CAUTION"), \
        f"{lens_id} stayed quiet on {label}: {speaker.stance}"


def test_a_stale_candidate_is_refused_even_when_it_looks_perfect():
    """Data an hour and a half old describes a market that no longer exists."""
    assert deliberate(candidate(retrieved_ts=NOW - 90 * 60)).is_blocking


def test_wash_trading_is_distinguished_from_demand():
    """Huge churn that moves no price is recycling, not buying pressure."""
    verdict = deliberate(candidate(volume_1h=1_500_000.0, price_change_1h=2.0))
    pearl = next(o for o in verdict.opinions if o.lens_id == "LENS-PEARL")
    assert pearl.stance == "VETO"
    assert "wash" in pearl.reason.lower() or "ساختگی" in pearl.reason


def test_verified_source_does_not_excuse_a_retained_mint_authority():
    """Trusting Trust: audited text is irrelevant if the rules can be rewritten."""
    verdict = deliberate(candidate(has_mint_authority=True))
    thompson = next(o for o in verdict.opinions if o.lens_id == "LENS-THOMPSON")
    assert thompson.stance == "VETO"


# ------------------------------------------------- the filter still passes --

def test_a_clean_token_is_still_approved():
    """The other half of the guarantee. Enlarging the panel must not turn it
    into a machine that refuses everything."""
    verdict = deliberate(candidate(liquidity_locked_pct=100.0,
                                   liquidity_burned_pct=100.0))
    assert verdict.verdict == "APPROVE", \
        f"a clean token was blocked by: {verdict.cautions + verdict.vetoes}"


def test_ordinary_healthy_variation_does_not_trip_the_panel():
    """Optional fields are absent on every real DexScreener candidate. A
    warning that fires on everything trains the user to ignore warnings."""
    for locked in (85.0, 90.0, 95.0, 100.0):
        for top10 in (8.0, 15.0, 25.0, 35.0):
            verdict = deliberate(candidate(liquidity_locked_pct=locked,
                                           top10_holder_concentration_pct=top10))
            assert not verdict.is_blocking, \
                f"healthy token blocked at locked={locked} top10={top10}: {verdict.cautions}"


# ------------------------------------------------------ convergent caution --

def test_convergent_caution_blocks_but_a_single_caution_does_not():
    """Several independent lenses reaching for the alarm at once is a
    different fact from one doing so."""
    # A lone caution. This used to be built from a 700/690 buy split, which
    # relied on Fisher cautioning about a 50.4% buy ratio -- a "significant"
    # deviation only because the sample was large, and a finding no trading
    # decision could act on. That behaviour was itself the bug, so the fixture
    # now uses a real single finding: turnover just above the churn threshold,
    # which one lens flags and nothing else corroborates.
    single = deliberate(candidate(volume_24h=250_000.0 * 45.0))
    assert len(single.cautions) == 1, \
        f"fixture no longer produces exactly one caution: {single.cautions}"
    assert single.verdict == "CAUTION"
    assert not single.is_blocking, "one caution must not block on its own"

    several = deliberate(candidate(top10_holder_concentration_pct=45.0))
    assert len(several.cautions) >= CONVERGENT_CAUTION_THRESHOLD
    assert several.verdict == "CONVERGENT_CAUTION"
    assert several.is_blocking


def test_a_blocking_convergent_verdict_states_its_reasons():
    """A refusal with no stated reason is exactly what this project rejects.
    CONVERGENT_CAUTION blocks with an empty `vetoes` list, so the advisor has
    to read `cautions` -- if it does not, the user gets a silent AVOID."""
    from architecture.decision.advisor import DecisionAdvisor
    cand = candidate(top10_holder_concentration_pct=45.0)
    verdict = deliberate(cand)
    advice = DecisionAdvisor().advise_entry(
        cand, score_report=OpportunityScorer().evaluate(cand, now=NOW),
        exitability=ExitabilityAnalyzer().analyze(cand, position_usd=100.0),
        panel=verdict, now=NOW)
    assert advice.action == "AVOID"
    assert advice.hard_vetoes, "refused the trade without telling the user why"

    # Not merely "some reason exists" -- the panel's own findings must be in
    # there. Another code path can independently produce AVOID, which would
    # mask a regression where the advisor stops reading `cautions` and blocks
    # with no explanation of what the council actually saw.
    panel_reasons = [v for v in advice.hard_vetoes if "شورای تحلیلی" in v]
    assert panel_reasons, \
        f"the council blocked, but its reasons never reached the user: {advice.hard_vetoes}"
    assert any(caution[:25] in " ".join(panel_reasons)
               for caution in verdict.cautions), \
        "the stated reason does not correspond to any caution the panel raised"


# ------------------------------------------------------------ honest silence --

def test_lenses_abstain_rather_than_guess_when_data_is_absent():
    """Silence lowers coverage; a fabricated vote corrupts the verdict."""
    bare = NormalizedTokenCandidate(
        chain="solana", address="B" * 44, symbol="X", name="X",
        source_provider="dexscreener", retrieved_ts=NOW)
    bare.identify_unknowns()
    verdict = CognitivePanel().deliberate(bare, now=NOW)

    assert verdict.verdict in ("INSUFFICIENT_EVIDENCE", "VETO"), \
        f"an evidence-free candidate produced {verdict.verdict}"
    assert verdict.coverage < 0.5


def test_a_broken_lens_is_never_counted_as_approval():
    def explode(cand, ctx):
        raise RuntimeError("lens exploded")

    panel = CognitivePanel(lenses=list(PANEL_LENSES) + [("LENS-BOOM", explode)])
    verdict = panel.deliberate(candidate(), now=NOW)
    boom = next(o for o in verdict.opinions if o.lens_id == "LENS-BOOM")
    assert boom.stance == "ABSTAIN"
    assert boom.reason not in verdict.approvals


# ------------------------------------------------------- registry coverage --

def test_coverage_reports_the_measured_number_not_the_headline():
    """The registry lists 100 minds. The honest figure is how many vote."""
    cov = analyze_coverage()
    assert cov.total_thinkers == 100
    assert cov.total_executable >= 17, \
        f"executable council shrank to {cov.total_executable}"
    assert cov.total_executable < cov.total_thinkers, \
        "claiming all 100 vote would be the very overstatement this measures"


def test_coverage_lists_the_still_inert_cards():
    """Naming what is not yet wired is what keeps this honest."""
    cov = analyze_coverage()
    assert cov.inert_cards, "every card is executable? verify before believing"
    executable = {lens_id for lens_id, _ in PANEL_LENSES}
    assert not (set(cov.inert_cards) & executable), \
        "a card is reported inert while it votes"


def test_the_roster_answer_reaches_the_user():
    """Guards the recurring failure: a capability that exists and is
    unreachable. Nothing consumed the registry before this."""
    from telegram_ai.service import TelegramDomainService
    result = TelegramDomainService().handle_message("شورا از کیا تشکیل شده")
    assert result["intent"] == "COUNCIL_ROSTER"
    assert result["status"] == "OK"
    assert "۱۰۰" in result["text"] or "100" in result["text"]


def test_the_roster_names_the_principle_each_lens_applies():
    """Thompson's card lists Unix composition first, but his lens reasons from
    Trusting Trust. Printing the first principle was a small lie about our
    own basis."""
    from telegram_ai.service import TelegramDomainService
    text = TelegramDomainService().handle_message("لیست نوابغ")["text"]
    assert "Trusting Trust" in text
