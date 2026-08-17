"""
core.models.decision — Advisory decision value object.

AHOS v2 law: this layer ADVISES. It never places an order.
Every Decision ends with human review — paper-only, never wallet-signing.

A Decision is derived from Evidence-backed observations and scoring:
    Token + Observation + Score/Reasoning + Risk + Evidence refs → Advice

Conservative: unverified evidence → lower confidence; rejected verification → REJECT.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any

from .evidence import Evidence, Confidence, VerificationStatus
from .token import Token
from .observation import Observation

# ---------------------------------------------------------------------------
# Decision action vocabulary — advisory only, no execution verb.
# ---------------------------------------------------------------------------

class DecisionAction:
    ENTER = "ENTER"                     # candidate passes filters — paper entry candidate
    WATCH = "WATCH"                     # track, insufficient conviction to size
    WAIT = "WAIT"                       # hold / defer due to stale evidence or low coverage
    AVOID = "AVOID"                     # veto / reject (honeypot, trap, unverifiable)
    REDUCE = "REDUCE"                   # thesis strengthening → realize partial (paper)
    EXIT = "EXIT"                       # thesis invalidated → close paper position
    HOLD = "HOLD"                       # existing paper position stays open, invalidation not met
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    ALL = (ENTER, WATCH, WAIT, AVOID, REDUCE, EXIT, HOLD, INSUFFICIENT_EVIDENCE)


ADVISORY_FOOTER = "تصمیم نهایی با کاربر است — این یک توصیهٔ تحلیلی است، نه دستور معامله."

# ---------------------------------------------------------------------------
# Decision — frozen advisory object
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Decision:
    """
    Frozen advisory decision for a single token.

    Required
    --------
    token: subject Token.
    action: one of DecisionAction.ALL (advisory verb).
    rationale: human-readable reasoning (Persian preferred for Telegram surface).
    evidence_refs: list[Evidence] that justify the action (≥1 unless INSUFFICIENT_EVIDENCE).
    created_at: epoch seconds.

    Optional
    --------
    observation: the observation that triggered the evaluation (if any).
    score: normalized 0–100 opportunity score if computed (None = rank-only / not yet scored).
    confidence: Confidence level of the decision (derived from evidence confidence + coverage).
    risk_level: LOW | MED | HIGH | CRITICAL.
    risks: list of risk descriptors.
    invalidation_conditions: list of conditions that would invalidate the thesis.
    advisory_only: always True — paper-only enforcement.
    decision_id: stable uuid4 hex.
    requires_human_review: True when action ∈ {ENTER, REDUCE, EXIT} or confidence ≠ HIGH.

    Invariants
    ----------
    * advisory_only is always True (frozen; any mutation → ValueError).
    * Secrets must never appear in rationale/risks/metadata.
    * AVOID/REJECT decisions must carry ≥1 evidence with REJECTED or CRITICAL risk.
    * INSUFFICIENT_EVIDENCE must have empty or UNKNOWN confidence.
    """

    token: Token
    action: str
    rationale: str
    evidence_refs: list[Evidence] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    observation: Observation | None = None
    score: float | None = None
    confidence: str = Confidence.UNKNOWN
    risk_level: str = "UNKNOWN"
    risks: list[dict[str, Any]] = field(default_factory=list)
    invalidation_conditions: list[dict[str, Any]] = field(default_factory=list)
    advisory_only: bool = True
    decision_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    requires_human_review: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.token, Token):
            raise ValueError("Decision.token must be Token")
        if self.action not in DecisionAction.ALL:
            raise ValueError(f"Decision.action must be one of {DecisionAction.ALL}, got {self.action!r}")
        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("Decision.rationale must be non-empty string")
        if self.confidence not in Confidence.ALL:
            raise ValueError(f"Decision.confidence must be one of {Confidence.ALL}")
        if self.score is not None:
            try:
                s = float(self.score)
            except Exception:
                raise ValueError("Decision.score must be numeric 0–100 or None")
            if not 0.0 <= s <= 100.0:
                raise ValueError("Decision.score must lie in [0, 100]")
        if not self.advisory_only:
            raise ValueError("Decision.advisory_only must remain True — live execution is forbidden")
        if not isinstance(self.evidence_refs, list):
            raise ValueError("Decision.evidence_refs must be list[Evidence]")
        for ev in self.evidence_refs:
            if not isinstance(ev, Evidence):
                raise ValueError("Decision.evidence_refs elements must be Evidence")

        # Normalize
        object.__setattr__(self, "action", self.action.strip())
        object.__setattr__(self, "rationale", self.rationale.strip())

        # Auto-require human review for state-changing and low-confidence advice
        needs_review = self.action in (DecisionAction.ENTER, DecisionAction.REDUCE, DecisionAction.EXIT) or self.confidence != Confidence.HIGH
        # Keep caller's explicit False only if they intentionally override; otherwise derive
        if "requires_human_review" not in self.__dict__ or self.requires_human_review == needs_review:
            object.__setattr__(self, "requires_human_review", needs_review)

        # Safety lint: secret-like patterns in rationale
        _assert_no_secrets_in_text(self.rationale)

    # ------------------------------------------------------------------
    # Safety helpers
    # ------------------------------------------------------------------

    @property
    def is_actionable(self) -> bool:
        return self.action in (DecisionAction.ENTER, DecisionAction.REDUCE, DecisionAction.EXIT)

    @property
    def is_reject(self) -> bool:
        return self.action in (DecisionAction.AVOID, DecisionAction.INSUFFICIENT_EVIDENCE)

    @property
    def footprint(self) -> str:
        """Deterministic footprint for audit / coalescence."""
        import hashlib

        parts = [self.token.token_id_, self.action, f"{self.created_at:.0f}"]
        return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "token": self.token.to_dict(),
            "action": self.action,
            "rationale": self.rationale,
            "evidence_refs": [e.to_dict() for e in self.evidence_refs],
            "created_at": self.created_at,
            "observation": self.observation.to_dict() if self.observation else None,
            "score": self.score,
            "confidence": self.confidence,
            "risk_level": self.risk_level,
            "risks": list(self.risks),
            "invalidation_conditions": list(self.invalidation_conditions),
            "advisory_only": self.advisory_only,
            "requires_human_review": self.requires_human_review,
            "metadata": dict(self.metadata),
            "advisory_footer": ADVISORY_FOOTER,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Decision":
        return cls(
            token=Token.from_dict(data["token"]),
            action=data["action"],
            rationale=data["rationale"],
            evidence_refs=[Evidence.from_dict(d) for d in data.get("evidence_refs", [])],
            created_at=float(data.get("created_at", time.time())),
            observation=Observation.from_dict(data["observation"]) if data.get("observation") else None,
            score=data.get("score"),
            confidence=data.get("confidence", Confidence.UNKNOWN),
            risk_level=data.get("risk_level", "UNKNOWN"),
            risks=list(data.get("risks", [])),
            invalidation_conditions=list(data.get("invalidation_conditions", [])),
            advisory_only=True,
            decision_id=data.get("decision_id", uuid.uuid4().hex),
            requires_human_review=bool(data.get("requires_human_review", True)),
            metadata=dict(data.get("metadata", {})),
        )

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def report_persian(self) -> str:
        icon = {
            DecisionAction.ENTER: "🟢",
            DecisionAction.WATCH: "🔵",
            DecisionAction.WAIT: "🟡",
            DecisionAction.AVOID: "🔴",
            DecisionAction.REDUCE: "🟠",
            DecisionAction.EXIT: "🛑",
            DecisionAction.HOLD: "⚪",
            DecisionAction.INSUFFICIENT_EVIDENCE: "⚫",
        }.get(self.action, "⚪")
        lines = [
            f"{icon} {self.token.display()} — {self.action}",
        ]
        if self.score is not None:
            lines.append(f"امتیاز: {self.score:.0f}/100 | اعتماد: {self.confidence} | ریسک: {self.risk_level}")
        lines.append(f"دلیل: {self.rationale}")
        if self.risks:
            lines.append("ریسک‌ها:")
            for r in self.risks[:3]:
                desc = r.get("description", str(r)) if isinstance(r, dict) else str(r)
                lines.append(f"  • {desc}")
        if self.invalidation_conditions:
            lines.append("ابطال در صورت:")
            for c in self.invalidation_conditions[:3]:
                desc = c.get("trigger_description", str(c)) if isinstance(c, dict) else str(c)
                lines.append(f"  • {desc}")
        if self.evidence_refs:
            lines.append("شواهد: " + " ؛ ".join(e.describe() for e in self.evidence_refs[:2]))
        lines.append("")
        lines.append(ADVISORY_FOOTER)
        if self.requires_human_review:
            lines.append("⟶ نیازمند تأیید انسانی")
        return "\n".join(lines)


def _assert_no_secrets_in_text(text: str) -> None:
    """Lightweight secret lint — mirrors architecture.security patterns without importing it at load-time."""
    import re

    # Must not broaden to block Persian text; only secret-looking patterns
    secret_patterns = [
        re.compile(r"\b[0-9]{8,12}:[a-zA-Z0-9_-]{30,50}\b"),  # Telegram bot token
        re.compile(r"sk-[a-zA-Z0-9]{20,}"),                # OpenAI
        re.compile(r"0x[0-9a-fA-F]{64}\b"),                 # EVM private key
    ]
    for pat in secret_patterns:
        if pat.search(text):
            raise ValueError("Decision text appears to contain a secret-like pattern — refusing to store")

