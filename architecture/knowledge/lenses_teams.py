#!/usr/bin/env python3
"""Lens data cards for the 19 team members who had none (Wave-31).

Why a second card module
------------------------
`lenses.py` holds the original 30 pilot cards. Team assignment in
`config/council_teams.yaml` gave operational duties to 19 further thinkers
from the 100-registry who had no card at all -- so they could not vote, and a
duty nobody can execute is the exact decoration this project keeps removing.

Same constitutional rules as the pilot cards:
  - DATA CARDS ONLY. A lens models a published principle, never a persona.
  - No invented quotations, no simulated private opinion.
  - Every principle carries a citation_ref to a real, checkable publication.
  - Documented failure modes are mandatory: a lens that cannot say where it
    breaks is being sold, not reasoned with.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .contracts import TrustClass, KnowledgeDomain, ExpertLensCard


def _sha(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()


def _card(lens_id: str, identity: str, domain: KnowledgeDomain,
          corpus: list[str], principles: list[dict[str, str]],
          models: list[str], failures: list[str], strengths: list[str],
          blind_spots: list[str], biases: list[str],
          applications: list[str]) -> ExpertLensCard:
    return ExpertLensCard(
        lens_id=lens_id, identity=identity, domain=domain,
        public_source_corpus=corpus, verified_principles=principles,
        mental_models=models, historical_evidence=corpus,
        documented_failures=failures, strengths=strengths,
        blind_spots=blind_spots, biases=biases,
        ahos_applications=applications,
        citations=[{"citation_ref": p["citation_ref"], "title": p["title"]}
                   for p in principles],
        provenance=_sha({"id": lens_id, "corpus": corpus}),
        trust_class=TrustClass.EXPERT_INTERPRETATION)


TEAM_LENS_REGISTRY: dict[str, ExpertLensCard] = {

    # ---------------------------------------------------------- SURVIVAL --
    "LENS-POINCARE": _card(
        "LENS-POINCARE", "Henri Poincaré (1854–1912)", KnowledgeDomain.COMPLEX_SYSTEMS,
        ["Sur le problème des trois corps et les équations de la dynamique (1890)",
         "Science et Méthode (1908)"],
        [{"principle_id": "CHAOS-01", "title": "Sensitive Dependence on Initial Conditions",
          "formula_or_rule": "small differences in initial state produce large divergence in outcome",
          "citation_ref": "SRC-POINCARE-1890:p270"}],
        ["Deterministic chaos", "Phase-space stability"],
        ["Says nothing about direction of divergence, only its magnitude",
         "Requires a dynamical model; raw snapshots cannot show sensitivity"],
        ["Detects verdicts that rest on a knife edge"],
        ["Cannot distinguish chaotic from merely noisy"],
        ["Over-attributes structure to randomness"],
        ["Flags candidates whose verdict flips under small input perturbation"]),

    "LENS-BOX": _card(
        "LENS-BOX", "George Box (1919–2013)", KnowledgeDomain.MATHEMATICS,
        ["Science and Statistics, JASA (1976)",
         "Empirical Model-Building and Response Surfaces (1987)"],
        [{"principle_id": "BOX-01", "title": "All Models Are Wrong, But Some Are Useful",
          "formula_or_rule": "judge a model by its usefulness within a stated range, never by its truth",
          "citation_ref": "SRC-BOX-1976:p792"}],
        ["Model adequacy", "Range of validity"],
        ["Cannot itself supply the missing model",
         "Usefulness is domain-specific and not directly measurable"],
        ["Names the boundary beyond which our own score means nothing"],
        ["Offers no replacement when the model fails"],
        ["Can be used to excuse any model whatsoever"],
        ["Refuses scores computed outside the regime they were calibrated in"]),

    # --------------------------------------------------------- ADVERSARY --
    "LENS-ANDERSON": _card(
        "LENS-ANDERSON", "Ross Anderson (1956–2024)", KnowledgeDomain.CYBERSECURITY,
        ["Why Information Security is Hard — An Economic Perspective (2001)",
         "Security Engineering (2001, 2008, 2020)"],
        [{"principle_id": "ECON-SEC-01", "title": "Security Fails Where Incentives Are Misaligned",
          "formula_or_rule": "the party able to prevent the loss is often not the party who bears it",
          "citation_ref": "SRC-ANDERSON-2001:acsac"}],
        ["Incentive analysis", "Liability allocation"],
        ["Incentives are inferred, not observed; inference can be wrong",
         "Says nothing about technically flawless but predatory designs"],
        ["Asks who profits from a structure rather than whether it is legal"],
        ["Cannot see off-chain agreements"],
        ["Assumes economic rationality of attackers"],
        ["Scores structures where the deployer's payoff conflicts with holders"]),

    "LENS-KREBS": _card(
        "LENS-KREBS", "Brian Krebs (1972–present)", KnowledgeDomain.ON_CHAIN_ANALYTICS,
        ["Spam Nation (2014)", "KrebsOnSecurity investigative corpus"],
        [{"principle_id": "KREBS-01", "title": "Follow the Money and the Repeat Offender",
          "formula_or_rule": "criminal infrastructure is reused; prior offence is the strongest single predictor",
          "citation_ref": "SRC-KREBS-2014:p8"}],
        ["Recidivism", "Infrastructure reuse"],
        ["Absence of prior record is not evidence of good faith — a first "
         "offence has no history",
         "Address reuse is trivially avoidable by a competent actor"],
        ["Prior rugs by the same deployer are the highest-value signal available"],
        ["Blind to fresh wallets"],
        ["Over-weights known bad actors relative to unknown ones"],
        ["Weights deployer_past_rug_count as a near-decisive signal"]),

    "LENS-MITNICK": _card(
        "LENS-MITNICK", "Kevin Mitnick (1963–2023)", KnowledgeDomain.CYBERSECURITY,
        ["The Art of Deception (2002)", "The Art of Intrusion (2005)"],
        [{"principle_id": "SOCENG-01", "title": "The Human Is the Softest Target",
          "formula_or_rule": "urgency and social proof bypass deliberation more reliably than technical exploits",
          "citation_ref": "SRC-MITNICK-2002:p4"}],
        ["Manufactured urgency", "Fabricated social proof"],
        ["Genuine excitement and manufactured excitement can look identical "
         "in aggregate metrics",
         "Cannot read the content of the hype, only its shape"],
        ["Detects the buy-pressure profile typical of coordinated promotion"],
        ["No access to the social channels themselves"],
        ["Treats sharp enthusiasm as suspicious by default"],
        ["Flags extreme buy/sell asymmetry paired with a very young pair"]),

    # --------------------------------------------------------- LIQUIDITY --
    "LENS-ADAMS": _card(
        "LENS-ADAMS", "Hayden Adams (1993–present)", KnowledgeDomain.MARKET_MICROSTRUCTURE,
        ["Uniswap Whitepaper (2018)", "Uniswap v2 Core (2020)"],
        [{"principle_id": "AMM-01", "title": "Constant Product Market Maker",
          "formula_or_rule": "x*y=k; price impact of trade size dx is dx/(x+dx)",
          "citation_ref": "SRC-ADAMS-2018:uniswap"}],
        ["Constant-product invariant", "Price impact as a function of pool share"],
        ["Assumes a single pool; routed trades across venues differ",
         "Ignores concentrated liquidity (v3) and dynamic fees"],
        ["Computes exact slippage from pool depth and order size"],
        ["Cannot see liquidity outside the observed pair"],
        ["Underestimates impact when liquidity is concentrated in a range"],
        ["Derives realistic exit cost for the position size being proposed"]),

    "LENS-KEYNES": _card(
        "LENS-KEYNES", "John Maynard Keynes (1883–1946)", KnowledgeDomain.BEHAVIORAL_ECONOMICS,
        ["The General Theory of Employment, Interest and Money (1936)"],
        [{"principle_id": "LIQPREF-01", "title": "Liquidity Preference",
          "formula_or_rule": "the premium demanded for holding an illiquid asset rises non-linearly as exit certainty falls",
          "citation_ref": "SRC-KEYNES-1936:ch13"}],
        ["Liquidity premium", "Animal spirits"],
        ["Written for macro-level money markets, not single-pool DEX pairs",
         "Gives no numeric threshold — the mapping onto turnover is ours"],
        ["Prices the cost of being unable to leave quickly"],
        ["Silent on the mechanics of any specific venue"],
        ["Assumes participants are broadly rational in aggregate"],
        ["Compares pool depth against realistic daily turnover"]),

    # ---------------------------------------------------------- EVIDENCE --
    "LENS-NEYMAN": _card(
        "LENS-NEYMAN", "Jerzy Neyman (1894–1981)", KnowledgeDomain.MATHEMATICS,
        ["Outline of a Theory of Statistical Estimation (1937)",
         "On the Problem of the Most Efficient Tests (1933, with E. Pearson)"],
        [{"principle_id": "NEYMAN-01", "title": "Type I / Type II Error Trade-off",
          "formula_or_rule": "reducing false positives raises false negatives; the cost ratio must be chosen, not discovered",
          "citation_ref": "SRC-NEYMAN-1937:p348"}],
        ["Confidence intervals", "Error-cost asymmetry"],
        ["The cost ratio is a value judgement no statistic can supply",
         "Frequentist intervals say nothing about this particular token"],
        ["Makes the asymmetry explicit: a missed scam costs more than a missed gain"],
        ["Cannot price the two errors on its own"],
        ["Encourages treating 95% as a natural constant"],
        ["Asserts the deliberate asymmetry between rejecting good and accepting bad"]),

    "LENS-TAO": _card(
        "LENS-TAO", "Terence Tao (1975–present)", KnowledgeDomain.MATHEMATICS,
        ["Compressed Sensing (with Candès, Romberg, 2006)",
         "Additive Combinatorics (2006)"],
        [{"principle_id": "SPARSE-01", "title": "Sparse Signal Recovery",
          "formula_or_rule": "a sparse signal is recoverable from far fewer samples than Nyquist requires, if sparsity holds",
          "citation_ref": "SRC-TAO-2006:ieee"}],
        ["Sparsity", "Sample complexity"],
        ["Recovery guarantees require the sparsity assumption to actually hold",
         "Says nothing when the underlying signal is dense noise"],
        ["Establishes how few observations can still support an inference"],
        ["Cannot verify its own sparsity precondition from the data"],
        ["Optimistic about what little data can prove"],
        ["Sets the minimum observation count before momentum claims are allowed"]),

    # ------------------------------------------------------------ TIMING --
    "LENS-RIEMANN": _card(
        "LENS-RIEMANN", "Bernhard Riemann (1826–1866)", KnowledgeDomain.MATHEMATICS,
        ["Über die Hypothesen welche der Geometrie zu Grunde liegen (1854)"],
        [{"principle_id": "RIEMANN-01", "title": "Curved Multi-Dimensional Manifolds",
          "formula_or_rule": "a surface's geometry is intrinsic; distance must be measured within the manifold, not in the embedding",
          "citation_ref": "SRC-RIEMANN-1854:p133"}],
        ["Intrinsic geometry", "Joint rather than marginal structure"],
        ["Purely geometric; supplies no probability",
         "Requires the dimensions to be commensurable, which price/depth/time are not naturally"],
        ["Judges price, depth and time jointly instead of one axis at a time"],
        ["No notion of causality between the axes"],
        ["Can impose smooth structure where the data is discrete"],
        ["Refuses candidates that look acceptable on each axis but not jointly"]),

    "LENS-TVERSKY": _card(
        "LENS-TVERSKY", "Amos Tversky (1937–1996)", KnowledgeDomain.BEHAVIORAL_ECONOMICS,
        ["Judgment under Uncertainty: Heuristics and Biases (1974, with Kahneman)"],
        [{"principle_id": "ANCHOR-01", "title": "Anchoring and Adjustment",
          "formula_or_rule": "estimates stay biased toward an initial reference even when it is known to be arbitrary",
          "citation_ref": "SRC-TVERSKY-1974:p1128"}],
        ["Anchoring", "Availability heuristic"],
        ["Describes human error, not market state — the bias corrected is ours",
         "Cannot be measured from token data alone"],
        ["Stops entry price from dominating the exit decision"],
        ["Not a signal about the token"],
        ["Risks discarding genuinely informative reference points"],
        ["Forces exit reasoning to use current liquidity, not the entry anchor"]),

    "LENS-SIMON": _card(
        "LENS-SIMON", "Herbert Simon (1916–2001)", KnowledgeDomain.BEHAVIORAL_ECONOMICS,
        ["A Behavioral Model of Rational Choice (1955)",
         "Administrative Behavior (1947)"],
        [{"principle_id": "SATISFICE-01", "title": "Bounded Rationality and Satisficing",
          "formula_or_rule": "with limited information, seek an adequate option rather than an optimal one",
          "citation_ref": "SRC-SIMON-1955:p99"}],
        ["Satisficing", "Bounded rationality"],
        ["Adequacy thresholds are chosen, not derived",
         "Can stop searching too early in a genuinely rich environment"],
        ["Prevents false precision when the evidence cannot support it"],
        ["No guidance on where to set the bar"],
        ["Biased toward accepting the first acceptable option"],
        ["Blocks fine-grained ranking of candidates whose data quality is coarse"]),

    "LENS-HAYEK": _card(
        "LENS-HAYEK", "Friedrich Hayek (1899–1992)", KnowledgeDomain.MARKET_MICROSTRUCTURE,
        ["The Use of Knowledge in Society, AER (1945)"],
        [{"principle_id": "HAYEK-01", "title": "Price as Distributed Knowledge",
          "formula_or_rule": "price aggregates information no single participant holds",
          "citation_ref": "SRC-HAYEK-1945:p519"}],
        ["Distributed knowledge", "Spontaneous order"],
        ["Requires many independent participants; a handful of wallets is not a market",
         "Manipulated prices aggregate the manipulator's intent, not knowledge"],
        ["Asks whether the price reflects a real crowd or a few actors"],
        ["Cannot detect manipulation on its own"],
        ["Tends to treat market prices as informative by default"],
        ["Discounts price signals when participant count is too small to aggregate"]),

    "LENS-NEWTON": _card(
        "LENS-NEWTON", "Isaac Newton (1643–1727)", KnowledgeDomain.MATHEMATICS,
        ["Philosophiae Naturalis Principia Mathematica (1687)",
         "Method of Fluxions (1671)"],
        [{"principle_id": "NEWTON-01", "title": "Rate of Change and Second Derivative",
          "formula_or_rule": "velocity is the first derivative of position; acceleration the second",
          "citation_ref": "SRC-NEWTON-1687:p1"}],
        ["Derivatives", "Momentum and its decay"],
        ["Extrapolating a derivative beyond its measurement window is unsound",
         "Discrete samples make second derivatives extremely noisy"],
        ["Separates a token still accelerating from one already decelerating"],
        ["No notion of a driving cause"],
        ["Extrapolates smoothly through what are in fact jumps"],
        ["Compares 5m/1h/24h windows to test whether momentum is fading"]),

    # ------------------------------------------------------------ SIZING --
    "LENS-THORP": _card(
        "LENS-THORP", "Edward O. Thorp (1932–present)", KnowledgeDomain.MATHEMATICS,
        ["Beat the Dealer (1962)",
         "The Kelly Criterion in Blackjack, Sports Betting and the Stock Market (2006)"],
        [{"principle_id": "KELLY-01", "title": "Kelly Criterion for Bet Sizing",
          "formula_or_rule": "f* = (bp - q) / b, where p is win probability, q=1-p, b the win/loss ratio",
          "citation_ref": "SRC-THORP-2006:p9"}],
        ["Kelly fraction", "Fractional Kelly for parameter uncertainty"],
        ["Full Kelly is brutally sensitive to an over-estimated p — the standard "
         "remedy is a fraction of it",
         "Assumes repeated independent bets and a known edge; neither strictly holds here",
         "With no calibrated probability, Kelly cannot be computed at all"],
        ["Gives the only principled answer to 'how much' that exists"],
        ["Requires a probability estimate we may not have"],
        ["Punishes over-confidence far more harshly than under-confidence"],
        ["Sizes positions from calibrated historical win rates, quarter-Kelly"]),

    "LENS-EINSTEIN": _card(
        "LENS-EINSTEIN", "Albert Einstein (1879–1955)", KnowledgeDomain.MATHEMATICS,
        ["Zur Elektrodynamik bewegter Körper (1905)"],
        [{"principle_id": "FRAME-01", "title": "Relativity of Reference Frames",
          "formula_or_rule": "a measurement is meaningless without stating the frame it was taken in",
          "citation_ref": "SRC-EINSTEIN-1905:p891"}],
        ["Reference frames", "Invariance under change of observer"],
        ["An analogy when applied to finance, not a physical law",
         "Cannot itself decide which frame is the right one"],
        ["Insists a position size be stated relative to bankroll, not in isolation"],
        ["No independent content beyond the reframing"],
        ["Risks over-generalising a physical principle"],
        ["Expresses risk as a fraction of total bankroll, never as a raw dollar figure"]),

    "LENS-FEYNMAN": _card(
        "LENS-FEYNMAN", "Richard Feynman (1918–1988)", KnowledgeDomain.MATHEMATICS,
        ["Cargo Cult Science, Caltech commencement address (1974)",
         "The Feynman Lectures on Physics (1964)"],
        [{"principle_id": "FEYNMAN-01", "title": "Cargo Cult Science",
          "formula_or_rule": "the first principle is that you must not fool yourself, and you are the easiest person to fool",
          "citation_ref": "SRC-FEYNMAN-1974:caltech"}],
        ["First-principles derivation", "Self-deception audit"],
        ["A discipline rather than a computation — it produces no number",
         "Can be invoked to dismiss any inconvenient result"],
        ["Demands each figure be derivable from evidence, not inherited from a default"],
        ["Provides no measurement of its own"],
        ["Sceptical of results even when they are correct"],
        ["Rejects position sizes not traceable to a measured input"]),

    # ---------------------------------------------------------- LEARNING --
    "LENS-DEMING": _card(
        "LENS-DEMING", "William Edwards Deming (1900–1993)", KnowledgeDomain.MATHEMATICS,
        ["Out of the Crisis (1986)", "The New Economics (1993)"],
        [{"principle_id": "SPC-01", "title": "Common Cause versus Special Cause Variation",
          "formula_or_rule": "reacting to common-cause variation as if it were special makes the process worse",
          "citation_ref": "SRC-DEMING-1986:p309"}],
        ["Statistical process control", "PDCA improvement cycle"],
        ["Needs a stable process and enough history; a young system has neither",
         "Cannot distinguish the two causes without sufficient samples"],
        ["Stops the system from over-fitting to individual losing trades"],
        ["Requires history the system may not yet have"],
        ["Conservative about changing anything"],
        ["Guards the self-review loop against tampering with noise"]),

    "LENS-DRUCKER": _card(
        "LENS-DRUCKER", "Peter Drucker (1909–2005)", KnowledgeDomain.MATHEMATICS,
        ["The Practice of Management (1954)",
         "Management by Objectives framework"],
        [{"principle_id": "DRUCKER-01", "title": "What Gets Measured Gets Managed",
          "formula_or_rule": "an objective without a measurement is an intention",
          "citation_ref": "SRC-DRUCKER-1954:p121"}],
        ["Management by objectives", "Measurement discipline"],
        ["Encourages optimising the measurable at the expense of the important",
         "Not a market principle at all — it governs our own process"],
        ["Forces every claim the system makes to carry a number"],
        ["Says nothing about which metric matters"],
        ["Can drive metric-gaming"],
        ["Requires each lens opinion to attach a metric where one exists"]),

    # ------------------------------------------- Wave-33c: closing blind spots --
    # These two were ADVISORY -- named duties nobody could execute -- and each
    # maps onto a field the collectors return that NO lens was reading.

    "LENS-MISES": _card(
        "LENS-MISES", "Ludwig von Mises (1881–1973)", KnowledgeDomain.MARKET_MICROSTRUCTURE,
        ["Economic Calculation in the Socialist Commonwealth (1920)",
         "Human Action: A Treatise on Economics (1949)"],
        [{"principle_id": "CALC-01", "title": "The Economic Calculation Problem",
          "formula_or_rule": "a price that does not arise from real exchange conveys no information "
                             "and cannot support rational calculation",
          "citation_ref": "SRC-MISES-1920:p105"}],
        ["Praxeology", "Prices as products of actual exchange"],
        ["Says nothing about how far a fictitious valuation can still travel upward",
         "Cannot time the correction it implies",
         "Treats thin markets and manipulated markets identically"],
        ["Separates notional valuation from the depth that would have to honour it"],
        ["Offers no view on momentum or timing"],
        ["Deeply sceptical of any valuation not settled in a real trade"],
        ["Compares fully diluted valuation against the liquidity able to pay it out"]),

    "LENS-NOETHER": _card(
        "LENS-NOETHER", "Emmy Noether (1882–1935)", KnowledgeDomain.MATHEMATICS,
        ["Invariante Variationsprobleme (1918)",
         "Noether's first theorem: symmetries and conservation laws"],
        [{"principle_id": "INVAR-01", "title": "Conserved Quantities Under Symmetry",
          "formula_or_rule": "identify what the system holds invariant; a quantity that "
                             "silently changes is where the accounting breaks",
          "citation_ref": "SRC-NOETHER-1918:sec1"}],
        ["Invariants under transformation", "Conservation laws from symmetry"],
        ["Says nothing about when an unlock actually occurs, only that it can",
         "A low circulating fraction is normal for a legitimately vesting project",
         "Cannot see vesting schedules, only the ratio at this instant"],
        ["Names the quantity a holder assumes is fixed and shows it is not"],
        ["Silent on the timing or the recipient of any release"],
        ["Treats all future issuance as equally threatening"],
        ["Compares circulating market cap against fully diluted supply"]),

    "LENS-ARCHIMEDES": _card(
        "LENS-ARCHIMEDES", "Archimedes (c. 287–212 BC)", KnowledgeDomain.MATHEMATICS,
        ["On the Equilibrium of Planes, Book I",
         "On Floating Bodies"],
        [{"principle_id": "LEVER-01", "title": "Law of the Lever",
          "formula_or_rule": "a lever multiplies force only in proportion to the fulcrum it rests on; "
                             "the load must be measured against the support, never on its own",
          "citation_ref": "SRC-ARCHIMEDES-EQP:bk1.prop6"}],
        ["Mechanical advantage", "Equilibrium about a fulcrum"],
        ["A purely static principle: says nothing about how costs evolve over time",
         "Assumes the frictions it is given are complete and correctly measured"],
        ["States the total load a position must lift before it breaks even"],
        ["Blind to any cost not passed to it"],
        ["Treats all frictions as equivalent regardless of cause"],
        ["Sums buy tax, sell tax and round-trip slippage into the move required to profit"]),
}
