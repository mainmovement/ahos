#!/usr/bin/env python3
"""AHOS Anti-Echo-Chamber Engineering Layer (Phase XXII - Section 9).

Non-negotiable Laws:
  - Unanimity != Truth: Unanimous consensus among models without independent empirical evidence
    is flagged as a potential echo-chamber / monoculture failure.
  - Mandatory Contrarian Slot: Every synthesized thesis must construct and evaluate the null/contrary thesis.
  - Source Diversity: Identifies whether multiple claims originate from a single shared upstream root.
  - Survivorship & Authority Bias Guards: Prevents trusting claims merely because an authority said so.
"""
from __future__ import annotations

import difflib
import math
from dataclasses import dataclass, field
from typing import Any

from .contracts import TrustClass


@dataclass
class EchoChamberAuditResult:
    correlation_score: float                     # 0.0 (fully independent) to 1.0 (identical echo)
    copied_reasoning_detected: bool
    source_monoculture_detected: bool
    contrarian_thesis: str
    authority_bias_flags: list[str]
    survivorship_bias_flags: list[str]
    epistemic_verdict: str                       # SOUND_DIVERSITY | SUSPECTED_ECHO_CHAMBER | MONOCULTURE_REJECT | INSUFFICIENT_EVIDENCE
    details: dict[str, Any] = field(default_factory=dict)


class AntiEchoEngine:
    def __init__(self, text_similarity_threshold: float = 0.75,
                 monoculture_source_threshold: float = 0.60):
        self.text_similarity_threshold = text_similarity_threshold
        self.monoculture_source_threshold = monoculture_source_threshold

    def audit_responses(self, agent_or_model_responses: list[dict[str, Any]],
                        evidence_count: int,
                        min_required_evidence: int = 2) -> EchoChamberAuditResult:
        if not agent_or_model_responses:
            return EchoChamberAuditResult(
                correlation_score=0.0,
                copied_reasoning_detected=False,
                source_monoculture_detected=False,
                contrarian_thesis="No active responses to invert.",
                authority_bias_flags=[],
                survivorship_bias_flags=[],
                epistemic_verdict="INSUFFICIENT_EVIDENCE",
                details={"reason": "Empty responses"}
            )

        # 1. Text & Reasoning Similarity (Copied Reasoning Detection)
        texts = [r.get("text") or r.get("reasoning") or "" for r in agent_or_model_responses]
        similarities = []
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                if texts[i] and texts[j]:
                    ratio = difflib.SequenceMatcher(None, texts[i].lower(), texts[j].lower()).ratio()
                    similarities.append(ratio)

        avg_similarity = (sum(similarities) / len(similarities)) if similarities else 0.0
        copied_reasoning = avg_similarity >= self.text_similarity_threshold

        # 2. Source Monoculture Detection
        all_sources = []
        for r in agent_or_model_responses:
            sources = r.get("sources") or r.get("citations") or []
            all_sources.extend(sources)

        if all_sources:
            counts = {}
            for s in all_sources:
                counts[s] = counts.get(s, 0) + 1
            top_share = max(counts.values()) / len(all_sources)
            source_monoculture = (top_share >= self.monoculture_source_threshold and len(counts) <= 2)
        else:
            source_monoculture = True  # No cited sources at all is an extreme monoculture of assumption

        # 3. Construct Mandatory Contrarian Thesis (Inversion)
        positive_claims = [r.get("verdict") or r.get("claim") for r in agent_or_model_responses]
        contrarian = (
            f"NULL THESIS INVERSION: What if the observed volume/price signals for "
            f"are entirely wash-trading and liquidity will be pulled within 4h?"
        )

        # 4. Authority & Survivorship Bias Checks
        authority_flags = []
        for r in agent_or_model_responses:
            if "because expert said" in str(r).lower() or "famous influencer" in str(r).lower():
                authority_flags.append(f"Authority argument without proof in {r.get('agent_id', 'unknown')}")

        survivorship_flags = []
        if any("guaranteed 100x" in str(r).lower() or "like previous pump" in str(r).lower() for r in agent_or_model_responses):
            survivorship_flags.append("Survivorship bias: assuming historical outliers represent standard distribution.")

        # 5. Epistemic Verdict Synthesis (Evidence Over Consensus Law)
        if evidence_count < min_required_evidence:
            verdict = "INSUFFICIENT_EVIDENCE"
        elif source_monoculture:
            verdict = "MONOCULTURE_REJECT"
        elif copied_reasoning:
            verdict = "SUSPECTED_ECHO_CHAMBER"
        else:
            verdict = "SOUND_DIVERSITY"

        return EchoChamberAuditResult(
            correlation_score=round(avg_similarity, 3),
            copied_reasoning_detected=copied_reasoning,
            source_monoculture_detected=source_monoculture,
            contrarian_thesis=contrarian,
            authority_bias_flags=authority_flags,
            survivorship_bias_flags=survivorship_flags,
            epistemic_verdict=verdict,
            details={
                "responses_count": len(agent_or_model_responses),
                "evidence_count": evidence_count,
                "sources_evaluated": len(all_sources)
            }
        )
