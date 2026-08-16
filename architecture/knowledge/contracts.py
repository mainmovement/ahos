#!/usr/bin/env python3
"""AHOS Global Knowledge & Trust Hierarchy Contracts (Phase XXII - K-01/K-02/K-03).

Non-negotiable Laws:
  - DATA > AI: Evidence always overrules AI opinions, expert claims, and model outputs.
  - Strict Hierarchy: Trust classes MUST NOT silently collapse into one another.
  - Deterministic Decision Floor: Council and Lenses are ADVISORY only; they never DECIDE.
  - Provenance Mandate: Every material fact, claim, and lens insight carries verifiable citation/provenance.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field, asdict
from typing import Any


class TrustClass(enum.Enum):
    """Strict hierarchy of epistemic trustworthiness. Rank 7 is highest, 1 is lowest."""
    RAW_FACT = "RAW_FACT"                         # Rank 7: Cryptographic proofs, on-chain state, raw bytecode
    VERIFIED_PRIMARY = "VERIFIED_PRIMARY"         # Rank 6: Official source code, peer-reviewed foundational math
    SECONDARY = "SECONDARY"                       # Rank 5: Verified aggregate feeds (Gecko, DexScreener, chain explorers)
    EXPERT_INTERPRETATION = "EXPERT_INTERPRETATION" # Rank 4: Peer-reviewed papers, published books by verified thinkers
    AI_INTERPRETATION = "AI_INTERPRETATION"       # Rank 3: LLM reasoning/summary (Advisory only)
    HYPOTHESIS = "HYPOTHESIS"                     # Rank 2: Formulated testable conjecture awaiting validation
    SPECULATION = "SPECULATION"                   # Rank 1: Social sentiment, unverified forum claims, rumors

    @property
    def rank(self) -> int:
        ranks = {
            "RAW_FACT": 7,
            "VERIFIED_PRIMARY": 6,
            "SECONDARY": 5,
            "EXPERT_INTERPRETATION": 4,
            "AI_INTERPRETATION": 3,
            "HYPOTHESIS": 2,
            "SPECULATION": 1,
        }
        return ranks[self.value]

    def is_at_least(self, other: TrustClass) -> bool:
        return self.rank >= other.rank


class KnowledgeDomain(enum.Enum):
    MATHEMATICS = "MATHEMATICS"
    INFORMATION_THEORY = "INFORMATION_THEORY"
    CRYPTOGRAPHY = "CRYPTOGRAPHY"
    DISTRIBUTED_SYSTEMS = "DISTRIBUTED_SYSTEMS"
    BEHAVIORAL_ECONOMICS = "BEHAVIORAL_ECONOMICS"
    MARKET_MICROSTRUCTURE = "MARKET_MICROSTRUCTURE"
    COMPLEX_SYSTEMS = "COMPLEX_SYSTEMS"
    CYBERSECURITY = "CYBERSECURITY"
    GAME_THEORY = "GAME_THEORY"
    ON_CHAIN_ANALYTICS = "ON_CHAIN_ANALYTICS"


class ClaimCategory(enum.Enum):
    CANONICAL = "CANONICAL"
    RESEARCH = "RESEARCH"
    LENS = "LENS"
    MODEL = "MODEL"
    HYPOTHESIS = "HYPOTHESIS"
    UNVERIFIED = "UNVERIFIED"


@dataclass
class KnowledgeSourceRecord:
    source_id: str
    source_name: str
    source_type: str                             # PRIMARY_DOC | CODE_REPO | PAPER | BOOK | DATA_FEED | AGENT
    trust_class: TrustClass
    domain: KnowledgeDomain
    origin: str                                  # URL, DOI, ISBN, Commit SHA
    timestamp: float
    version: str
    license_legal_status: str                    # MIT, Apache-2.0, CC-BY-4.0, Public Domain, Proprietary
    provenance_hash: str
    review_status: str                           # VERIFIED | PENDING_REVIEW | DEPRECATED | REJECTED
    confidence: float                            # 0.0 to 1.0
    known_bias: str
    allowed_use: list[str] = field(default_factory=lambda: ["ANALYZE", "ADVISE", "CHALLENGE"])

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["trust_class"] = self.trust_class.value
        d["domain"] = self.domain.value
        return d


@dataclass
class EvidenceLink:
    evidence_id: str
    source_id: str
    trust_class: TrustClass
    pointer: str                                 # Table rowid, obs_id, tx_hash, formula_ref, DOI
    description: str
    raw_sha256: str
    retrieved_ts: float


@dataclass
class VersionedClaim:
    claim_id: str
    version: int
    category: ClaimCategory
    statement: str
    trust_class: TrustClass
    author_or_source_id: str
    evidence_links: list[EvidenceLink]
    contradicting_evidence_ids: list[str]
    contradiction_edges: list[dict[str, str]]    # [{target_claim_id, reason}]
    provenance_sha256: str
    created_ts: float
    review_status: str                           # ACTIVE | DISPUTED | REFUTED | ARCHIVED
    confidence: float
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExpertLensCard:
    lens_id: str
    identity: str                                # Verified historical thinker / mathematician
    domain: KnowledgeDomain
    public_source_corpus: list[str]              # Canonical publications, papers, books
    verified_principles: list[dict[str, str]]    # [{principle_id, title, formula_or_rule, citation_ref}]
    mental_models: list[str]
    historical_evidence: list[str]
    documented_failures: list[str]               # Known boundary limitations / where the model breaks
    strengths: list[str]
    blind_spots: list[str]
    biases: list[str]
    ahos_applications: list[str]
    citations: list[dict[str, str]]              # [{citation_ref, title, year, publication}]
    provenance: str                              # SHA-256 of verified source corpus
    trust_class: TrustClass = TrustClass.EXPERT_INTERPRETATION
    version: str = "1.0.0"
    confidence: float = 0.95
    review_status: str = "VERIFIED"
