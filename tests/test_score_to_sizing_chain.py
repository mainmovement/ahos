"""End-to-end contracts from a persisted score to council position sizing.

This is the canonical adaptation of the recovered Wave-33 regression suite.
It uses architecture.learning (the sole prediction-integrity layer) and the
immutable EXIT_V1 policy; no competing evolution calibration store is restored.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

import pytest

from architecture.knowledge.panel import PANEL_LENSES
from architecture.knowledge.team_lenses import lens_thorp_kelly
from architecture.providers.contracts import (
    NormalizedTokenCandidate, MarketMetrics, SecuritySignals)
from architecture.scoring.engine import OpportunityScorer
from paper_trading.exit_rules import EXIT_V1

ROOT = Path(__file__).resolve().parents[1]
NOW = time.time()
ADDR = "So11111111111111111111111111111111111111112"
TAKE_PROFIT_PCT = float(EXIT_V1["take_profit_pct"])
STOP_LOSS_PCT = float(EXIT_V1["stop_loss_pct"])


def _healthy_candidate(**overrides) -> NormalizedTokenCandidate:
    security = dict(
        is_honeypot=False, sell_tax_pct=2.0, buy_tax_pct=2.0,
        is_contract_verified=True, is_ownership_renounced=True,
        has_mint_authority=False, has_freeze_authority=False,
        liquidity_locked_pct=90.0, liquidity_burned_pct=0.0,
        top10_holder_concentration_pct=18.0, deployer_past_rug_count=0,
        deployer_address="D" * 44)
    metrics = dict(
        price_usd=0.01, liquidity_usd=250_000.0, volume_1h=90_000.0,
        volume_24h=1_500_000.0, volume_5m=8_000.0, fdv_usd=3_000_000.0,
        market_cap_usd=2_000_000.0, price_change_5m=0.8, price_change_1h=4.0,
        price_change_6h=9.0, price_change_24h=15.0, txns_1h_buys=520,
        txns_1h_sells=380, txns_5m_buys=44, txns_5m_sells=33)
    security.update({k: v for k, v in overrides.items() if k in security})
    metrics.update({k: v for k, v in overrides.items() if k in metrics})
    cand = NormalizedTokenCandidate(
        chain="solana", address=ADDR, symbol="ALPHA", name="Alpha",
        source_provider="dexscreener", retrieved_ts=NOW,
        pair_created_ts=NOW - 86_400, dex_id="raydium",
        confidence_level="HIGH", metrics=MarketMetrics(**metrics),
        security=SecuritySignals(**security))
    cand.identify_unknowns()
    return cand


def test_the_panel_accepts_a_calibration_and_passes_it_through():
    from architecture.knowledge.panel import CognitivePanel
    from architecture.knowledge.team_lenses import lens_thorp_kelly
    seen = {}
    def spy(cand, ctx):
        seen.update(ctx)
        return lens_thorp_kelly(cand, ctx)
    sentinel = object()
    CognitivePanel(lenses=[("LENS-THORP", spy)]).deliberate(
        _healthy_candidate(), calibration=sentinel, now=NOW)
    assert seen.get("calibration") is sentinel


def test_thorp_votes_once_a_guarded_descriptive_rate_exists():
    from architecture.knowledge.team_lenses import lens_thorp_kelly
    report = _calibrated(140, 200)
    class Ex: realizable_fraction = 0.95
    class SR: opportunity_score = 90.0
    op = lens_thorp_kelly(None, {"score_report": SR(), "exitability": Ex(),
                                 "calibration": report})
    assert op.stance == "APPROVE"


def test_no_calibration_means_an_honest_abstention():
    from architecture.knowledge.team_lenses import lens_thorp_kelly
    class Ex: realizable_fraction = 0.95
    class SR: opportunity_score = 95.0
    op = lens_thorp_kelly(None, {"score_report": SR(), "exitability": Ex(),
                                 "calibration": None})
    assert op.stance == "ABSTAIN"


def test_kelly_uses_net_odds_not_the_gross_multiple():
    """`b = 1.5` was a unit error, and it was not conservative.

    Kelly's `b` is the profit per unit staked on a win. Exiting at EXIT_V1's
    take-profit pays +50%, so b = 0.50, not 1.5. The downside was wrong too:
    the code assumed a total loss while EXIT_V1 stops out at -35%.

    Break-even therefore sat at p = 0.400 instead of the true p = c/(a+c) =
    0.412. In that band the lens called a losing bet profitable.
    """
    a, c = TAKE_PROFIT_PCT, STOP_LOSS_PCT
    break_even = c / (a + c)

    class _Ex:
        realizable_fraction = 1.0

    class _SR:
        def __init__(self, s):
            self.opportunity_score = s

    class _Cal:
        is_usable = True

        def __init__(self, p):
            self._p = p

        def probability_for_score(self, score):
            return (self._p, (self._p, self._p))

    just_below = lens_thorp_kelly(None, {"score_report": _SR(80.0),
                                         "exitability": _Ex(),
                                         "calibration": _Cal(break_even - 0.01)})
    assert just_below.stance == "VETO", (
        f"p={break_even - 0.01:.3f} is below break-even {break_even:.3f} "
        f"but the lens said {just_below.stance}")

    just_above = lens_thorp_kelly(None, {"score_report": _SR(80.0),
                                         "exitability": _Ex(),
                                         "calibration": _Cal(break_even + 0.05)})
    assert just_above.stance != "VETO"


def test_the_recommended_fraction_stays_inside_the_bankroll():
    """With a -35% stop rather than a total loss, raw f* can exceed 1.0.

    That is arithmetically faithful -- the formula sizes against the stop
    distance -- and practically absurd on a $20 bankroll, so it must be capped
    before it is ever reported as a share of capital.
    """
    class _Ex:
        realizable_fraction = 1.0

    class _SR:
        opportunity_score = 99.0

    class _Cal:
        is_usable = True

        @staticmethod
        def probability_for_score(score):
            return (0.95, (0.9, 0.99))

    op = lens_thorp_kelly(None, {"score_report": _SR(), "exitability": _Ex(),
                                 "calibration": _Cal()})
    assert op.stance == "APPROVE"
    assert op.metric is not None
    assert 0.0 < op.metric <= 0.25, \
        f"quarter-Kelly reported {op.metric:.2%} of capital"


# ============================================================ import safety --

def test_the_bench_is_identical_whichever_module_loads_first():
    """`team_lenses` and `panel` import each other.

    Registration used to happen only from panel.py, so importing
    `architecture.knowledge.team_lenses` directly -- the natural thing for a
    test or a new caller to do -- raised ImportError on a partially
    initialised module. Both directions must now work, and neither may
    register a lens twice: a duplicated lens votes twice, manufacturing a
    second "independent" opinion for the convergence rule to count.
    """
    ids = [lens_id for lens_id, _ in PANEL_LENSES]
    assert len(ids) == len(set(ids)), \
        f"duplicate lenses on the bench: {sorted({i for i in ids if ids.count(i) > 1})}"
    assert len(ids) >= 39
    assert "LENS-THORP" in ids


def test_importing_team_lenses_first_does_not_explode():
    import subprocess
    import sys
    result = subprocess.run(
        [sys.executable, "-c",
         "import architecture.knowledge.team_lenses as t;"
         "from architecture.knowledge.panel import PANEL_LENSES;"
         "ids=[i for i,_ in PANEL_LENSES];"
         "assert len(ids)==len(set(ids));"
         "assert 'LENS-THORP' in ids;"
         "print(len(ids))"],
        cwd=str(ROOT), capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stderr[-1500:]



# ============================================ candidate/report correspondence --

def test_each_alert_is_built_from_its_own_tokens_score():
    """`reports.sort()` desynchronised a positional zip.

    The pipeline scored candidates in collection order, sorted the REPORTS by
    score, then recombined the two lists with zip(). Whenever the collection
    order was not already descending by score, every alert paired one token's
    candidate with a different token's report -- so the alert cited one address
    while the metrics, provider and evidence came from another token entirely.
    """
    scorer = OpportunityScorer()
    specs = [("LOWLIQ", 5_000.0), ("DEEP", 400_000.0), ("MID", 90_000.0)]
    cands = []
    for sym, liq in specs:
        c = _healthy_candidate()
        c.symbol = sym
        c.address = (sym[0] * 44)
        c.metrics.liquidity_usd = liq
        c.metrics.volume_24h = liq * 10
        c.metrics.volume_1h = liq / 20
        cands.append(c)

    scored = [(c, scorer.evaluate(c, now=NOW)) for c in cands]
    scored.sort(key=lambda pair: pair[1].opportunity_score, reverse=True)

    assert [r.opportunity_score for _, r in scored] == \
        sorted([r.opportunity_score for _, r in scored], reverse=True)
    for cand, report in scored:
        assert cand.symbol == report.token_symbol, (
            f"candidate {cand.symbol} paired with report for "
            f"{report.token_symbol}")
        assert cand.address == report.token_address


# ================================ significance is not importance (Wave-33b) --

def _panel_op(cand, lens_id, **ctx):
    from architecture.knowledge.panel import CognitivePanel
    v = CognitivePanel().deliberate(cand, now=NOW, **ctx)
    return next(o for o in v.opinions if o.lens_id == lens_id)


def test_a_balanced_order_book_is_not_vetoed_for_being_busy():
    """A z-test's power grows without bound in n.

    At 10,000 trades an hour it turns "significant" at a 49% buy ratio; at
    50,000, at 49.6%. LENS-FISHER answered that with a VETO -- the harshest
    verdict the panel has, the one reserved for honeypots -- applied to an
    ordinary balanced book on the most liquid tokens in the sample. Activity
    was being punished as pathology, and it cost 105 of 400 healthy tokens.
    """
    cand = _healthy_candidate()
    cand.metrics.txns_1h_buys = 9_800
    cand.metrics.txns_1h_sells = 10_200      # 49% buys, |z| >> 1.96
    op = _panel_op(cand, "LENS-FISHER")
    assert op.stance != "VETO", (
        f"a 49% buy ratio over 20k trades was vetoed: {op.reason}")


def test_a_real_exodus_is_still_fatal():
    """The fix must not disarm the lens: 25% buys is a rout, not timing."""
    cand = _healthy_candidate()
    cand.metrics.txns_1h_buys = 250
    cand.metrics.txns_1h_sells = 750
    assert _panel_op(cand, "LENS-FISHER").stance == "VETO"


def test_moderate_sell_pressure_is_timing_not_ruin():
    """A veto in this panel means unrecoverable. Momentum reverses."""
    cand = _healthy_candidate()
    # 35% buys: a 15-point deviation, so past the effect floor and clearly
    # significant, but short of the 30/70 rout that justifies a veto.
    cand.metrics.txns_1h_buys = 350
    cand.metrics.txns_1h_sells = 650
    assert _panel_op(cand, "LENS-FISHER").stance == "CAUTION"


# ============================== convergence needs independent evidence (b) --

def test_one_fact_cannot_convict_a_token_twice():
    """Buterin and Nakamoto both caution off `liquidity_locked_pct < 80`.

    So a single fact -- "79% locked" -- produced two cautions, and the
    convergence rule, whose entire justification is that INDEPENDENT lenses
    agreed, blocked the token as though two separate defects had been found.
    That one collision accounted for 125 rejections in the healthy population.
    """
    from architecture.knowledge.panel import CognitivePanel
    cand = _healthy_candidate()
    cand.security.liquidity_locked_pct = 79.0

    verdict = CognitivePanel().deliberate(cand, now=NOW)
    lock_cautions = [o for o in verdict.opinions
                     if o.stance == "CAUTION" and "liquidity_lock" in (o.evidence or ())]
    assert len(lock_cautions) >= 2, \
        "fixture no longer produces the collision this test exists for"

    bases = set()
    for o in verdict.opinions:
        if o.stance == "CAUTION":
            bases.update(o.evidence or (f"lens:{o.lens_id}",))
    assert "liquidity_lock" in bases
    assert len(bases) < 2 or verdict.verdict == "CONVERGENT_CAUTION", \
        "distinct evidence must drive the verdict, not opinion count"

    # With the lock as the ONLY finding, two lenses reading it must not block.
    only_lock = [o for o in verdict.opinions if o.stance in ("CAUTION", "VETO")]
    if all("liquidity_lock" in (o.evidence or ()) for o in only_lock):
        assert not verdict.is_blocking, \
            "one fact, read twice, still blocked the token"


def test_two_genuinely_different_facts_still_block():
    """The rule must not be disarmed -- only made honest."""
    from architecture.knowledge.panel import CognitivePanel
    cand = _healthy_candidate()
    cand.security.liquidity_locked_pct = 70.0            # fact 1
    cand.security.top10_holder_concentration_pct = 55.0  # fact 2
    verdict = CognitivePanel().deliberate(cand, now=NOW)
    assert verdict.is_blocking, \
        f"two independent findings failed to block: {verdict.verdict}"


def test_an_untagged_lens_is_counted_on_its_own_identity():
    """Failing to declare a basis must never make the panel MORE permissive."""
    from architecture.knowledge.panel import CognitivePanel, _op

    def a(cand, ctx):
        return _op("LENS-GODEL", "INCOMPLETE-01", "CAUTION", "alpha")

    def b(cand, ctx):
        return _op("LENS-TALEB", "RUIN-01", "CAUTION", "beta")

    verdict = CognitivePanel(lenses=[("LENS-GODEL", a), ("LENS-TALEB", b)]) \
        .deliberate(_healthy_candidate(), now=NOW)
    assert verdict.verdict == "CONVERGENT_CAUTION"
    assert verdict.is_blocking


# ===================== extreme cases must be fatal on their own evidence (b) --

def test_a_market_with_no_sellers_is_vetoed_by_the_lens_that_sees_it():
    """99% buys was caught only because Fisher happened to caution too.

    That was luck: Fisher's caution was about the same trade counts, so the
    "convergence" was one fact counted twice. Mitnick must reach the verdict
    on its own evidence.
    """
    cand = _healthy_candidate()
    cand.metrics.txns_1h_buys = 900
    cand.metrics.txns_1h_sells = 8
    assert _panel_op(cand, "LENS-MITNICK").stance == "VETO"


def test_wash_trading_volume_is_vetoed_by_the_lens_that_sees_it():
    """667x daily turnover recycles the entire pool every two minutes."""
    cand = _healthy_candidate()
    cand.metrics.liquidity_usd = 60_000.0
    cand.metrics.volume_24h = 40_000_000.0
    assert _panel_op(cand, "LENS-KEYNES").stance == "VETO"


def test_ordinary_churn_is_not_promoted_to_a_veto():
    """45x turnover is churny; it is not wash trading. Keep the gradation."""
    cand = _healthy_candidate()
    cand.metrics.volume_24h = cand.metrics.liquidity_usd * 45.0
    assert _panel_op(cand, "LENS-KEYNES").stance == "CAUTION"


def test_strong_but_credible_buying_is_not_promoted_to_a_veto():
    cand = _healthy_candidate()
    cand.metrics.txns_1h_buys = 930
    cand.metrics.txns_1h_sells = 70          # 93%: a sign, not yet a certainty
    assert _panel_op(cand, "LENS-MITNICK").stance == "CAUTION"


# ============ fields the collectors return that no lens read (Wave-33c) --

def test_a_valuation_the_pool_cannot_honour_is_caught():
    """`fdv_usd` was collected from both providers, stored, and read by nobody.

    Not the scorer, not a single lens. That left the panel blind to the most
    ordinary memecoin trap there is: an $800-to-1 headline valuation resting on
    a pool that could pay out 0.1% of it. Such a token scored 90 and reached
    ENTER.
    """
    cand = _healthy_candidate()
    cand.metrics.fdv_usd = 200_000_000.0      # 800x the 250k pool
    assert _panel_op(cand, "LENS-MISES").stance == "VETO"


def test_a_normal_valuation_multiple_is_not_punished():
    """FDV legitimately exceeds pool depth by a wide margin on healthy tokens."""
    cand = _healthy_candidate()
    cand.metrics.fdv_usd = cand.metrics.liquidity_usd * 40.0
    assert _panel_op(cand, "LENS-MISES").stance == "APPROVE"


def test_the_round_trip_tax_load_is_measured_against_the_take_profit():
    """`buy_tax_pct` was read by no lens, and Adams stops at slippage.

    So a 24%/24% token cleared every tax check -- each side sits below the 25%
    sell-tax veto -- while needing a +161% move to net the +50% the exit rules
    actually take profit at.
    """
    cand = _healthy_candidate()
    cand.security.buy_tax_pct = 24.0
    cand.security.sell_tax_pct = 24.0
    op = _panel_op(cand, "LENS-ARCHIMEDES")
    assert op.stance == "VETO"
    assert op.metric is not None and op.metric > 150.0


def test_a_cheap_round_trip_is_approved():
    cand = _healthy_candidate()
    cand.security.buy_tax_pct = 0.0
    cand.security.sell_tax_pct = 0.0
    op = _panel_op(cand, "LENS-ARCHIMEDES")
    assert op.stance == "APPROVE"
    # Needs essentially just the take-profit itself, plus a little slippage.
    assert op.metric == pytest.approx(TAKE_PROFIT_PCT * 100.0, abs=1.0)


def test_the_two_activated_members_declare_independent_evidence():
    """New lenses must not collide with an existing basis.

    Two lenses reading one fact is what made a single 79%-locked reading block
    a token twice. A new lens sharing an existing evidence tag would quietly
    recreate that.
    """
    from architecture.knowledge.panel import CognitivePanel
    cand = _healthy_candidate()
    verdict = CognitivePanel().deliberate(cand, now=NOW)
    by_id = {o.lens_id: o for o in verdict.opinions}
    assert by_id["LENS-MISES"].evidence == ("fdv_backing",)
    assert by_id["LENS-ARCHIMEDES"].evidence == ("round_trip_cost",)

    for other, op in by_id.items():
        if other in ("LENS-MISES", "LENS-ARCHIMEDES"):
            continue
        assert "fdv_backing" not in (op.evidence or ())
        assert "round_trip_cost" not in (op.evidence or ())


def test_activated_members_are_active_in_the_roster_too():
    """Code and YAML must agree, or the roster is advertising again."""
    from architecture.knowledge.teams import load_structure, validate
    structure = load_structure()
    for name, lens_id in (("Ludwig von Mises", "LENS-MISES"),
                          ("Archimedes", "LENS-ARCHIMEDES")):
        member = next(m for t in structure.teams for m in t.members
                      if m.name == name)
        assert member.status == "ACTIVE"
        assert member.lens_id == lens_id
    assert validate() == []


# ================== uncertainty must shrink the bet (Wave-33d) --

def _calibrated(wins: int, n: int, score: float = 90.0):
    """Build the canonical guarded descriptive band used by the sizing lens."""
    from architecture.learning.calibration import (
        BandResult, CalibrationReport, MIN_N_PER_BAND, MIN_POSITIVES)
    from research.baseline_stats import wilson_ci

    usable = n >= MIN_N_PER_BAND and wins >= MIN_POSITIVES
    lo, hi = wilson_ci(wins, n) if n else (None, None)
    band = BandResult(
        band="80-100", lower=80.0, upper=100.001, n=n, positives=wins,
        rate=(wins / n) if n else None, ci_low=lo, ci_high=hi,
        verdict="DESCRIPTIVE_OK" if usable else "INSUFFICIENT_DATA",
        reason=None if usable else "pre-registered sample guard",
    )
    return CalibrationReport(
        generated_utc="2026-08-19T00:00:00Z", horizon="24h",
        event_class="+50%", total_predictions=n, joined_pairs=n,
        bands=[band], verdict="DESCRIPTIVE_OK" if usable else "INSUFFICIENT_DATA",
    )


def _thorp(report, score: float = 90.0, frac: float = 1.0):
    from architecture.knowledge.team_lenses import lens_thorp_kelly
    ex = type("Ex", (), {"realizable_fraction": frac})()
    rep = type("Rep", (), {"opportunity_score": score})()
    return lens_thorp_kelly(None, {"score_report": rep, "exitability": ex,
                                   "calibration": report})


def test_kelly_abstains_on_five_samples():
    """The canonical 200-sample guard blocks a point estimate from five rows."""
    op = _thorp(_calibrated(3, 5))
    assert op.stance == "ABSTAIN"


def test_thin_evidence_never_becomes_a_position_size():
    from architecture.learning.calibration import MIN_N_PER_BAND
    for n in (5, 20, 50, MIN_N_PER_BAND - 1):
        op = _thorp(_calibrated(round(0.6 * n), n))
        assert op.stance == "ABSTAIN", f"n={n} produced a sizing vote"


def test_a_genuinely_losing_rate_is_still_fatal():
    op = _thorp(_calibrated(20, 200))          # 10% win rate, guards earned
    assert op.stance == "VETO"


def test_the_recommended_size_converges_as_evidence_accumulates():
    """The Wilson lower-bound penalty fades as evidence accumulates."""
    sizes = []
    for n in (200, 400, 800):
        op = _thorp(_calibrated(round(0.6 * n), n))
        assert op.stance == "APPROVE"
        sizes.append(op.metric)
    assert sizes == sorted(sizes), "more evidence must not mean a smaller bet"
    point_kelly = 0.6 / STOP_LOSS_PCT - 0.4 / TAKE_PROFIT_PCT
    assert sizes[-1] < min(point_kelly, 1.0) * 0.25


def test_supply_overhang_is_read_at_last():
    """`market_cap_usd` was the other collected-but-unread field.

    A buyer at 10% circulating holds a claim that 9x the traded supply can be
    printed against, on the same pool.
    """
    cand = _healthy_candidate()
    cand.metrics.fdv_usd = 20_000_000.0
    cand.metrics.market_cap_usd = 2_000_000.0        # 10% circulating
    assert _panel_op(cand, "LENS-NOETHER").stance == "CAUTION"


def test_a_settled_supply_is_not_flagged():
    cand = _healthy_candidate()
    cand.metrics.fdv_usd = 3_000_000.0
    cand.metrics.market_cap_usd = 2_900_000.0        # 97% circulating
    assert _panel_op(cand, "LENS-NOETHER").stance == "APPROVE"


def test_dilution_alone_never_blocks_a_token():
    """Vesting is a schedule, not a honeypot: size down, do not refuse.

    The overhang must be isolated to test it. A first draft used a $50M FDV on
    a $250k pool, which is also 200x liquidity, so Mises cautioned too and the
    token blocked on convergence -- correctly, because those are two different
    facts (supply not yet issued vs. a pool that cannot honour the notional),
    and a token can have either without the other. Keep FDV within Mises'
    range so only the dilution is under test.
    """
    from architecture.knowledge.panel import CognitivePanel
    cand = _healthy_candidate()
    cand.metrics.fdv_usd = cand.metrics.liquidity_usd * 20.0   # 20x: fine
    cand.metrics.market_cap_usd = cand.metrics.fdv_usd * 0.02  # 2% circulating
    verdict = CognitivePanel().deliberate(cand, now=NOW)
    assert _panel_op(cand, "LENS-NOETHER").stance == "CAUTION"
    assert not verdict.is_blocking


def test_dilution_and_an_unbacked_valuation_are_two_facts_not_one():
    """Both cautions together SHOULD block -- they are independent findings."""
    from architecture.knowledge.panel import CognitivePanel
    cand = _healthy_candidate()
    cand.metrics.fdv_usd = 50_000_000.0                # 200x the pool
    cand.metrics.market_cap_usd = 1_000_000.0          # and 2% circulating
    verdict = CognitivePanel().deliberate(cand, now=NOW)
    assert verdict.is_blocking
    assert verdict.verdict == "CONVERGENT_CAUTION"


def test_impossible_supply_numbers_are_reported_as_bad_data():
    """Circulating cannot exceed total; that is an accounting fault."""
    cand = _healthy_candidate()
    cand.metrics.fdv_usd = 3_000_000.0
    cand.metrics.market_cap_usd = 4_000_000.0
    op = _panel_op(cand, "LENS-NOETHER")
    assert op.stance == "CAUTION"
    assert "ناسازگار" in op.reason


def test_the_third_activation_also_declares_independent_evidence():
    from architecture.knowledge.panel import CognitivePanel
    verdict = CognitivePanel().deliberate(_healthy_candidate(), now=NOW)
    by_id = {o.lens_id: o for o in verdict.opinions}
    assert by_id["LENS-NOETHER"].evidence == ("supply_overhang",)
    for other, op in by_id.items():
        if other != "LENS-NOETHER":
            assert "supply_overhang" not in (op.evidence or ())
