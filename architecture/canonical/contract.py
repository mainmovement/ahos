"""Canonical decision contract — the single versioned cross-runtime record.

`CanonicalDecision` is the ONE record every adapter consumes. It reuses the
existing canonical vocabulary from `architecture/security/gate.py`
(SECURITY_VETO / PASS_WITH_UNKNOWN / PASS; caps AVOID / WATCH / PASS) — no new
terminology is introduced.

Authority vs evidence:
  * `opportunity_eligible` is the AUTHORITATIVE eligibility result.
  * `opportunity_score` is evidence/measurement — NOT authority. A high score
    can never, by itself, make a token a positive opportunity.

Validation is fail-closed: a record that does not satisfy every invariant is
invalid, and an invalid record must never be treated as a positive opportunity.
The binding invariant is: opportunity_eligible == True  ⇒  security_disposition == PASS.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from ..security.gate import (
    VERDICT_VETO,
    VERDICT_PASS_WITH_UNKNOWN,
    VERDICT_PASS,
    CAP_AVOID,
    CAP_WATCH,
    CAP_PASS,
)

#: Contract schema version. Bump on any breaking field/semantic change.
DECISION_VERSION = 1
#: Identifies the runtime that produced the record (the sole canonical writer).
CANONICAL_SOURCE = "python-architecture-runtime"
#: Canonical brain version stamp (informational provenance).
BRAIN_VERSION = "1.0.0"

_VALID_DISPOSITIONS = frozenset({VERDICT_VETO, VERDICT_PASS_WITH_UNKNOWN, VERDICT_PASS})
_VALID_CAPS = frozenset({CAP_AVOID, CAP_WATCH, CAP_PASS})


@dataclass(frozen=True)
class CanonicalDecision:
    canonical_token_id: str
    chain: str
    normalized_contract_address: str
    security_disposition: str            # SECURITY_VETO | PASS_WITH_UNKNOWN | PASS
    recommendation_cap: str              # AVOID | WATCH | PASS
    opportunity_eligible: bool           # AUTHORITATIVE eligibility (True ⇒ disposition PASS)
    opportunity_score: float             # evidence/measurement only, NOT authority
    evidence_reference: str              # provenance sha / ledger ref
    decision_timestamp: float            # epoch seconds (UTC) when the decision was produced
    decision_version: int = DECISION_VERSION
    brain_version: str = BRAIN_VERSION
    canonical_source: str = CANONICAL_SOURCE
    # NON-AUTHORITATIVE presentation payload (symbol/name/reasons/… produced by
    # the Python brain) so adapters can DISPLAY a canonical opportunity without
    # recomputing anything. It carries no authority: eligibility/disposition/cap
    # above remain the only decision fields. Optional + additive (version-safe).
    presentation: dict[str, Any] | None = None

    # ------------------------------------------------------------------ #
    def validate(self) -> bool:
        """Fail-closed structural + invariant validation."""
        if not isinstance(self.canonical_token_id, str) or not self.canonical_token_id:
            return False
        if not isinstance(self.chain, str) or not self.chain:
            return False
        if not isinstance(self.normalized_contract_address, str) or not self.normalized_contract_address:
            return False
        if self.security_disposition not in _VALID_DISPOSITIONS:
            return False
        if self.recommendation_cap not in _VALID_CAPS:
            return False
        if not isinstance(self.opportunity_eligible, bool):
            return False
        # THE binding One-Brain invariant: only an explicit PASS may be eligible.
        if self.opportunity_eligible and self.security_disposition != VERDICT_PASS:
            return False
        # UNKNOWN / VETO can never be eligible.
        if self.security_disposition in (VERDICT_VETO, VERDICT_PASS_WITH_UNKNOWN) and self.opportunity_eligible:
            return False
        if not isinstance(self.opportunity_score, (int, float)):
            return False
        if not isinstance(self.decision_version, int) or self.decision_version < 1:
            return False
        if self.decision_version != DECISION_VERSION:
            return False
        if not isinstance(self.decision_timestamp, (int, float)) or self.decision_timestamp <= 0:
            return False
        return True

    def is_stale(self, now: float, budget_sec: float) -> bool:
        """True when the decision is older than the freshness budget."""
        try:
            return (now - float(self.decision_timestamp)) > float(budget_sec)
        except (TypeError, ValueError):
            return True  # unparseable timestamp ⇒ treat as stale (fail-closed)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Any) -> "CanonicalDecision | None":
        """Reconstruct a record; returns None (fail-closed) on any malformation."""
        if not isinstance(data, dict):
            return None
        try:
            rec = CanonicalDecision(
                canonical_token_id=data["canonical_token_id"],
                chain=data["chain"],
                normalized_contract_address=data["normalized_contract_address"],
                security_disposition=data["security_disposition"],
                recommendation_cap=data["recommendation_cap"],
                opportunity_eligible=bool(data["opportunity_eligible"]),
                opportunity_score=float(data["opportunity_score"]),
                evidence_reference=str(data.get("evidence_reference", "")),
                decision_timestamp=float(data["decision_timestamp"]),
                decision_version=int(data.get("decision_version", DECISION_VERSION)),
                brain_version=str(data.get("brain_version", BRAIN_VERSION)),
                canonical_source=str(data.get("canonical_source", CANONICAL_SOURCE)),
                presentation=data.get("presentation") if isinstance(data.get("presentation"), dict) else None,
            )
        except (KeyError, TypeError, ValueError):
            return None
        return rec if rec.validate() else None
