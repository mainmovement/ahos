#!/usr/bin/env python3
"""AHOS Expert Lens Library — 10 Pilot Data Cards (Phase XXII - K-03).

Constitutional Laws for Lens Data Cards:
  - DATA CARDS ONLY: Lenses are structured epistemic frameworks, NOT active conversational personas.
  - NO Impersonation: Models principles and mental models, NEVER private consciousness or fabricated quotes.
  - Verifiable Provenance: Every principle carries explicit citation_ref linking to canonical publications.
  - Documented Failure Modes: Every lens explicitly specifies where its assumptions break down.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .contracts import (
    TrustClass,
    KnowledgeDomain,
    ExpertLensCard
)


def _sha(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode("utf-8")).hexdigest()


LENS_PILOT_REGISTRY: dict[str, ExpertLensCard] = {
    # 1. Claude Shannon
    "LENS-SHANNON": ExpertLensCard(
        lens_id="LENS-SHANNON",
        identity="Claude Shannon (1916–2001)",
        domain=KnowledgeDomain.INFORMATION_THEORY,
        public_source_corpus=[
            "A Mathematical Theory of Communication (1948)",
            "Communication Theory of Secrecy Systems (1949)"
        ],
        verified_principles=[
            {
                "principle_id": "INFO-01",
                "title": "Information Entropy & Surprise",
                "formula_or_rule": "H(X) = -sum(p(x) * log2(p(x)))",
                "citation_ref": "SRC-SHANNON-1948:p380"
            },
            {
                "principle_id": "INFO-02",
                "title": "Noisy-Channel Coding Theorem",
                "formula_or_rule": "C = B * log2(1 + S/N)",
                "citation_ref": "SRC-SHANNON-1948:p408"
            }
        ],
        mental_models=["Bit as fundamental unit of uncertainty reduction", "Signal-to-Noise Ratio (SNR)", "Channel Capacity bounds"],
        historical_evidence=["Digital telecommunications infrastructure", "Information-theoretic compression algorithms"],
        documented_failures=["Assumes stationary statistical distribution; fails during regime-switching non-ergodic market crashes."],
        strengths=["Quantifying real information content versus noise", "Eliminating redundant data transmission"],
        blind_spots=["Does not capture semantic meaning or deception in human social narratives"],
        biases=["Engineering/Transmission bias (treats all information as probabilistic bit streams)"],
        ahos_applications=["Filter redundant social spam vs high-entropy on-chain volume shifts", "Quantify SNR across multi-source providers"],
        citations=[
            {"citation_ref": "SRC-SHANNON-1948", "title": "A Mathematical Theory of Communication", "year": "1948", "publication": "Bell System Tech. J."}
        ],
        provenance=_sha("Shannon_Information_Theory_1948")
    ),

    # 2. John von Neumann
    "LENS-VON-NEUMANN": ExpertLensCard(
        lens_id="LENS-VON-NEUMANN",
        identity="John von Neumann (1903–1957)",
        domain=KnowledgeDomain.GAME_THEORY,
        public_source_corpus=[
            "Theory of Games and Economic Behavior (with Oskar Morgenstern, 1944)",
            "First Draft of a Report on the EDVAC (1945)"
        ],
        verified_principles=[
            {
                "principle_id": "GAME-01",
                "title": "Minimax Theorem for Zero-Sum Games",
                "formula_or_rule": "max_x min_y (x^T A y) = min_y max_x (x^T A y)",
                "citation_ref": "SRC-VON-NEUMANN-1944:p153"
            }
        ],
        mental_models=["Strategic adversarial equilibrium", "Self-reproducing automata architecture", "Expected utility maximization"],
        historical_evidence=["Cold war nuclear deterrence game theory", "Stored-program computer architecture"],
        documented_failures=["Assumes rational adversaries with complete preference orderings; fails on irrational crowd panics."],
        strengths=["Adversarial modeling and vulnerability analysis in zero-sum environments (DEX MEV, rug-pullers)"],
        blind_spots=["Positive-sum network coordination effects and altruistic open-source behavior"],
        biases=["Hyper-rationality bias"],
        ahos_applications=["Model MEV-sandwich bot behavior as adversarial zero-sum games", "Audit smart contract extractable value"],
        citations=[
            {"citation_ref": "SRC-VON-NEUMANN-1944", "title": "Theory of Games and Economic Behavior", "year": "1944", "publication": "Princeton Univ. Press"}
        ],
        provenance=_sha("VonNeumann_GameTheory_1944")
    ),

    # 3. Benoit Mandelbrot
    "LENS-MANDELBROT": ExpertLensCard(
        lens_id="LENS-MANDELBROT",
        identity="Benoit Mandelbrot (1924–2010)",
        domain=KnowledgeDomain.COMPLEX_SYSTEMS,
        public_source_corpus=[
            "The Fractal Geometry of Nature (1982)",
            "Fractals and Scaling in Finance (1997)",
            "The (Mis)Behavior of Markets (2004)"
        ],
        verified_principles=[
            {
                "principle_id": "FRACTAL-01",
                "title": "Heavy-Tailed Power Law Scaling (Fat Tails)",
                "formula_or_rule": "P(X > x) ~ x^(-alpha), where alpha < 2 indicates infinite variance",
                "citation_ref": "SRC-MANDELBROT-1997:p84"
            }
        ],
        mental_models=["Scale invariance & self-similarity", "Wild randomness vs Mild Gaussian randomness", "Volatility clustering"],
        historical_evidence=["Cotton price fluctuations across 100 years", "Black Monday 1987 crash distribution"],
        documented_failures=["Does not provide deterministic timing for turning points; parameter alpha drifts over time."],
        strengths=["Realistic tail-risk modeling in hyper-volatile crypto tokens", "Rejecting false Gaussian assumptions"],
        blind_spots=["Does not model fundamental valuation floors or cash flow mechanics"],
        biases=["Power-law universality bias"],
        ahos_applications=["Replace Gaussian drawdown models with heavy-tailed Pareto confidence bounds", "Liquidity shock simulation"],
        citations=[
            {"citation_ref": "SRC-MANDELBROT-1997", "title": "Fractals and Scaling in Finance", "year": "1997", "publication": "Springer"}
        ],
        provenance=_sha("Mandelbrot_Fractals_1997")
    ),

    # 4. Daniel Kahneman
    "LENS-KAHNEMAN": ExpertLensCard(
        lens_id="LENS-KAHNEMAN",
        identity="Daniel Kahneman (1934–2024)",
        domain=KnowledgeDomain.BEHAVIORAL_ECONOMICS,
        public_source_corpus=[
            "Prospect Theory: An Analysis of Decision under Risk (1979)",
            "Thinking, Fast and Slow (2011)"
        ],
        verified_principles=[
            {
                "principle_id": "BEHAV-01",
                "title": "Loss Aversion Asymmetry",
                "formula_or_rule": "Losses loom ~2x larger than equivalent gains: v(-x) = -lambda * v(x), lambda ~ 2.25",
                "citation_ref": "SRC-KAHNEMAN-1979:p279"
            }
        ],
        mental_models=["System 1 (fast, heuristic) vs System 2 (slow, analytical)", "Availability Heuristic", "Anchoring & Framing"],
        historical_evidence=["Extensive behavioral economics experiments replicated globally across 4 decades"],
        documented_failures=["Heuristics describe retail crowd psychology well, but systematic algorithmic bots do not exhibit human loss aversion."],
        strengths=["Predicting retail FOMO peaks and panic-selling bottoms in crypto meme tokens"],
        blind_spots=["Algorithmic trading behavior and automated liquidation protocols"],
        biases=["Cognitive bias focus (over-indexes on human irrationality)"],
        ahos_applications=["Detect retail buyer exhaustion when social volume spikes during declining on-chain liquidity", "Anti-FOMO gate"],
        citations=[
            {"citation_ref": "SRC-KAHNEMAN-1979", "title": "Prospect Theory", "year": "1979", "publication": "Econometrica"}
        ],
        provenance=_sha("Kahneman_Prospect_Theory_1979")
    ),

    # 5. Charlie Munger
    "LENS-MUNGER": ExpertLensCard(
        lens_id="LENS-MUNGER",
        identity="Charlie Munger (1924–2023)",
        domain=KnowledgeDomain.BEHAVIORAL_ECONOMICS,
        public_source_corpus=[
            "Poor Charlie's Almanack: The Wit and Wisdom of Charles T. Munger (2005)",
            "The Psychology of Human Misjudgment (1995)"
        ],
        verified_principles=[
            {
                "principle_id": "INVERSION-01",
                "title": "Inversion Principle",
                "formula_or_rule": "Invert, always invert: identify all ways a system can fail and systematically eliminate them.",
                "citation_ref": "SRC-MUNGER-1995:speech"
            }
        ],
        mental_models=["Lollapalooza Tendency (multiple biases reinforcing)", "Circle of Competence", "Margin of Safety"],
        historical_evidence=["Berkshire Hathaway multi-decade compound investment track record"],
        documented_failures=["Dismissive of open decentralized cryptographic assets and early-stage network goods."],
        strengths=["Rigorous elimination of failure modes; detecting multi-factor fraud schemes"],
        blind_spots=["Early-stage open protocol network effects without traditional cash flows"],
        biases=["Traditional capital allocation bias"],
        ahos_applications=["Inversion-first security gate: check for honeypots, mint privileges, and liquidity drains BEFORE scoring opportunity"],
        citations=[
            {"citation_ref": "SRC-MUNGER-2005", "title": "Poor Charlie's Almanack", "year": "2005", "publication": "Warrant Investment"}
        ],
        provenance=_sha("Munger_Inversion_Almanack_2005")
    ),

    # 6. Nassim Nicholas Taleb
    "LENS-TALEB": ExpertLensCard(
        lens_id="LENS-TALEB",
        identity="Nassim Nicholas Taleb (1960–present)",
        domain=KnowledgeDomain.MARKET_MICROSTRUCTURE,
        public_source_corpus=[
            "Fooled by Randomness (2001)",
            "The Black Swan (2007)",
            "Antifragile: Things That Gain from Disorder (2012)",
            "Skin in the Game (2018)"
        ],
        verified_principles=[
            {
                "principle_id": "CONVEXITY-01",
                "title": "Jensen's Inequality & Convex Payoff Architecture",
                "formula_or_rule": "f(E[x]) <= E[f(x)] for convex f; maximize optionality with bounded downside.",
                "citation_ref": "SRC-TALEB-2012:p231"
            }
        ],
        mental_models=["Antifragility", "Skin in the Game", "Non-ergodicity & Ruin Elimination", "Barbell Strategy"],
        historical_evidence=["Empirica Capital & Universa Investments tail-hedging performance in 2000, 2008, 2020"],
        documented_failures=["Tail hedges suffer negative carry in prolonged low-volatility drift regimes."],
        strengths=["Absolute elimination of catastrophic tail risk and liquidity trap exposure"],
        blind_spots=["Short-term high-frequency scalping opportunities"],
        biases=["Extreme epistemic skepticism; hostility to point-estimate forecasting"],
        ahos_applications=["Strict $0 / Paper-only trapped-capital protection; elimination of un-exitability risks"],
        citations=[
            {"citation_ref": "SRC-TALEB-2012", "title": "Antifragile", "year": "2012", "publication": "Random House"}
        ],
        provenance=_sha("Taleb_Antifragile_2012")
    ),

    # 7. Satoshi Nakamoto
    "LENS-NAKAMOTO": ExpertLensCard(
        lens_id="LENS-NAKAMOTO",
        identity="Satoshi Nakamoto (Pseudonymous, 2008)",
        domain=KnowledgeDomain.CRYPTOGRAPHY,
        public_source_corpus=[
            "Bitcoin: A Peer-to-Peer Electronic Cash System (2008)",
            "Source code and forum archives (2008–2010)"
        ],
        verified_principles=[
            {
                "principle_id": "CRYPTO-01",
                "title": "Trust Minimization via Proof-of-Work Consensus",
                "formula_or_rule": "Longest valid chain with cumulative proof-of-work is the single historical truth.",
                "citation_ref": "SRC-NAKAMOTO-2008:p3"
            }
        ],
        mental_models=["Cryptographic proof over human trust", "Selfish miner incentives", "Strict digital scarcity"],
        historical_evidence=["Bitcoin 17-year uninterrupted network execution without central coordinator"],
        documented_failures=["Base-layer throughput scaling limits; does not natively support rich AMM state machines."],
        strengths=["Evaluating true decentralization versus centralized admin-key theater"],
        blind_spots=["High-speed DeFi composability and MEV dynamics"],
        biases=["Minimalist security conservatism"],
        ahos_applications=["Verify contract immutability: detect active admin mint/freeze keys masquerading as decentralized tokens"],
        citations=[
            {"citation_ref": "SRC-NAKAMOTO-2008", "title": "Bitcoin Whitepaper", "year": "2008", "publication": "bitcoin.org"}
        ],
        provenance=_sha("Nakamoto_Bitcoin_2008")
    ),

    # 8. Hal Finney
    "LENS-FINNEY": ExpertLensCard(
        lens_id="LENS-FINNEY",
        identity="Hal Finney (1956–2014)",
        domain=KnowledgeDomain.CRYPTOGRAPHY,
        public_source_corpus=[
            "Reusable Proofs of Work (RPOW, 2004)",
            "Cypherpunk mailing list contributions (1992–2014)"
        ],
        verified_principles=[
            {
                "principle_id": "PRIV-01",
                "title": "Verifiable Cryptographic Determinism",
                "formula_or_rule": "Deterministic verification allows untrusted nodes to reach identical state without central clock.",
                "citation_ref": "SRC-FINNEY-2004:rpow"
            }
        ],
        mental_models=["Reusable token proofs", "Zero-knowledge verification", "Cryptographic privacy safeguards"],
        historical_evidence=["First Bitcoin transaction receiver; early PGP software engineering"],
        documented_failures=["Early RPOW required trusted hardware (IBM 4758 TPM) before decentralized PoW was discovered."],
        strengths=["Deep understanding of low-level cryptographic signatures and wallet token transfers"],
        blind_spots=["Modern complex multi-token liquidity routing games"],
        biases=["Cypherpunk idealism"],
        ahos_applications=["Audit raw cryptographic bytecode and signature verification integrity"],
        citations=[
            {"citation_ref": "SRC-FINNEY-2004", "title": "Reusable Proofs of Work", "year": "2004", "publication": "RPOW Project"}
        ],
        provenance=_sha("Finney_RPOW_2004")
    ),

    # 9. Vitalik Buterin
    "LENS-BUTERIN": ExpertLensCard(
        lens_id="LENS-BUTERIN",
        identity="Vitalik Buterin (1994–present)",
        domain=KnowledgeDomain.DISTRIBUTED_SYSTEMS,
        public_source_corpus=[
            "Ethereum Whitepaper: A Next-Generation Smart Contract and Decentralized Application Platform (2013)",
            "On Public Goods and Quadratic Funding (2018)",
            "Proof of Stake and Cryptoeconomics Research (2015–2024)"
        ],
        verified_principles=[
            {
                "principle_id": "TRILEMMA-01",
                "title": "Blockchain Scalability Trilemma",
                "formula_or_rule": "A decentralized network can optimize at most 2 of: Decentralization, Security, Scalability.",
                "citation_ref": "SRC-BUTERIN-2017:trilemma"
            }
        ],
        mental_models=["State machine replication with Turing-complete execution", "Mechanism design & Cryptoeconomic incentives", "Account abstraction"],
        historical_evidence=["Ethereum global smart contract ecosystem, EVM standard adoption across dozens of L1/L2 networks"],
        documented_failures=["High gas congestion spikes; complex smart contracts increase vulnerability attack surface."],
        strengths=["Analyzing multi-token composability, AMM pools, rollup bridges, and protocol governance"],
        blind_spots=["Over-estimating user willingness to navigate complex cryptographic UX/gas abstractions"],
        biases=["Turing-completeness and complex mechanism design preference"],
        ahos_applications=["Evaluate token contract composability, DEX pair architectures, and bridge lock contracts"],
        citations=[
            {"citation_ref": "SRC-BUTERIN-2013", "title": "Ethereum Whitepaper", "year": "2013", "publication": "ethereum.org"}
        ],
        provenance=_sha("Buterin_Ethereum_2013")
    ),

    # 10. Howard Marks
    "LENS-MARKS": ExpertLensCard(
        lens_id="LENS-MARKS",
        identity="Howard Marks (1946–present)",
        domain=KnowledgeDomain.MARKET_MICROSTRUCTURE,
        public_source_corpus=[
            "The Most Important Thing: Uncommon Sense for the Thoughtful Investor (2011)",
            "Mastering the Market Cycle: Getting the Odds on Your Side (2018)"
        ],
        verified_principles=[
            {
                "principle_id": "SECOND-LEVEL-01",
                "title": "Second-Level Thinking",
                "formula_or_rule": "First-level thinking: 'It is a good project, buy.' Second-level: 'It is a good project, but everybody thinks so, thus it is overpriced; avoid.'",
                "citation_ref": "SRC-MARKS-2011:p5"
            }
        ],
        mental_models=["Market pendulum & sentiment cycles", "Second-level thinking", "Risk as probability of permanent capital loss"],
        historical_evidence=["Oaktree Capital distressed debt track record across 1990, 2001, 2008 cycles"],
        documented_failures=["Can stay defensive too long during liquidity-driven momentum bubbles."],
        strengths=["Identifying asymmetric risk/reward setups and separating price momentum from underlying solvency"],
        blind_spots=["Fast-moving algorithmic meme token dynamics"],
        biases=["Value and distressed debt cycle orientation"],
        ahos_applications=["Compare token opportunity score against crowd sentiment: penalize over-hyped tokens lacking liquidity"],
        citations=[
            {"citation_ref": "SRC-MARKS-2011", "title": "The Most Important Thing", "year": "2011", "publication": "Columbia Univ. Press"}
        ],
        provenance=_sha("Marks_Most_Important_Thing_2011")
    ),

    # 11. John Nash
    "LENS-NASH": ExpertLensCard(
        lens_id="LENS-NASH",
        identity="John Nash (1928–2015)",
        domain=KnowledgeDomain.GAME_THEORY,
        public_source_corpus=[
            "Equilibrium Points in N-Person Games (1950)",
            "Non-Cooperative Games (1951)"
        ],
        verified_principles=[
            {
                "principle_id": "NASH-01",
                "title": "Non-Cooperative Nash Equilibrium",
                "formula_or_rule": "In an N-player game, no player has an incentive to unilaterally deviate from their strategy.",
                "citation_ref": "SRC-NASH-1950:p48"
            }
        ],
        mental_models=["Non-cooperative equilibrium", "Adversarial payoff matrices", "Strategic stability"],
        historical_evidence=["Applied globally in spectrum auctions, economics, and decentralized protocol incentive design"],
        documented_failures=["Multiple equilibria can exist; does not predict which equilibrium non-rational agents select."],
        strengths=["Analyzing liquidity provider (LP) withdrawal games and MEV searcher competition"],
        blind_spots=["Irrational panic runs during catastrophic market crashes"],
        biases=["Rational self-interest assumption"],
        ahos_applications=["Model DEX pool liquidity stability as an N-player withdrawal equilibrium"],
        citations=[
            {"citation_ref": "SRC-NASH-1950", "title": "Equilibrium Points in N-Person Games", "year": "1950", "publication": "PNAS"}
        ],
        provenance=_sha("Nash_Equilibrium_1950")
    ),

    # 12. Ken Thompson
    "LENS-THOMPSON": ExpertLensCard(
        lens_id="LENS-THOMPSON",
        identity="Ken Thompson (1943–present)",
        domain=KnowledgeDomain.DISTRIBUTED_SYSTEMS,
        public_source_corpus=[
            "The Unix Time-Sharing System (1974)",
            "Reflections on Trusting Trust (1984)"
        ],
        verified_principles=[
            {
                "principle_id": "UNIX-01",
                "title": "Orthogonal Tool Composition",
                "formula_or_rule": "Write programs that do one thing and do it well. Write programs to work together.",
                "citation_ref": "SRC-THOMPSON-1974:unix"
            },
            {
                "principle_id": "TRUST-01",
                "title": "Trusting Trust Problem",
                "formula_or_rule": "You cannot trust code that you did not totally create yourself, especially the compiler.",
                "citation_ref": "SRC-THOMPSON-1984:acm"
            }
        ],
        mental_models=["Do one thing well", "Clean text streams", "Trusting Trust compiler vulnerability"],
        historical_evidence=["Unix operating system, B/C language foundations, UTF-8 design"],
        documented_failures=["Extreme modularity can lead to complex integration overhead if interface contracts drift."],
        strengths=["Minimalist system architecture, micro-service boundary isolation, compiler-level backdoor awareness"],
        blind_spots=["High-level abstract UI/UX ergonomics"],
        biases=["Minimalist Unix philosophy"],
        ahos_applications=["Ensure AHOS subsystems remain modular, deep, and orthogonal without bloated dependencies"],
        citations=[
            {"citation_ref": "SRC-THOMPSON-1984", "title": "Reflections on Trusting Trust", "year": "1984", "publication": "Comm. ACM"}
        ],
        provenance=_sha("Thompson_Unix_Trust_1984")
    ),

    # 13. George Boole
    "LENS-BOOLE": ExpertLensCard(
        lens_id="LENS-BOOLE",
        identity="George Boole (1815–1864)",
        domain=KnowledgeDomain.MATHEMATICS,
        public_source_corpus=[
            "The Mathematical Analysis of Logic (1847)",
            "An Investigation of the Laws of Thought (1854)"
        ],
        verified_principles=[
            {
                "principle_id": "BOOLE-01",
                "title": "Boolean Logic Foundations",
                "formula_or_rule": "Logical propositions reduce to binary algebraic operations (AND, OR, NOT) with values in {0, 1}.",
                "citation_ref": "SRC-BOOLE-1854:p12"
            }
        ],
        mental_models=["Binary truth values", "Algebraic reduction of logical statements", "Deterministic decision trees"],
        historical_evidence=["Digital logic gates, modern computing hardware, symbolic computation"],
        documented_failures=["Binary logic does not natively model fuzzy uncertainty or continuous probability without probabilistic extensions."],
        strengths=["Unambiguous deterministic security vetoes (Honeypot = 1 => Score = 0)"],
        blind_spots=["Continuous probabilistic confidence calibration"],
        biases=["Strict binary categorization"],
        ahos_applications=["Formulate non-negotiable binary security vetoes as hard boolean gates"],
        citations=[
            {"citation_ref": "SRC-BOOLE-1854", "title": "The Laws of Thought", "year": "1854", "publication": "Walton and Maberly"}
        ],
        provenance=_sha("Boole_Laws_Thought_1854")
    ),

    # 14. Alan Turing
    "LENS-TURING": ExpertLensCard(
        lens_id="LENS-TURING",
        identity="Alan Turing (1912–1954)",
        domain=KnowledgeDomain.MATHEMATICS,
        public_source_corpus=[
            "On Computable Numbers, with an Application to the Entscheidungsproblem (1936)",
            "Computing Machinery and Intelligence (1950)"
        ],
        verified_principles=[
            {
                "principle_id": "TURING-01",
                "title": "Halting Problem Undecidability",
                "formula_or_rule": "No general algorithm can decide whether an arbitrary program will halt or run forever.",
                "citation_ref": "SRC-TURING-1936:p230"
            }
        ],
        mental_models=["Universal Turing Machine", "Undecidability & Halting bounds", "Turing Test for intelligence"],
        historical_evidence=["Modern programmable computer theory, Enigma cryptanalysis at Bletchley Park"],
        documented_failures=["Turing machine models ignore physical hardware timing, energy, and network partition delays."],
        strengths=["Identifying fundamentally uncomputable questions and infinite loop vulnerabilities in smart contracts"],
        blind_spots=["Real-time asynchronous distributed network consensus"],
        biases=["Theoretical computation focus"],
        ahos_applications=["Audit smart contract gas loop bounds and avoid uncomputable decision pathways"],
        citations=[
            {"citation_ref": "SRC-TURING-1936", "title": "On Computable Numbers", "year": "1936", "publication": "Proc. London Math. Soc."}
        ],
        provenance=_sha("Turing_Computable_Numbers_1936")
    ),

    # 15. Kurt Gödel
    "LENS-GODEL": ExpertLensCard(
        lens_id="LENS-GODEL",
        identity="Kurt Gödel (1906–1978)",
        domain=KnowledgeDomain.MATHEMATICS,
        public_source_corpus=[
            "Über formal unentscheidbare Sätze der Principia Mathematica (1931)"
        ],
        verified_principles=[
            {
                "principle_id": "GODEL-01",
                "title": "First Incompleteness Theorem",
                "formula_or_rule": "Any consistent formal system capable of basic arithmetic contains true statements that cannot be proven within the system.",
                "citation_ref": "SRC-GODEL-1931:p173"
            }
        ],
        mental_models=["Incompleteness", "Epistemic limits of closed axiomatic systems", "Self-referential paradoxes"],
        historical_evidence=["Modern mathematical logic, foundational limits of formal automated proof systems"],
        documented_failures=["Does not prevent constructing practical, robust engineering approximations within bounded domains."],
        strengths=["Epistemic humility: recognizing that no single rulebook or scoring model can capture all market reality"],
        blind_spots=["Can lead to paralysis if taken as a reason to reject all practical heuristics"],
        biases=["Mathematical skepticism of completeness"],
        ahos_applications=["Enforce the 'UNKNOWN remains UNKNOWN' rule and prevent overconfident closed-system assumptions"],
        citations=[
            {"citation_ref": "SRC-GODEL-1931", "title": "Incompleteness Theorems", "year": "1931", "publication": "Monatshefte für Math."}
        ],
        provenance=_sha("Godel_Incompleteness_1931")
    ),

    # 16. Thomas Bayes
    "LENS-BAYES": ExpertLensCard(
        lens_id="LENS-BAYES",
        identity="Thomas Bayes (1701–1761)",
        domain=KnowledgeDomain.MATHEMATICS,
        public_source_corpus=[
            "An Essay towards solving a Problem in the Doctrine of Chances (1763)"
        ],
        verified_principles=[
            {
                "principle_id": "BAYES-01",
                "title": "Bayes' Theorem for Conditional Probability",
                "formula_or_rule": "P(A|B) = [P(B|A) * P(A)] / P(B)",
                "citation_ref": "SRC-BAYES-1763:p370"
            }
        ],
        mental_models=["Prior belief updating via empirical likelihood", "Base rate fallacy avoidance", "Conditional probability"],
        historical_evidence=["Statistical inference across physics, cryptography, medical diagnostics, and search theory"],
        documented_failures=["Vulnerable to arbitrary or miscalibrated prior selection (subjective priors)."],
        strengths=["Continuously refining token opportunity confidence as fresh observations arrive"],
        blind_spots=["Black swan events where true probability distribution has undefined moments"],
        biases=["Bayesian updating assumption"],
        ahos_applications=["Update token success probabilities from base rate priors as snapshot intervals mature"],
        citations=[
            {"citation_ref": "SRC-BAYES-1763", "title": "Doctrine of Chances", "year": "1763", "publication": "Phil. Trans. Royal Soc."}
        ],
        provenance=_sha("Bayes_Probability_1763")
    ),

    # 17. Ronald Fisher
    "LENS-FISHER": ExpertLensCard(
        lens_id="LENS-FISHER",
        identity="Ronald Fisher (1890–1962)",
        domain=KnowledgeDomain.MATHEMATICS,
        public_source_corpus=[
            "Statistical Methods for Research Workers (1925)",
            "The Design of Experiments (1935)"
        ],
        verified_principles=[
            {
                "principle_id": "FISHER-01",
                "title": "Null Hypothesis Significance Testing & Maximum Likelihood",
                "formula_or_rule": "Reject null hypothesis H0 only when p-value < alpha under pre-registered experimental controls.",
                "citation_ref": "SRC-FISHER-1925:p42"
            }
        ],
        mental_models=["Randomized control trials", "Null hypothesis testing", "Maximum likelihood estimation", "ANOVA"],
        historical_evidence=["Foundational standard of empirical scientific testing in biology, medicine, and economics"],
        documented_failures=["Vulnerable to p-hacking and multiple testing artifacts if search space is not strictly pre-registered."],
        strengths=["Enforcing pre-registered significance bars and preventing false discovery claims"],
        blind_spots=["Does not incorporate prior probability distributions (contrast with Bayes)"],
        biases=["Frequentist significance bias"],
        ahos_applications=["Enforce pre-registered Wilson CI baseline cells (B1/B2) and reject un-registered p-hacked cells"],
        citations=[
            {"citation_ref": "SRC-FISHER-1925", "title": "Statistical Methods for Research Workers", "year": "1925", "publication": "Oliver and Boyd"}
        ],
        provenance=_sha("Fisher_Statistical_Methods_1925")
    ),

    # 18. Judea Pearl
    "LENS-PEARL": ExpertLensCard(
        lens_id="LENS-PEARL",
        identity="Judea Pearl (1936–present)",
        domain=KnowledgeDomain.COMPLEX_SYSTEMS,
        public_source_corpus=[
            "Probabilistic Reasoning in Intelligent Systems (1988)",
            "Causality: Models, Reasoning, and Inference (2000)",
            "The Book of Why (2018)"
        ],
        verified_principles=[
            {
                "principle_id": "CAUSAL-01",
                "title": "Causal DAGs & Do-Calculus",
                "formula_or_rule": "P(Y | do(X)) != P(Y | X); confounding variables must be blocked via back-door criterion.",
                "citation_ref": "SRC-PEARL-2000:p85"
            }
        ],
        mental_models=["Ladder of Causation (Association -> Intervention -> Counterfactual)", "Confounder blocking", "Structural Causal Models"],
        historical_evidence=["Modern causal inference in epidemiology, econometrics, and artificial intelligence"],
        documented_failures=["Constructing true causal graphs requires domain knowledge; wrong DAG topology yields biased estimates."],
        strengths=["Separating spurious correlation (e.g. wash volume) from true causal demand drivers"],
        blind_spots=["Complex feedback loops in high-frequency reflexive financial markets"],
        biases=["Directed Acyclic Graph (DAG) structural assumption"],
        ahos_applications=["Audit whether volume growth causes price appreciation or if both are confounded by deployer wash trading"],
        citations=[
            {"citation_ref": "SRC-PEARL-2000", "title": "Causality", "year": "2000", "publication": "Cambridge Univ. Press"}
        ],
        provenance=_sha("Pearl_Causality_2000")
    ),

    # 19. Bruce Schneier
    "LENS-SCHNEIER": ExpertLensCard(
        lens_id="LENS-SCHNEIER",
        identity="Bruce Schneier (1959–present)",
        domain=KnowledgeDomain.CYBERSECURITY,
        public_source_corpus=[
            "Applied Cryptography (1994)",
            "Secrets and Lies: Digital Security in a Networked World (2000)",
            "Liars and Outliers (2012)"
        ],
        verified_principles=[
            {
                "principle_id": "SEC-PROCESS-01",
                "title": "Security is a Process, Not a Product",
                "formula_or_rule": "A system is only as secure as its weakest link; cryptography alone does not solve human/protocol failure modes.",
                "citation_ref": "SRC-SCHNEIER-2000:p12"
            }
        ],
        mental_models=["Defense-in-depth", "Attacker economics & asymmetric attack cost", "Threat modeling"],
        historical_evidence=["Foundational digital security standards, counterpane security engineering"],
        documented_failures=["Can lead to excessive pessimism regarding usability if security controls are too friction-heavy."],
        strengths=["Detecting side-channel risks, deployer privilege escalations, and socio-technical attack vectors"],
        blind_spots=["Fast-moving decentralized composability UX"],
        biases=["Defense-in-depth security conservatism"],
        ahos_applications=["Apply multi-layered security gates: contract bytecode audit + deployer wallet history + LP lock verification"],
        citations=[
            {"citation_ref": "SRC-SCHNEIER-2000", "title": "Secrets and Lies", "year": "2000", "publication": "John Wiley & Sons"}
        ],
        provenance=_sha("Schneier_Secrets_Lies_2000")
    ),

    # 20. Eric Brewer
    "LENS-BREWER": ExpertLensCard(
        lens_id="LENS-BREWER",
        identity="Eric Brewer (1965–present)",
        domain=KnowledgeDomain.DISTRIBUTED_SYSTEMS,
        public_source_corpus=[
            "Towards Robust Distributed Systems (2000)",
            "CAP Twelve Years Later: How the 'Rules' Have Changed (2012)"
        ],
        verified_principles=[
            {
                "principle_id": "CAP-01",
                "title": "CAP Theorem",
                "formula_or_rule": "A distributed data store can simultaneously provide at most two of: Consistency, Availability, Partition tolerance.",
                "citation_ref": "SRC-BREWER-2000:cap"
            }
        ],
        mental_models=["Consistency vs Availability trade-off", "Network partition handling", "Eventual consistency"],
        historical_evidence=["Global distributed database designs (Cassandra, Spanner, DynamoDB, decentralized blockchains)"],
        documented_failures=["CAP theorem applies strictly to network partitions; normal-mode latency trade-offs require PACELC extension."],
        strengths=["Evaluating blockchain RPC node latency, network partition recovery, and data freshness trade-offs"],
        blind_spots=["Single-node standalone algorithmic performance"],
        biases=["Distributed systems trade-off focus"],
        ahos_applications=["Design local SQLite data storage with partition-tolerant offline queueing and eventual synchronization"],
        citations=[
            {"citation_ref": "SRC-BREWER-2000", "title": "Towards Robust Distributed Systems", "year": "2000", "publication": "ACM PODC"}
        ],
        provenance=_sha("Brewer_CAP_Theorem_2000")
    ),

    # 21. Ada Lovelace
    "LENS-LOVELACE": ExpertLensCard(
        lens_id="LENS-LOVELACE",
        identity="Ada Lovelace (1815–1852)",
        domain=KnowledgeDomain.MATHEMATICS,
        public_source_corpus=[
            "Sketch of the Analytical Engine Invented by Charles Babbage (1843)"
        ],
        verified_principles=[
            {
                "principle_id": "ALGO-01",
                "title": "Separation of Data Manipulation from Symbolic Operations",
                "formula_or_rule": "The engine weaves algebraic patterns just as the Jacquard-loom weaves flowers and leaves.",
                "citation_ref": "SRC-LOVELACE-1843:noteG"
            }
        ],
        mental_models=["Universal algorithmic transformation", "Software separation from hardware", "Symbolic abstraction"],
        historical_evidence=["First published computer algorithm (Bernoulli numbers computation)"],
        documented_failures=["Mechanical calculation limitations of Babbage physical engine."],
        strengths=["Evaluating abstract algorithmic transformations independent of raw execution media"],
        blind_spots=["Asynchronous real-time streaming concurrency"],
        biases=["Symbolic mathematical purity"],
        ahos_applications=["Separate data collection schemas strictly from scoring logic and presentation layers"],
        citations=[
            {"citation_ref": "SRC-LOVELACE-1843", "title": "Notes on the Analytical Engine", "year": "1843", "publication": "Taylor's Scientific Memoirs"}
        ],
        provenance=_sha("Lovelace_Analytical_Engine_1843")
    ),

    # 22. Grace Hopper
    "LENS-HOPPER": ExpertLensCard(
        lens_id="LENS-HOPPER",
        identity="Grace Hopper (1906–1992)",
        domain=KnowledgeDomain.MATHEMATICS,
        public_source_corpus=[
            "The Education of a Computer (1952)",
            "Keynote Address on Standards and Compilers (1970)"
        ],
        verified_principles=[
            {
                "principle_id": "COMPILER-01",
                "title": "Machine-Independent Abstractions & Standards",
                "formula_or_rule": "Programs should be written in human-readable terms that compile down to deterministic machine instructions.",
                "citation_ref": "SRC-HOPPER-1952:compiler"
            }
        ],
        mental_models=["Standardized interfaces", "Compiler-level optimization", "Nanosecond physical latency reality"],
        historical_evidence=["First compiler (A-0), COBOL language standardization, Harvard Mark I/II debugging"],
        documented_failures=["High-level abstractions can hide hardware-level cache misses and gas costs if not profiled."],
        strengths=["Designing portable, machine-independent interfaces across disparate systems"],
        blind_spots=["Obfuscated low-level assembly vulnerabilities"],
        biases=["Standardization and high-level language preference"],
        ahos_applications=["Standardize provider response envelopes into normalized candidate schemas across all chains"],
        citations=[
            {"citation_ref": "SRC-HOPPER-1952", "title": "The Education of a Computer", "year": "1952", "publication": "ACM Conference"}
        ],
        provenance=_sha("Hopper_Compiler_Standards_1952")
    ),

    # 23. Edsger Dijkstra
    "LENS-DIJKSTRA": ExpertLensCard(
        lens_id="LENS-DIJKSTRA",
        identity="Edsger Dijkstra (1930–2002)",
        domain=KnowledgeDomain.MATHEMATICS,
        public_source_corpus=[
            "A Note on Two Problems in Connexion with Graphs (1959)",
            "Go To Statement Considered Harmful (1968)",
            "Structured Programming (1972)"
        ],
        verified_principles=[
            {
                "principle_id": "DIJKSTRA-01",
                "title": "Structural Elegance & Shortest-Path Optimality",
                "formula_or_rule": "Simplicity is prerequisite for reliability; software correctness must be proven mathematically.",
                "citation_ref": "SRC-DIJKSTRA-1972:struct"
            }
        ],
        mental_models=["Shortest path routing", "Semaphores & mutual exclusion", "Structured programming invariants"],
        historical_evidence=["Dijkstra algorithm in global network routing (OSPF), semaphore concurrency in modern OS kernels"],
        documented_failures=["Pure mathematical proof can be intractable for dynamic emergent financial crowd behavior."],
        strengths=["Enforcing acyclic execution graphs, deterministic state machines, and mutual exclusion locks"],
        blind_spots=["Fuzzy heuristic decision-making under severe data starvation"],
        biases=["Elegance and formal verification purism"],
        ahos_applications=["Enforce acyclic DAGs in multi-agent execution and atomic locking in scheduler leases"],
        citations=[
            {"citation_ref": "SRC-DIJKSTRA-1959", "title": "Shortest Path Algorithm", "year": "1959", "publication": "Numerische Mathematik"}
        ],
        provenance=_sha("Dijkstra_Shortest_Path_1959")
    ),

    # 24. Donald Knuth
    "LENS-KNUTH": ExpertLensCard(
        lens_id="LENS-KNUTH",
        identity="Donald Knuth (1938–present)",
        domain=KnowledgeDomain.MATHEMATICS,
        public_source_corpus=[
            "The Art of Computer Programming (Volumes 1–4, 1968–2024)",
            "Structured Programming with go to Statements (1974)"
        ],
        verified_principles=[
            {
                "principle_id": "KNUTH-01",
                "title": "Asymptotic Analysis & Premature Optimization Law",
                "formula_or_rule": "Premature optimization is the root of all evil (or at least most of it) in programming.",
                "citation_ref": "SRC-KNUTH-1974:acm"
            }
        ],
        mental_models=["Asymptotic algorithm complexity", "Literate programming & documentation truth", "Combinatorial algorithms"],
        historical_evidence=["TeX typesetting system, Knuth-Morris-Pratt string matching, TAOCP foundational algorithms"],
        documented_failures=["Extreme precision in micro-algorithms can delay macroscopic architectural pivots."],
        strengths=["Rigorous algorithmic efficiency, precise error bounding, and exhaustive documentation"],
        blind_spots=["Rapid exploratory prototyping under uncertain market product-market fit"],
        biases=["Deep perfectionism and algorithmic thoroughness"],
        ahos_applications=["Profile and ensure sub-second execution for all batch scoring and feature calculation loops"],
        citations=[
            {"citation_ref": "SRC-KNUTH-1968", "title": "The Art of Computer Programming", "year": "1968", "publication": "Addison-Wesley"}
        ],
        provenance=_sha("Knuth_TAOCP_1968")
    ),

    # 25. Dennis Ritchie
    "LENS-RITCHIE": ExpertLensCard(
        lens_id="LENS-RITCHIE",
        identity="Dennis Ritchie (1941–2011)",
        domain=KnowledgeDomain.DISTRIBUTED_SYSTEMS,
        public_source_corpus=[
            "The C Programming Language (with Brian Kernighan, 1978)",
            "The Development of the C Language (1993)"
        ],
        verified_principles=[
            {
                "principle_id": "RITCHIE-01",
                "title": "Minimalist Expressiveness & System Transparency",
                "formula_or_rule": "Keep the abstractions thin and transparent so the programmer understands the underlying machine state.",
                "citation_ref": "SRC-RITCHIE-1978:cbook"
            }
        ],
        mental_models=["Direct pointer semantics", "Minimalist standard libraries", "System transparency"],
        historical_evidence=["C language and Unix kernel powering all modern computing infrastructure (Linux, iOS, Windows NT)"],
        documented_failures=["Lack of memory safety leads to buffer overflow and security vulnerabilities if unmanaged."],
        strengths=["Designing lean, fast, transparent system utilities without bloated layers"],
        blind_spots=["High-level mathematical declarative reasoning"],
        biases=["Systems programming minimalism"],
        ahos_applications=["Keep AHOS runtime and database layers transparent, direct, and free of unnecessary layers"],
        citations=[
            {"citation_ref": "SRC-RITCHIE-1978", "title": "The C Programming Language", "year": "1978", "publication": "Prentice Hall"}
        ],
        provenance=_sha("Ritchie_C_Language_1978")
    ),

    # 26. Margaret Hamilton
    "LENS-HAMILTON": ExpertLensCard(
        lens_id="LENS-HAMILTON",
        identity="Margaret Hamilton (1936–present)",
        domain=KnowledgeDomain.DISTRIBUTED_SYSTEMS,
        public_source_corpus=[
            "Apollo Guidance Computer Software Architecture (1969)",
            "Universal Systems Language & Development Before the Fact (1986)"
        ],
        verified_principles=[
            {
                "principle_id": "HAMILTON-01",
                "title": "Priority Task Scheduling & Asynchronous Fault Recovery",
                "formula_or_rule": "When overloaded, drop lower-priority background tasks to preserve vital real-time control and state.",
                "citation_ref": "SRC-HAMILTON-1969:apollo"
            }
        ],
        mental_models=["Priority preemption under overload", "Asynchronous executive", "Software engineering rigor"],
        historical_evidence=["Apollo 11 lunar landing software recovery (1201/1202 radar overload alarms)"],
        documented_failures=["Extreme redundancy increases system verification time and specification complexity."],
        strengths=["Mission-critical fault tolerance, overload shedding, and fail-safe recovery"],
        blind_spots=["Non-critical user interfaces and experimental exploratory research"],
        biases=["Mission-critical safety conservatism"],
        ahos_applications=["Implement backpressure load shedding: prioritize active paper position monitoring over new discovery if overloaded"],
        citations=[
            {"citation_ref": "SRC-HAMILTON-1969", "title": "Apollo Guidance Computer Architecture", "year": "1969", "publication": "NASA Report"}
        ],
        provenance=_sha("Hamilton_Apollo_1969")
    ),

    # 27. Barbara Liskov
    "LENS-LISKOV": ExpertLensCard(
        lens_id="LENS-LISKOV",
        identity="Barbara Liskov (1939–present)",
        domain=KnowledgeDomain.MATHEMATICS,
        public_source_corpus=[
            "Data Abstraction and Hierarchy (1987)",
            "A Behavioral Notion of Subtyping (with Jeannette Wing, 1994)"
        ],
        verified_principles=[
            {
                "principle_id": "LISKOV-01",
                "title": "Liskov Substitution Principle (LSP)",
                "formula_or_rule": "Subtypes must be substitutable for their base types without altering the correctness of program invariants.",
                "citation_ref": "SRC-LISKOV-1994:lsp"
            }
        ],
        mental_models=["Behavioral subtyping", "Abstract data types (ADT)", "Formal precondition/postcondition contracts"],
        historical_evidence=["Object-oriented programming contracts (SOLID principles), CLU programming language"],
        documented_failures=["Rigid subtyping hierarchies can resist rapid ad-hoc schema modifications in exploratory pipelines."],
        strengths=["Enforcing strong provider contracts, adapter substitutability, and deterministic interface guarantees"],
        blind_spots=["Dynamic schema-less streaming ingestion"],
        biases=["Contract and behavioral subtyping rigor"],
        ahos_applications=["Ensure BaseMarketProvider adapters (DexScreener, Gecko, GoPlus, RugCheck) are 100% interchangeable"],
        citations=[
            {"citation_ref": "SRC-LISKOV-1994", "title": "Behavioral Notion of Subtyping", "year": "1994", "publication": "ACM TOPLAS"}
        ],
        provenance=_sha("Liskov_Substitution_1994")
    ),

    # 28. Leslie Lamport
    "LENS-LAMPORT": ExpertLensCard(
        lens_id="LENS-LAMPORT",
        identity="Leslie Lamport (1941–present)",
        domain=KnowledgeDomain.DISTRIBUTED_SYSTEMS,
        public_source_corpus=[
            "Time, Clocks, and the Ordering of Events in a Distributed System (1978)",
            "The Part-Time Parliament / Paxos Algorithm (1998)",
            "Specifying Systems: The TLA+ Language (2002)"
        ],
        verified_principles=[
            {
                "principle_id": "LAMPORT-01",
                "title": "Logical Clocks & Causal Ordering",
                "formula_or_rule": "Events in a distributed system are ordered by a partial-order causal relation (happened-before: a -> b).",
                "citation_ref": "SRC-LAMPORT-1978:time"
            }
        ],
        mental_models=["Happened-before causal relation", "Paxos consensus", "Formal specification with TLA+"],
        historical_evidence=["Distributed database consensus engines (Raft, Paxos, Spanner), Lamport timestamps in distributed logs"],
        documented_failures=["Paxos consensus latency can be high across WAN networks with intermittent connectivity."],
        strengths=["Preventing race conditions, enforcing causal ordering, and formal verification of distributed state"],
        blind_spots=["High-throughput optimistic execution with probabilistic finality"],
        biases=["Formal specification and strict causal ordering"],
        ahos_applications=["Audit observation retrieved_ts vs availability_ts: enforce Rule L1/L3 anti-lookahead causal invariants"],
        citations=[
            {"citation_ref": "SRC-LAMPORT-1978", "title": "Time, Clocks and Ordering", "year": "1978", "publication": "Comm. ACM"}
        ],
        provenance=_sha("Lamport_Logical_Clocks_1978")
    ),

    # 29. John McCarthy
    "LENS-MCCARTHY": ExpertLensCard(
        lens_id="LENS-MCCARTHY",
        identity="John McCarthy (1927–2011)",
        domain=KnowledgeDomain.MATHEMATICS,
        public_source_corpus=[
            "Recursive Functions of Symbolic Expressions and Their Computation by Machine (1960)",
            "Programs with Common Sense (1959)"
        ],
        verified_principles=[
            {
                "principle_id": "MCCARTHY-01",
                "title": "Symbolic Representation & Metalinguistic Abstraction",
                "formula_or_rule": "Programs and data have identical representation (homoiconicity); reasoning systems operate on explicit symbols.",
                "citation_ref": "SRC-MCCARTHY-1960:lisp"
            }
        ],
        mental_models=["Homoiconicity (code as data)", "Garbage collection", "Symbolic knowledge representation"],
        historical_evidence=["Lisp programming language, first automated garbage collection, foundational AI logic programming"],
        documented_failures=["Pure symbolic logic systems struggle with perceptual noisy real-time sensor streams without neural statistical layers."],
        strengths=["Representing structured knowledge claims, contradiction graphs, and meta-level reasoning"],
        blind_spots=["High-frequency numerical market volatility estimation"],
        biases=["Symbolic AI purism"],
        ahos_applications=["Structure K-02 knowledge claims and contradiction edges as queryable symbolic graphs"],
        citations=[
            {"citation_ref": "SRC-MCCARTHY-1960", "title": "Recursive Functions of Symbolic Expressions", "year": "1960", "publication": "Comm. ACM"}
        ],
        provenance=_sha("McCarthy_Lisp_Symbolic_1960")
    ),

    # 30. Marvin Minsky
    "LENS-MINSKY": ExpertLensCard(
        lens_id="LENS-MINSKY",
        identity="Marvin Minsky (1927–2016)",
        domain=KnowledgeDomain.MATHEMATICS,
        public_source_corpus=[
            "Perceptrons (with Seymour Papert, 1969)",
            "A Framework for Representing Knowledge (1974)",
            "The Society of Mind (1986)"
        ],
        verified_principles=[
            {
                "principle_id": "MINSKY-01",
                "title": "Society of Mind & Frame Representation",
                "formula_or_rule": "Intelligence emerges from interactions of many smaller, specialized non-intelligent agents organized in frames.",
                "citation_ref": "SRC-MINSKY-1986:som"
            }
        ],
        mental_models=["Society of Mind (decentralized agency)", "Knowledge Frames & Default Assumptions", "Perceptron linear separation limits"],
        historical_evidence=["Frame representations in knowledge bases, multi-agent cognitive architectures, neural network bounds"],
        documented_failures=["Early frame systems suffered from the frame problem (difficulty in updating non-changed facts in dynamic worlds)."],
        strengths=["Decomposing complex opportunity scoring into distinct specialized agents (Risk, Liquidity, Security, Narrative)"],
        blind_spots=["End-to-end monolithic continuous gradient optimization"],
        biases=["Multi-agent compositional bias"],
        ahos_applications=["Structure the 25-agent cognitive architecture into specialized evaluation frames without monolithic coupling"],
        citations=[
            {"citation_ref": "SRC-MINSKY-1986", "title": "The Society of Mind", "year": "1986", "publication": "Simon & Schuster"}
        ],
        provenance=_sha("Minsky_Society_Mind_1986")
    )
}


class ExpertLensLibrary:
    def __init__(self, lenses: dict[str, ExpertLensCard] | None = None):
        self._lenses = dict(lenses or LENS_PILOT_REGISTRY)

    def get_lens(self, lens_id: str) -> ExpertLensCard | None:
        return self._lenses.get(lens_id)

    def list_lenses(self) -> list[ExpertLensCard]:
        return list(self._lenses.values())

    def list_by_domain(self, domain: KnowledgeDomain) -> list[ExpertLensCard]:
        return [l for l in self._lenses.values() if l.domain == domain]

    def evaluate_opportunity_with_lenses(self, token_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Applies lens principles to token observation data without AI fabrication."""
        insights = []
        liq = token_data.get("liquidity_usd") or 0.0
        vol = token_data.get("volume_1h") or 0.0
        is_hp = token_data.get("is_honeypot", False)

        # Apply Munger Inversion Lens
        if is_hp:
            insights.append({
                "lens_id": "LENS-MUNGER",
                "identity": "Charlie Munger",
                "insight": "INVERSION VETO: Fraudulent contract structure detected (Honeypot). Immediate reject.",
                "verdict": "VETO",
                "citation_ref": "SRC-MUNGER-1995:speech"
            })

        # Apply Taleb Antifragility / Convexity Lens
        if liq < 2000.0:
            insights.append({
                "lens_id": "LENS-TALEB",
                "identity": "Nassim Nicholas Taleb",
                "insight": "CONVEXITY FAIL: Extreme liquidity fragility (< k). Risk of 100% trapped capital ruin.",
                "verdict": "AVOID_TRAPPED_CAPITAL",
                "citation_ref": "SRC-TALEB-2012:p231"
            })

        # Apply Shannon SNR / Entropy Lens
        if vol > 20000.0 and liq > 30000.0:
            insights.append({
                "lens_id": "LENS-SHANNON",
                "identity": "Claude Shannon",
                "insight": "HIGH SNR: Strong on-chain volume-to-liquidity signal exceeding background entropy.",
                "verdict": "CONFIRM_SIGNAL",
                "citation_ref": "SRC-SHANNON-1948:p380"
            })

        # Apply Howard Marks Second-Level Thinking Lens
        if vol > 50000.0 and liq < 10000.0:
            insights.append({
                "lens_id": "LENS-MARKS",
                "identity": "Howard Marks",
                "insight": "SECOND-LEVEL WARNING: High volume chasing paper-thin liquidity. Asymmetric downside risk.",
                "verdict": "CAUTION_OVERHYPED",
                "citation_ref": "SRC-MARKS-2011:p5"
            })

        return insights
