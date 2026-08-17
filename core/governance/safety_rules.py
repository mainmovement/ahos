"""
core.governance.safety_rules — Paper-only safety gate.

Every future action in AHOS v2 must pass through SafetyEngine.
Core laws enforced here (same as AHOS_PROJECT_STATE_MAP / docs/canonical/SECURITY):

* PAPER_ONLY — no live execution path may exist.
* NO_WALLET_SIGNING — signing primitives (sign_transaction etc.) are forbidden.
* NO_REAL_TRADING — SDKs for ccxt, web3 live trading, exchange order placement are forbidden.
* EVIDENCE_REQUIRED — every Decision must cite ≥1 Evidence (except INSUFFICIENT_EVIDENCE).
* VERIFICATION_REQUIRED — critical actions require VERIFIED or at least DERIVED evidence when available.
* SECRETS_NOT_IN_CODE — no bot token, private key, or api key pattern in stored text.
* RATE_LIMITED — provider writes must not exceed budget (delegated to providers layer).

The engine is pure (no I/O); callers interpret violations and downgrade
to WAIT/AVOID or force human review via governance flow.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from ..models.evidence import Evidence, Confidence, VerificationStatus
from ..models.decision import Decision, DecisionAction
from ..events.event_types import Event, EventType

# ---------------------------------------------------------------------------
# Rule identifiers — controlled vocabulary, never renamed.
# ---------------------------------------------------------------------------

class SafetyRule:
    PAPER_ONLY = "PAPER_ONLY"
    NO_WALLET_SIGNING = "NO_WALLET_SIGNING"
    NO_REAL_TRADING = "NO_REAL_TRADING"
    EVIDENCE_REQUIRED = "EVIDENCE_REQUIRED"
    VERIFICATION_REQUIRED = "VERIFICATION_REQUIRED"
    SECRETS_NOT_IN_CODE = "SECRETS_NOT_IN_CODE"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"

    ALL = (
        PAPER_ONLY,
        NO_WALLET_SIGNING,
        NO_REAL_TRADING,
        EVIDENCE_REQUIRED,
        VERIFICATION_REQUIRED,
        SECRETS_NOT_IN_CODE,
        STALE_EVIDENCE,
        HUMAN_REVIEW_REQUIRED,
    )


# ---------------------------------------------------------------------------
# Forbidden primitives — paper-only invariant.
# Any source file containing these strings must be rejected at PR time
# (see tests/test_zero_money_invariant.py). This engine lint re-checks
# textual payloads at runtime as defense-in-depth.
# ---------------------------------------------------------------------------

_FORBIDDEN_TRADING_PATTERNS: list[tuple[str, str]] = [
    (r"\bsign_transaction\b", "transaction signing"),
    (r"\bsignTransaction\b", "transaction signing"),
    (r"\bsend_transaction\b", "transaction broadcast"),
    (r"\bsendTransaction\b", "transaction broadcast"),
    (r"\bsend_raw_transaction\b", "raw transaction broadcast"),
    (r"\bsendRawTransaction\b", "raw transaction broadcast"),
    (r"\beth_sendTransaction\b", "EVM transaction broadcast"),
    (r"\beth_signTransaction\b", "EVM transaction signing"),
    (r"\bpersonal_sign\b", "wallet signing"),
    (r"\bcreate_order\b", "exchange order placement"),
    (r"\bplace_order\b", "exchange order placement"),
    (r"\bcreate_market_buy\b", "exchange market order"),
    (r"\bcreate_market_sell\b", "exchange market order"),
    (r"\bwallet\.sign\b", "wallet signing"),
    (r"\bprivate_key\b", "private key reference"),
    (r"\bmnemonic\b", "mnemonic reference"),
]

_FORBIDDEN_IMPORT_PATTERNS: list[tuple[str, str]] = [
    (r"\bimport\s+ccxt\b", "ccxt trading SDK"),
    (r"\bfrom\s+ccxt\b", "ccxt trading SDK"),
    (r"\bimport\s+web3\b", "web3 trading SDK"),
    (r"\bfrom\s+solana\b", "solana wallet SDK (raw)"),
    (r"\bbip39\b", "BIP-39 mnemonic"),
]

_SECRET_PATTERNS: list[str] = [
    r"\b[0-9]{8,12}:[a-zA-Z0-9_-]{30,50}\b",  # Telegram bot token
    r"sk-[a-zA-Z0-9]{20,}",  # OpenAI
    r"0x[0-9a-fA-F]{64}\b",  # EVM private key
]

_COMPILED_TRADING = [(re.compile(p, re.IGNORECASE), name) for p, name in _FORBIDDEN_TRADING_PATTERNS]
_COMPILED_IMPORTS = [(re.compile(p, re.IGNORECASE), name) for p, name in _FORBIDDEN_IMPORT_PATTERNS]
_COMPILED_SECRETS = [re.compile(p) for p in _SECRET_PATTERNS]


def _contains_trading_primitive(text: str) -> list[str]:
    hits: list[str] = []
    low = text or ""
    for pat, name in _COMPILED_TRADING:
        if pat.search(low):
            hits.append(name)
    for pat, name in _COMPILED_IMPORTS:
        if pat.search(low):
            hits.append(name)
    return sorted(set(hits))


def _contains_secret_like(text: str) -> bool:
    for pat in _COMPILED_SECRETS:
        if pat.search(text or ""):
            return True
    return False


# ---------------------------------------------------------------------------
# Violation type
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SafetyViolation:
    rule: str
    reason: str
    severity: str = "HIGH"  # CRITICAL | HIGH | MED | LOW
    evidence: str = ""      # optional snippet (sanitized) showing the trigger

    def to_dict(self) -> dict[str, Any]:
        return {"rule": self.rule, "reason": self.reason, "severity": self.severity, "evidence": self.evidence}


# ---------------------------------------------------------------------------
# Safety engine — pure, injectable
# ---------------------------------------------------------------------------

@dataclass
class SafetyEngine:
    """
    Pure safety gate.

    Parameters
    ----------
    paper_only: when True, any allowed trading primitive is a violation (default True).
    require_verification_for_enter: when True, ENTER decisions must carry at least
            one Evidence with VERIFIED/DERIVED status (default True).
    stale_after_seconds: evidence considered stale (default 4h).
    enforce_human_review: when True, INSUFFICIENT_EVIDENCE / LOW confidence actions
            are flagged for human review (default True).

    Stateless except for config — safe to share across evaluations.
    """

    paper_only: bool = True
    require_verification_for_enter: bool = True
    stale_after_seconds: float = 4 * 3600
    enforce_human_review: bool = True

    # ------------------------------------------------------------------
    # Public: evaluate arbitrary textual code / rationale for violations
    # ------------------------------------------------------------------

    def check_text(self, text: str, context: str = "") -> list[SafetyViolation]:
        violations: list[SafetyViolation] = []
        trading_hits = _contains_trading_primitive(text or "")
        for hit in trading_hits:
            violations.append(
                SafetyViolation(
                    rule=SafetyRule.NO_WALLET_SIGNING if "sign" in hit or "private" in hit else SafetyRule.NO_REAL_TRADING,
                    reason=f"Forbidden trading primitive detected ({hit})" + (f" in {context}" if context else ""),
                    severity="CRITICAL",
                    evidence=hit,
                )
            )
        if _contains_secret_like(text or ""):
            violations.append(
                SafetyViolation(
                    rule=SafetyRule.SECRETS_NOT_IN_CODE,
                    reason="Secret-like pattern detected in stored text" + (f" ({context})" if context else ""),
                    severity="HIGH",
                    evidence="[REDACTED]",
                )
            )
        return violations

    # ------------------------------------------------------------------
    # Public: evaluate Evidence / Decision / Event for governance
    # ------------------------------------------------------------------

    def evaluate_evidence(self, evidence: Evidence) -> list[SafetyViolation]:
        v: list[SafetyViolation] = []
        # Paper-only evidence should never claim live execution
        if evidence.source.strip().lower() in ("live_trade", "execute", "real_order"):
            v.append(
                SafetyViolation(
                    rule=SafetyRule.PAPER_ONLY,
                    reason="Evidence claims live execution — paper-only violation",
                    severity="CRITICAL",
                    evidence=evidence.source,
                )
            )
        if evidence.is_unknown and evidence.verification_status == VerificationStatus.REJECTED:
            # Inconsistent state — UNKNOWN confidence cannot be REJECTED
            v.append(
                SafetyViolation(
                    rule=SafetyRule.EVIDENCE_REQUIRED,
                    reason="Evidence in inconsistent UNKNOWN/REJECTED state",
                    severity="MED",
                )
            )
        # Stale check (advisory, not blocking, but surfaces gap)
        if evidence.age_seconds > self.stale_after_seconds and evidence.verification_status not in (
            VerificationStatus.STALE,
            VerificationStatus.UNKNOWN,
        ):
            v.append(
                SafetyViolation(
                    rule=SafetyRule.STALE_EVIDENCE,
                    reason=f"Evidence age {evidence.age_seconds:.0f}s exceeds {self.stale_after_seconds:.0f}s window",
                    severity="LOW",
                    evidence=evidence.evidence_id[:12],
                )
            )
        # Secrets in metadata
        if evidence.metadata:
            for k in evidence.metadata:
                if _contains_secret_like(str(k)) or _contains_secret_like(str(evidence.metadata[k])):
                    v.append(
                        SafetyViolation(
                            rule=SafetyRule.SECRETS_NOT_IN_CODE,
                            reason="Evidence metadata appears to contain a secret",
                            severity="HIGH",
                        )
                    )
                    break
        return v

    def evaluate_decision(self, decision: Decision) -> list[SafetyViolation]:
        v: list[SafetyViolation] = []
        # Law: advisory_only must always be True
        if not decision.advisory_only:
            v.append(
                SafetyViolation(
                    rule=SafetyRule.PAPER_ONLY,
                    reason="Decision.advisory_only must be True — live execution is forbidden",
                    severity="CRITICAL",
                )
            )
        # Law: rationale must not contain trading primitives or secrets
        v.extend(self.check_text(decision.rationale, "Decision.rationale"))
        for r in decision.risks:
            txt = r.get("description", "") if isinstance(r, dict) else str(r)
            v.extend(self.check_text(txt, "Decision.risks"))

        # Law: evidence required (except INSUFFICIENT_EVIDENCE)
        if decision.action != DecisionAction.INSUFFICIENT_EVIDENCE and not decision.evidence_refs:
            v.append(
                SafetyViolation(
                    rule=SafetyRule.EVIDENCE_REQUIRED,
                    reason=f"Decision {decision.action} requires ≥1 Evidence citation",
                    severity="HIGH",
                )
            )

        # Law: verification required for ENTER
        if decision.action == DecisionAction.ENTER and self.require_verification_for_enter:
            if decision.evidence_refs:
                has_verified = any(
                    e.verification_status in (VerificationStatus.VERIFIED, VerificationStatus.DERIVED)
                    for e in decision.evidence_refs
                )
                if not has_verified:
                    v.append(
                        SafetyViolation(
                            rule=SafetyRule.VERIFICATION_REQUIRED,
                            reason="ENTER requires at least one VERIFIED/DERIVED Evidence — none cited",
                            severity="HIGH",
                        )
                    )

        # Law: human review for low confidence / critical actions
        if decision.requires_human_review and self.enforce_human_review:
            # This is not a block — it flags for governance queue
            if decision.confidence == Confidence.LOW or decision.action in (DecisionAction.ENTER,):
                v.append(
                    SafetyViolation(
                        rule=SafetyRule.HUMAN_REVIEW_REQUIRED,
                        reason=f"Decision {decision.action} with confidence={decision.confidence} requires human review",
                        severity="MED",
                        evidence=decision.decision_id[:12],
                    )
                )

        # Check each evidence too
        for ev in decision.evidence_refs:
            v.extend(self.evaluate_evidence(ev))

        return v

    def evaluate_event(self, event: Event) -> list[SafetyViolation]:
        v: list[SafetyViolation] = []
        if event.event_type == EventType.SAFETY_VIOLATION:
            return v  # avoid recursion
        # Event payload must not contain trading primitives
        payload_text = str(event.payload)
        v.extend(self.check_text(payload_text, f"Event[{event.event_type}].payload"))
        return v

    # Convenience
    def is_safe(self, obj: Evidence | Decision | Event | str) -> bool:
        """True when no CRITICAL/HIGH violations."""
        if isinstance(obj, Evidence):
            vs = self.evaluate_evidence(obj)
        elif isinstance(obj, Decision):
            vs = self.evaluate_decision(obj)
        elif isinstance(obj, Event):
            vs = self.evaluate_event(obj)
        elif isinstance(obj, str):
            vs = self.check_text(obj)
        else:
            raise TypeError(f"Unknown type for safety check: {type(obj).__name__}")
        return not any(x.severity in ("CRITICAL", "HIGH") for x in vs)

    def assert_safe(self, obj: Evidence | Decision | Event | str) -> None:
        """Raise PermissionError on any CRITICAL/HIGH violation (fail-closed)."""
        if isinstance(obj, Evidence):
            vs = self.evaluate_evidence(obj)
        elif isinstance(obj, Decision):
            vs = self.evaluate_decision(obj)
        elif isinstance(obj, Event):
            vs = self.evaluate_event(obj)
        elif isinstance(obj, str):
            vs = self.check_text(obj)
        else:
            raise TypeError(type(obj).__name__)
        critical = [x for x in vs if x.severity in ("CRITICAL", "HIGH")]
        if critical:
            reasons = "; ".join(f"[{x.rule}] {x.reason}" for x in critical)
            raise PermissionError(f"SAFETY VETO — {reasons}")

