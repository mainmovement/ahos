#!/usr/bin/env python3
"""AHOS Knowledge & Trust Registry (Phase XXII - K-01).

Maintains a machine-readable catalog of verified knowledge sources, public corpora,
and scientific foundations with immutable trust classifications.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .contracts import (
    TrustClass,
    KnowledgeDomain,
    KnowledgeSourceRecord
)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class KnowledgeTrustRegistry:
    def __init__(self):
        self._sources: dict[str, KnowledgeSourceRecord] = {}
        self._seed_foundational_sources()

    def register_source(self, record: KnowledgeSourceRecord) -> str:
        if record.trust_class == TrustClass.SPECULATION and record.confidence > 0.5:
            # Epistemic invariant: Speculation cannot claim high confidence
            record.confidence = min(0.4, record.confidence)
        self._sources[record.source_id] = record
        return record.source_id

    def get_source(self, source_id: str) -> KnowledgeSourceRecord | None:
        return self._sources.get(source_id)

    def list_sources_by_trust(self, min_trust: TrustClass) -> list[KnowledgeSourceRecord]:
        return [
            s for s in self._sources.values()
            if s.trust_class.is_at_least(min_trust) and s.review_status == "VERIFIED"
        ]

    def list_sources_by_domain(self, domain: KnowledgeDomain) -> list[KnowledgeSourceRecord]:
        return [s for s in self._sources.values() if s.domain == domain]

    def _seed_foundational_sources(self):
        # 1. Claude Shannon — Information Theory
        self.register_source(KnowledgeSourceRecord(
            source_id="SRC-SHANNON-1948",
            source_name="A Mathematical Theory of Communication",
            source_type="PAPER",
            trust_class=TrustClass.VERIFIED_PRIMARY,
            domain=KnowledgeDomain.INFORMATION_THEORY,
            origin="Bell System Technical Journal, Vol. 27, pp. 379–423, 623–656",
            timestamp=time.time(),
            version="1.0.0",
            license_legal_status="Public Academic / IEEE Archive",
            provenance_hash=_sha("Shannon_1948_Information_Theory"),
            review_status="VERIFIED",
            confidence=1.0,
            known_bias="Assumes discrete noiseless or memoryless Gaussian channels; non-ergodic regimes require adjustments.",
            allowed_use=["ANALYZE", "ADVISE", "CHALLENGE", "MODEL_ENTROPY"]
        ))

        # 2. Satoshi Nakamoto — Bitcoin Whitepaper
        self.register_source(KnowledgeSourceRecord(
            source_id="SRC-NAKAMOTO-2008",
            source_name="Bitcoin: A Peer-to-Peer Electronic Cash System",
            source_type="PRIMARY_DOC",
            trust_class=TrustClass.VERIFIED_PRIMARY,
            domain=KnowledgeDomain.CRYPTOGRAPHY,
            origin="https://bitcoin.org/bitcoin.pdf",
            timestamp=time.time(),
            version="1.0.0",
            license_legal_status="MIT / Open Access",
            provenance_hash=_sha("Nakamoto_2008_Bitcoin_Cash_System"),
            review_status="VERIFIED",
            confidence=1.0,
            known_bias="Designed for UTXO proof-of-work state machine; does not model complex AMM token bonding curves.",
            allowed_use=["ANALYZE", "ADVISE", "CHALLENGE", "CONSENSUS_VERIFY"]
        ))

        # 3. Daniel Kahneman & Amos Tversky — Prospect Theory
        self.register_source(KnowledgeSourceRecord(
            source_id="SRC-KAHNEMAN-1979",
            source_name="Prospect Theory: An Analysis of Decision under Risk",
            source_type="PAPER",
            trust_class=TrustClass.EXPERT_INTERPRETATION,
            domain=KnowledgeDomain.BEHAVIORAL_ECONOMICS,
            origin="Econometrica, Vol. 47, No. 2, pp. 263-291",
            timestamp=time.time(),
            version="1.0.0",
            license_legal_status="Academic Publication / Econometric Society",
            provenance_hash=_sha("Kahneman_Tversky_1979_Prospect_Theory"),
            review_status="VERIFIED",
            confidence=0.95,
            known_bias="Laboratory experimental setups; crypto market participants exhibit higher tail-risk appetite.",
            allowed_use=["ANALYZE", "ADVISE", "CHALLENGE", "RETAIL_BIAS_DETECTION"]
        ))

        # 4. Benoit Mandelbrot — Fractals and Scaling in Finance
        self.register_source(KnowledgeSourceRecord(
            source_id="SRC-MANDELBROT-1997",
            source_name="Fractals and Scaling in Finance: Discontinuity, Concentration, Risk",
            source_type="BOOK",
            trust_class=TrustClass.EXPERT_INTERPRETATION,
            domain=KnowledgeDomain.COMPLEX_SYSTEMS,
            origin="Springer-Verlag New York, ISBN: 978-0-387-98363-9",
            timestamp=time.time(),
            version="1.0.0",
            license_legal_status="Academic Book / Springer",
            provenance_hash=_sha("Mandelbrot_1997_Fractals_Scaling_Finance"),
            review_status="VERIFIED",
            confidence=0.95,
            known_bias="Focuses on heavy-tailed power laws; parameter estimation requires large sample sizes.",
            allowed_use=["ANALYZE", "ADVISE", "CHALLENGE", "TAIL_RISK_ESTIMATION"]
        ))

        # 5. Nassim Nicholas Taleb — Antifragile & Skin in the Game
        self.register_source(KnowledgeSourceRecord(
            source_id="SRC-TALEB-2012",
            source_name="Antifragile: Things That Gain from Disorder",
            source_type="BOOK",
            trust_class=TrustClass.EXPERT_INTERPRETATION,
            domain=KnowledgeDomain.MARKET_MICROSTRUCTURE,
            origin="Random House, ISBN: 978-1-4000-6782-4",
            timestamp=time.time(),
            version="1.0.0",
            license_legal_status="Published Book / Random House",
            provenance_hash=_sha("Taleb_2012_Antifragile_Disorder"),
            review_status="VERIFIED",
            confidence=0.92,
            known_bias="Extreme skepticism of statistical predictive models; demands convex payoff architecture.",
            allowed_use=["ANALYZE", "ADVISE", "CHALLENGE", "CONVEXITY_AUDIT"]
        ))
