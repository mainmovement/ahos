"""Autonomy tier state management for M43.

This module implements the autonomy tier promotion/demotion system. It tracks
per-market current tier state, validates promotion evidence, and manages the
ledger evidence surface for tier decisions.

Design
------
- Tier decisions are recorded as KIND_DECISION in the mission ledger
- Each promotion requires evidence of performance at the current tier
- Signers validate the promotion according to tier-specific rules
- Tier states are cached locally with expiry checks
- Decisions are bound to specific markets and never global

Constants
----------
- T0–T4: Autonomy tiers from fully manual to fully autonomous
- SIGNERS_PER_TIER: Number of signers required per tier
- TIER_EXPIRY_DAYS: Days before a tier decision must be re-validated
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Set, Optional
from uuid import uuid4

from architecture.mission.ledger import MissionLedger, KIND_DECISION, validate_agent


# ---- constants ---------------------------------------------------------------

class Tier(str, Enum):
    """Autonomy tiers from T0 (fully manual) to T4 (fully autonomous)."""
    T0 = "T0"
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    T4 = "T4"


# Tier promotion requirements
SIGNERS_PER_TIER: Dict[Tier, int] = {
    Tier.T0: 1,  # At least 1 signer for any promotion
    Tier.T1: 2,  # At least 2 signers for T1 promotion
    Tier.T2: 3,  # At least 3 signers for T2 promotion
    Tier.T3: 4,  # At least 4 signers for T3 promotion
    Tier.T4: 5,  # All 5 signers required for T4 promotion
}

# Tier expiry durations (in days)
TIER_EXPIRY_DAYS: Dict[Tier, int] = {
    Tier.T0: 30,   # T0 decisions expire in 30 days
    Tier.T1: 60,   # T1 decisions expire in 60 days
    Tier.T2: 90,   # T2 decisions expire in 90 days
    Tier.T3: 180,  # T3 decisions expire in 180 days
    Tier.T4: 365,  # T4 decisions expire in 1 year
}

# Tier evidence requirements
EVIDENCE_KINDS_PER_TIER: Dict[Tier, Set[str]] = {
    Tier.T0: {"PERFORMANCE_T0"},
    Tier.T1: {"PERFORMANCE_T1", "SAFETY_T0"},
    Tier.T2: {"PERFORMANCE_T2", "SAFETY_T1", "COMPLIANCE_T1"},
    Tier.T3: {"PERFORMANCE_T3", "SAFETY_T2", "COMPLIANCE_T2", "GOVERNANCE_T2"},
    Tier.T4: {"PERFORMANCE_T4", "SAFETY_T3", "COMPLIANCE_T3", "GOVERNANCE_T3", "AUDIT_T3"},
}


# ---- dataclasses -------------------------------------------------------------

@dataclass
class DecisionRecord:
    """M43 autonomy tier decision record with 11 fields from spec."""
    # Core identification
    decision_id: str
    market: str

    # Tier information
    from_tier: Tier
    to_tier: Tier

    # Evidence and validation
    evidence_refs: List[str]
    signers: List[str]
    signers_rejected: List[str] = field(default_factory=list)

    # Authority and timing
    authority: str = "NONE"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Additional metadata
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TierState:
    """Per-market current tier state."""
    market: str
    current_tier: Tier
    decision_id: str  # ID of the decision that set this tier
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: Optional[str] = None

    def is_expired(self) -> bool:
        """Check if this tier state has expired."""
        if self.expires_at is None:
            return False
        try:
            expiry = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
            return datetime.now(timezone.utc) >= expiry
        except (ValueError, TypeError):
            return True


# ---- decision store ----------------------------------------------------------

class DecisionStore:
    """M43 autonomy tier decision store with validation and ledger integration."""

    def __init__(self, ledger: MissionLedger) -> None:
        self.ledger = ledger
        self._cache: Dict[str, TierState] = {}

    def record(self, decision: DecisionRecord) -> Dict[str, Any]:
        """Validate and record a tier promotion decision to the ledger.

        Args:
            decision: DecisionRecord with promotion details

        Returns:
            Ledger entry for the recorded decision

        Raises:
            ValueError: If decision validation fails
            LedgerError: If ledger recording fails
        """
        # Validate decision structure
        self._validate_decision(decision)

        # Convert to ledger format
        payload = {
            "decision_id": decision.decision_id,
            "market": decision.market,
            "from_tier": decision.from_tier.value,
            "to_tier": decision.to_tier.value,
            "evidence_refs": decision.evidence_refs,
            "signers": decision.signers,
            "signers_rejected": decision.signers_rejected,
            "authority": decision.authority,
            "created_at": decision.created_at,
            "metadata": decision.metadata,
            "payload": decision.payload,
        }

        # Record to ledger
        return self.ledger.decision(payload)

    def promote(self, market: str, to_tier: Tier, evidence_refs: List[str],
                signers: List[str], *, authority: str = "NONE",
                from_tier: Optional[Tier] = None, metadata: Optional[Dict[str, Any]] = None) -> DecisionRecord:
        """Promote a market to a higher autonomy tier.

        Args:
            market: Target market identifier
            to_tier: Target tier (must be higher than current)
            evidence_refs: List of evidence references supporting promotion
            signers: List of agent names who approved the promotion
            authority: Authority class making the decision
            from_tier: Source tier (if None, uses current tier)
            metadata: Additional metadata for the decision

        Returns:
            DecisionRecord for the promotion

        Raises:
            ValueError: If promotion validation fails
        """
        # Get current tier
        current = self.current_tier(market)
        if from_tier is None:
            from_tier = current

        # Validate promotion direction
        if to_tier.value <= from_tier.value:
            raise ValueError(f"Cannot promote to {to_tier.value} from {from_tier.value} (must be higher)")

        # Validate signers first (before evidence)
        self.validate_signers(signers, to_tier)

        # Validate evidence requirements
        required_evidence = EVIDENCE_KINDS_PER_TIER.get(from_tier, set())
        provided_evidence = {ref.split(":")[0] for ref in evidence_refs}
        missing_evidence = required_evidence - provided_evidence
        if missing_evidence:
            raise ValueError(f"Missing required evidence: {missing_evidence}")

        # Create decision record
        decision = DecisionRecord(
            decision_id=str(uuid4()),
            market=market,
            from_tier=from_tier,
            to_tier=to_tier,
            evidence_refs=evidence_refs,
            signers=signers,
            authority=authority,
            metadata=metadata or {},
        )

        # Record to ledger
        self.record(decision)

        # Update cache
        expiry_days = TIER_EXPIRY_DAYS.get(to_tier, 30)
        expires_at = (datetime.now(timezone.utc) + timedelta(days=expiry_days)).isoformat()
        self._cache[market] = TierState(
            market=market,
            current_tier=to_tier,
            decision_id=decision.decision_id,
            expires_at=expires_at,
        )

        return decision

    def current_tier(self, market: str) -> Tier:
        """Get the current tier for a market.

        Args:
            market: Target market identifier

        Returns:
            Current Tier for the market
        """
        # Check cache first
        cached = self._cache.get(market)
        if cached and not cached.is_expired():
            return cached.current_tier

        # Check ledger for latest decision
        latest = self.ledger.current_decision(market)
        if latest is None:
            return Tier.T0  # Default to T0 if no decision exists

        # Parse the latest decision
        payload = latest.get("payload", {})
        to_tier = Tier(payload.get("to_tier", "T0"))

        # Update cache
        expiry_days = TIER_EXPIRY_DAYS.get(to_tier, 30)
        expires_at = (datetime.fromisoformat(payload.get("created_at", datetime.now(timezone.utc).isoformat())) +
                     timedelta(days=expiry_days)).isoformat()

        self._cache[market] = TierState(
            market=market,
            current_tier=to_tier,
            decision_id=payload.get("decision_id", str(uuid4())),
            expires_at=expires_at,
        )

        return to_tier

    def check_expiry(self, market: str) -> bool:
        """Check if a market's current tier decision has expired.

        Args:
            market: Target market identifier

        Returns:
            True if the tier decision has expired, False otherwise
        """
        cached = self._cache.get(market)
        if cached:
            return cached.is_expired()

        # If not cached, check if there's any decision at all
        latest = self.ledger.current_decision(market)
        return latest is None

    def validate_signers(self, signers: List[str], target_tier: Tier) -> None:
        """Validate that signers meet tier requirements.

        Args:
            signers: List of agent names who approved
            target_tier: Tier being promoted to

        Raises:
            ValueError: If signer validation fails
        """
        if not isinstance(signers, list):
            raise ValueError("signers must be a list")

        # Check for valid agent format
        for signer in signers:
            validate_agent(signer)

        # Check minimum number of signers
        required = SIGNERS_PER_TIER.get(target_tier, 1)
        if len(signers) < required:
            raise ValueError(f"Need at least {required} signers for {target_tier.value} promotion, got {len(signers)}")

        # Check for duplicate signers
        if len(set(signers)) != len(signers):
            raise ValueError("Duplicate signers not allowed")

    def reject_skip(self, market: str, reason: str) -> Dict[str, Any]:
        """Reject a promotion attempt and skip the market.

        Args:
            market: Target market identifier
            reason: Why the promotion was rejected

        Returns:
            Ledger entry for the rejection
        """
        current = self.current_tier(market)

        # Create rejection decision
        decision = DecisionRecord(
            decision_id=str(uuid4()),
            market=market,
            from_tier=current,
            to_tier=current,  # No change
            evidence_refs=[],
            signers=[],
            signers_rejected=[],
            authority="REJECT_SKIP",
            payload={"reject_reason": reason},
            metadata={"reject_skip": True},
        )

        return self.record(decision)

    def get_decision_history(self, market: str) -> List[Dict[str, Any]]:
        """Get the full decision history for a market.

        Args:
            market: Target market identifier

        Returns:
            List of decision records in chronological order
        """
        all_decisions = self.ledger.decision_history()
        return [d for d in all_decisions if d.get("payload", {}).get("market") == market]

    def _validate_decision(self, decision: DecisionRecord) -> None:
        """Validate a decision record structure.

        Args:
            decision: DecisionRecord to validate

        Raises:
            ValueError: If validation fails
        """
        if not decision.decision_id:
            raise ValueError("decision_id required")

        if not decision.market:
            raise ValueError("market required")

        if not isinstance(decision.from_tier, Tier):
            raise ValueError("from_tier must be a Tier")

        if not isinstance(decision.to_tier, Tier):
            raise ValueError("to_tier must be a Tier")

        # Only require evidence_refs for promotion (not rejection or skip)
        if (not decision.evidence_refs and
            decision.authority != "REJECT_SKIP" and
            not decision.metadata.get("reject_skip", False)):
            raise ValueError("evidence_refs required")

        if not isinstance(decision.evidence_refs, list):
            raise ValueError("evidence_refs must be a list")

        # Ensure evidence refs are strings
        for ref in decision.evidence_refs:
            if not isinstance(ref, str):
                raise ValueError("evidence_refs must contain strings")

        # Validate timestamp format
        try:
            datetime.fromisoformat(decision.created_at.replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("created_at must be ISO format")