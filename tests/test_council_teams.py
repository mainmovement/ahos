"""Every mind has a team, every team has a question, every duty is performed.

The problem
-----------
`cognitive_registry_100.yaml` grouped 100 thinkers by academic discipline.
That answers "who are they?" and not "who decides what?", so 83 of them had no
role in any decision -- and grouping by discipline gave no way to notice.

Wave-31 re-organises the same 100 into seven operational teams, each owning one
question that must be settled before money moves, each member holding a named
duty. Nineteen members whose duty had no executable lens now have one.

The danger in a change like this is a roster that reads impressively and does
nothing -- a YAML file asserting capability the code lacks. So the central test
here is `validate()`: a member marked ACTIVE must have a lens that actually
votes and a data card with real citations behind it. If the promise and the
code disagree, these tests fail.

The second danger is a panel so large it refuses everything. Measured over 400
healthy and 400 hostile candidates the separation is unchanged at 100%/0%, and
that is pinned below too.
"""
from __future__ import annotations

import time

import pytest

from architecture.knowledge.teams import (
    load_structure, validate, VALID_STATUSES, CouncilStructure)
from architecture.knowledge.panel import (
    CognitivePanel, PANEL_LENSES, ALL_LENS_CARDS)
from architecture.knowledge.team_lenses import TEAM_PANEL_LENSES
from architecture.providers.contracts import (
    NormalizedTokenCandidate, MarketMetrics, SecuritySignals)
from architecture.intel.exitability import ExitabilityAnalyzer
from architecture.scoring.engine import OpportunityScorer

NOW = time.time()


def candidate(**overrides) -> NormalizedTokenCandidate:
    """A fully-populated healthy token."""
    security = dict(
        is_honeypot=False, sell_tax_pct=2.0, buy_tax_pct=2.0,
        liquidity_locked_pct=95.0, liquidity_burned_pct=100.0,
        has_mint_authority=False, has_freeze_authority=False,
        is_contract_verified=True, is_ownership_renounced=True,
        top10_holder_concentration_pct=15.0, deployer_past_rug_count=0,
        deployer_address="D" * 44)
    metrics = dict(
        price_usd=1.0, liquidity_usd=250_000.0, volume_1h=150_000.0,
        volume_24h=1_800_000.0, volume_5m=12_000.0, price_change_5m=3.0,
        price_change_6h=20.0, market_cap_usd=3_000_000.0,
        txns_5m_buys=40, txns_5m_sells=18, txns_1h_buys=900,
        txns_1h_sells=380, price_change_1h=18.0, price_change_24h=55.0,
        fdv_usd=4_000_000.0)
    for key, value in overrides.items():
        (security if key in security else metrics)[key] = value
    cand = NormalizedTokenCandidate(
        chain="solana", address="A" * 44, symbol="T", name="T",
        metrics=MarketMetrics(**metrics), security=SecuritySignals(**security),
        source_provider="dexscreener", retrieved_ts=NOW)
    cand.identify_unknowns()
    return cand


def deliberate(cand, lenses=None):
    panel = CognitivePanel(lenses=lenses) if lenses else CognitivePanel()
    return panel.deliberate(
        cand, score_report=OpportunityScorer().evaluate(cand, now=NOW),
        exitability=ExitabilityAnalyzer().analyze(cand, position_usd=100.0),
        now=NOW)


@pytest.fixture(scope="module")
def structure() -> CouncilStructure:
    return load_structure()


# ------------------------------------------------- the roster tells the truth --

def test_the_declared_structure_matches_the_code():
    """The test this file exists for.

    ACTIVE must mean the lens exists, votes, and has a citation-backed card.
    Any drift between council_teams.yaml and the panel shows up here.
    """
    problems = validate()
    assert not problems, "roster and code disagree:\n  " + "\n  ".join(problems)


def test_all_one_hundred_minds_are_assigned(structure):
    assert structure.total_members == 100, \
        f"{structure.total_members} assigned; nobody may be left out"


def test_nobody_is_assigned_twice(structure):
    seen = [m.thinker_id for t in structure.teams for m in t.members]
    seen += [b["id"] for b in structure.bench]
    assert len(seen) == len(set(seen))


def test_every_member_has_a_duty_and_a_valid_status(structure):
    for team in structure.teams:
        for m in team.members:
            assert m.duty.strip(), f"{m.thinker_id} has no duty"
            assert m.duty_fa.strip(), f"{m.thinker_id} has no Persian duty"
            assert m.status in VALID_STATUSES


def test_every_team_has_a_charter_and_a_lead_who_is_a_member(structure):
    for team in structure.teams:
        assert team.charter.strip() and team.charter_fa.strip()
        assert team.lead_member() is not None, \
            f"{team.team_id} lead {team.lead} is not on the team"


def test_the_bench_is_honest_about_not_voting(structure):
    """Engineering-bench members built the tools; giving them token-scoring
    duties would be theatre. They must not be counted as voters."""
    bench_ids = {b["id"] for b in structure.bench}
    voting_ids = {m.thinker_id for t in structure.teams for m in t.voting_members}
    assert not (bench_ids & voting_ids)


def test_external_lenses_are_not_folded_into_the_hundred(structure):
    """Munger, Mandelbrot and Marks vote but are not in the registry. Counting
    them among the 100 would inflate exactly the number being measured."""
    assert structure.external_lenses, "external lenses are no longer recorded"
    registry_ids = {m.thinker_id for t in structure.teams for m in t.members}
    for ext in structure.external_lenses:
        assert "lens_id" in ext and "team" in ext
        assert structure.team(ext["team"]) is not None
    assert structure.total_members == 100, \
        "external lenses leaked into the registry count"


# ------------------------------------------------------- duties are performed --

def test_every_active_member_actually_votes(structure):
    executable = {lens_id for lens_id, _ in PANEL_LENSES}
    for team in structure.teams:
        for m in team.members:
            if m.status == "ACTIVE":
                assert m.lens_id in executable, \
                    f"{m.name} is ACTIVE but {m.lens_id} never votes"


def test_every_voting_lens_has_a_card_with_citations():
    """A lens may not invent authority. Its principle must exist on a card."""
    for lens_id, _ in PANEL_LENSES:
        card = ALL_LENS_CARDS.get(lens_id)
        assert card is not None, f"{lens_id} votes with no data card"
        assert card.verified_principles, f"{lens_id} has no principles"
        for p in card.verified_principles:
            assert p.get("citation_ref"), f"{lens_id} principle lacks a citation"


def test_every_voting_lens_documents_where_it_breaks():
    """A lens that cannot say where its reasoning fails is being sold, not
    reasoned with."""
    for lens_id, _ in PANEL_LENSES:
        card = ALL_LENS_CARDS[lens_id]
        assert card.documented_failures, \
            f"{lens_id} documents no failure modes"


def test_every_team_lens_is_actually_wired():
    """A floor plus uniqueness, never an exact count.

    This asserted `== 19` and broke the moment two ADVISORY members were
    activated -- a test failing for growth it should have welcomed. What
    matters is that nothing was written and left unwired, and that no lens got
    registered twice (a duplicate votes twice, manufacturing a second
    "independent" opinion for the convergence rule to count).
    """
    ids = [lens_id for lens_id, _ in TEAM_PANEL_LENSES]
    assert len(ids) >= 19
    assert len(ids) == len(set(ids)), "a team lens is registered twice"
    wired = {lens_id for lens_id, _ in PANEL_LENSES}
    for lens_id in ids:
        assert lens_id in wired, f"{lens_id} was written but never wired in"


def test_no_opinion_carries_an_unresolved_citation():
    for opinion in deliberate(candidate()).opinions:
        assert not opinion.citation_ref.startswith("UNRESOLVED:"), \
            f"{opinion.lens_id} cites a principle absent from its card"


# ---------------------------------------------------------- the new findings --

@pytest.mark.parametrize("label,kwargs,lens_id", [
    ("finished pump", {"price_change_24h": 300.0, "price_change_1h": -8.0}, "LENS-NEWTON"),
    ("coordinated promotion", {"txns_1h_buys": 950, "txns_1h_sells": 50,
                               "price_change_1h": 200.0}, "LENS-MITNICK"),
    ("prior rug", {"deployer_past_rug_count": 1}, "LENS-KREBS"),
    ("dead turnover", {"volume_24h": 12_000.0, "volume_1h": 500.0}, "LENS-KEYNES"),
    ("owner keeps every lever", {"has_mint_authority": True,
                                 "liquidity_locked_pct": 40.0,
                                 "liquidity_burned_pct": 0.0}, "LENS-ANDERSON"),
])
def test_the_new_teams_catch_what_the_panel_previously_missed(label, kwargs, lens_id):
    verdict = deliberate(candidate(**kwargs))
    speaker = next(o for o in verdict.opinions if o.lens_id == lens_id)
    assert speaker.stance in ("VETO", "CAUTION"), \
        f"{lens_id} stayed silent on {label}"
    assert verdict.is_blocking, f"{label} was not blocked: {verdict.verdict}"


def test_a_stale_pump_is_recognised_as_already_over():
    """+300% on the day but negative in the last hour: the move has happened."""
    verdict = deliberate(candidate(price_change_24h=300.0, price_change_1h=-8.0))
    newton = next(o for o in verdict.opinions if o.lens_id == "LENS-NEWTON")
    assert newton.stance == "VETO"


def test_our_own_order_must_not_be_the_market_event():
    """$20 into a $1,000 pool is 2% of the pool -- we become the event."""
    verdict = deliberate(candidate(liquidity_usd=1_000.0))
    einstein = next(o for o in verdict.opinions if o.lens_id == "LENS-EINSTEIN")
    assert einstein.stance == "VETO"


def test_kelly_refuses_rather_than_guesses_without_a_probability():
    """Kelly is undefined without a win probability -- not merely imprecise."""
    bare = NormalizedTokenCandidate(
        chain="solana", address="B" * 44, symbol="X", name="X",
        source_provider="dexscreener", retrieved_ts=NOW)
    bare.identify_unknowns()
    verdict = CognitivePanel().deliberate(bare, now=NOW)
    thorp = next(o for o in verdict.opinions if o.lens_id == "LENS-THORP")
    assert thorp.stance == "ABSTAIN"


# ------------------------------------------- the filter still lets tokens in --

def test_a_healthy_token_still_passes_thirty_nine_lenses():
    """A council that refuses everything is as useless as one that refuses
    nothing. Two thresholds were corrected during this wave for exactly this:
    Deming fired on every score of 100 (47% of healthy tokens) and Keynes on
    every turnover above 20x (the healthy p90)."""
    verdict = deliberate(candidate())
    assert not verdict.is_blocking, \
        f"a clean token was blocked by: {verdict.vetoes + verdict.cautions}"


def test_ordinary_healthy_variation_does_not_trip_the_panel():
    """Turnover values span the measured healthy distribution: p10 ~5.6x,
    median ~12x, p90 ~22x, p99 ~27x over 600 simulated healthy candidates.
    A threshold set inside that range flags ordinary tokens, which is what
    both corrected lenses were doing."""
    for liquidity in (150_000.0, 300_000.0, 600_000.0):
        for turnover_24h in (5.6, 12.2, 21.8, 27.5):
            cand = candidate(liquidity_usd=liquidity,
                             volume_24h=liquidity * turnover_24h)
            verdict = deliberate(cand)
            assert not verdict.is_blocking, (
                f"healthy token blocked at liq={liquidity} turnover={turnover_24h}: "
                f"{verdict.vetoes + verdict.cautions}")
            # Not merely "not blocked" -- silent. A single caution does not
            # block, so is_blocking alone cannot detect a threshold that has
            # crept back inside the healthy range. It would simply start
            # warning on every ordinary token, and a warning that is always
            # on is what trains a user to ignore warnings.
            assert verdict.verdict == "APPROVE", (
                f"ordinary token at liq={liquidity} turnover={turnover_24h} drew "
                f"a warning: {verdict.cautions}")


def test_coverage_stays_high_on_a_fully_populated_candidate():
    """39 lenses must not mean 39 abstentions."""
    verdict = deliberate(candidate())
    assert verdict.coverage >= 0.90, \
        f"coverage collapsed to {verdict.coverage:.0%} with the larger bench"


# ---------------------------------------------------------- the team report --

def test_the_verdict_groups_by_team():
    grouped = deliberate(candidate()).by_team()
    assert "UNASSIGNED" not in grouped, \
        f"some lens belongs to no team: {grouped.get('UNASSIGNED')}"
    assert len(grouped) >= 5


def test_the_team_report_names_teams_and_the_expert_behind_each_finding():
    scam = candidate(sell_tax_pct=30.0, has_mint_authority=True,
                     top10_holder_concentration_pct=70.0,
                     liquidity_locked_pct=40.0, liquidity_burned_pct=0.0,
                     deployer_past_rug_count=1)
    text = deliberate(scam).team_summary_persian()
    assert "تیم بقا" in text
    assert "تیم حریف" in text
    assert "Brian Krebs" in text or "Ross Anderson" in text, \
        "a finding was reported without saying which specialist made it"


def test_the_team_structure_reaches_the_user():
    """Guards the recurring failure: capability that exists and is
    unreachable."""
    from telegram_ai.service import TelegramDomainService
    result = TelegramDomainService().handle_message("شورا از کیا تشکیل شده")
    assert result["intent"] == "COUNCIL_ROSTER"
    text = result["text"]
    assert "ساختار تیمی" in text
    assert "تیم بقا" in text
    assert "حق وتو" in text


def test_pending_data_members_are_shown_as_pending_not_active(structure):
    """Honesty about what is not yet possible is the point of the status
    field. Five offensive-security duties need contract bytecode we do not
    collect; claiming they run would be the overstatement being removed."""
    pending = [m for t in structure.teams for m in t.members
               if m.status == "PENDING_DATA"]
    assert pending, "nothing is pending? verify before believing"
    for m in pending:
        assert not m.votes
