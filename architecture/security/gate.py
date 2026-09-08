#!/usr/bin/env python3
"""Lane B security-gate overlay.

Composes frozen Lane A `discovery.security_gate.evaluate` without renaming its
enums. Lane A stays:

    SECURITY_VETO / PASS_WITH_UNKNOWN / PASS

Lane B overlay:

    REJECT ⇐ SECURITY_VETO or confirmed extra-critical (unsellable / trapped)
    INCOMPLETE ⇐ PASS_WITH_UNKNOWN or unknown extra-critical
    STALE ⇐ aged evidence that is not an active REJECT
    PASS ⇐ Lane A PASS and all overlay criticals resolved FALSE

UNKNOWN critical evidence is never treated as safe.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from architecture.providers.contracts import NormalizedTokenCandidate, SecuritySignals

POLICY_VERSION = "security-overlay-v1"
DEFAULT_STALE_SEC = 24 * 3600

# Mirrors frozen discovery.security_gate.CRITICAL / evaluate() without importing
# Lane A into architecture/security (phase-4 lane isolation).
LANE_A_CRITICAL_KEYS = (
    "honeypot",
    "sell_tax_extreme",
    "blacklist_function",
    "mint_authority_active",
    "freeze_authority_active",
    "lp_not_locked_fresh_pool",
    "deployer_prior_rug",
)

# Align with paper_trading.security_multi.EXTREME_SELL_TAX = 0.20 as percent.
EXTREME_SELL_TAX_PCT = 20.0


class SecurityState(str, Enum):
    PASS = "PASS"
    REJECT = "REJECT"
    INCOMPLETE = "INCOMPLETE"
    STALE = "STALE"


@dataclass(frozen=True)
class SecurityOverlay:
    state: SecurityState
    reason: str
    lane_a_verdict: str | None
    veto_reasons: tuple[str, ...] = ()
    unknown_critical: tuple[str, ...] = ()
    coverage: float = 0.0
    policy_version: str = POLICY_VERSION
    computed_ts: float = 0.0
    extras: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "reason": self.reason,
            "lane_a_verdict": self.lane_a_verdict,
            "veto_reasons": list(self.veto_reasons),
            "unknown_critical": list(self.unknown_critical),
            "coverage": self.coverage,
            "policy_version": self.policy_version,
            "computed_ts": self.computed_ts,
            "extras": list(self.extras),
        }


def security_allows_positive_eligibility(overlay: SecurityOverlay | None) -> bool:
    """NO SECURITY PASS ⇒ no positive rec / alert / paper candidate."""
    if overlay is None:
        return False
    return overlay.state == SecurityState.PASS


def security_allows_alert(overlay: SecurityOverlay | None) -> bool:
    return security_allows_positive_eligibility(overlay)


def security_allows_paper_candidate(overlay: SecurityOverlay | None) -> bool:
    return security_allows_positive_eligibility(overlay)


def _tri(value: bool | None) -> str:
    if value is True:
        return "TRUE"
    if value is False:
        return "FALSE"
    return "UNKNOWN"


def _sell_tax_extreme(pct: float | None) -> str:
    """SecuritySignals.sell_tax_pct is percent (1.0 == 1%). Extreme >= 20%."""
    if pct is None:
        return "UNKNOWN"
    return "TRUE" if pct >= EXTREME_SELL_TAX_PCT else "FALSE"


def _lp_fresh_pool_check(
    lp_locked_pct: float | None, pair_created_ts: float | None, now: float, fresh_days: int = 7,
) -> str:
    """Mirror of frozen discovery.security_gate.lp_fresh_pool_check."""
    if lp_locked_pct is None or pair_created_ts is None:
        return "UNKNOWN"
    young = (now - pair_created_ts) < fresh_days * 86400
    locked = lp_locked_pct > 0
    return "TRUE" if (young and not locked) else "FALSE"


def _lane_a_evaluate(checks: list[dict]) -> dict:
    """Mirror of frozen discovery.security_gate.evaluate for CRITICAL keys."""
    present = {c["check_key"]: c for c in checks}
    veto = [k for k in LANE_A_CRITICAL_KEYS if present.get(k, {}).get("value") == "TRUE"]
    unknown_crit = [
        k for k in LANE_A_CRITICAL_KEYS
        if present.get(k, {}).get("value") in (None, "UNKNOWN") or k not in present
    ]
    unknown_crit = sorted(set(unknown_crit))
    total = len(LANE_A_CRITICAL_KEYS)
    resolved = total - len(unknown_crit)
    coverage = resolved / total if total else 0.0
    if veto:
        verdict, cap = "SECURITY_VETO", "AVOID"
    elif unknown_crit:
        verdict, cap = "PASS_WITH_UNKNOWN", "WATCH"
    else:
        verdict, cap = "PASS", "WATCH-if-early"
    return {
        "verdict": verdict,
        "veto_reasons": veto,
        "unknown_critical": unknown_crit,
        "coverage": round(coverage, 4),
        "recommendation_cap": cap,
    }


def _lp_check(sec: SecuritySignals, pair_created_ts: float | None, now: float) -> str:
    if pair_created_ts is not None:
        return _lp_fresh_pool_check(sec.liquidity_locked_pct, pair_created_ts, now)
    # Age unknown: locked liquidity is not the fresh-unlocked trap; unlocked
    # without age stays UNKNOWN (never inferred safe).
    if sec.liquidity_locked_pct is None:
        return "UNKNOWN"
    if sec.liquidity_locked_pct > 0:
        return "FALSE"
    return "UNKNOWN"


def checks_from_signals(
    sec: SecuritySignals,
    *,
    pair_created_ts: float | None = None,
    now: float,
) -> list[dict]:
    """Project Lane B SecuritySignals onto frozen Lane A check keys."""
    deployer = sec.deployer_past_rug_count
    if deployer is None:
        rug = "UNKNOWN"
    else:
        rug = "TRUE" if deployer > 0 else "FALSE"
    rows = [
        ("honeypot", _tri(sec.is_honeypot)),
        ("sell_tax_extreme", _sell_tax_extreme(sec.sell_tax_pct)),
        ("blacklist_function", _tri(getattr(sec, "is_blacklisted", None))),
        ("mint_authority_active", _tri(sec.has_mint_authority)),
        ("freeze_authority_active", _tri(sec.has_freeze_authority)),
        ("lp_not_locked_fresh_pool", _lp_check(sec, pair_created_ts, now)),
        ("deployer_prior_rug", rug),
    ]
    return [
        {"check_key": key, "value": value, "severity": "CRITICAL", "provider": "signals"}
        for key, value in rows
    ]


def _map_lane_a(verdict: str) -> SecurityState:
    if verdict == "SECURITY_VETO":
        return SecurityState.REJECT
    if verdict == "PASS_WITH_UNKNOWN":
        return SecurityState.INCOMPLETE
    if verdict == "PASS":
        return SecurityState.PASS
    return SecurityState.INCOMPLETE


def compose_security_overlay(
    lane_a: dict,
    *,
    now: float,
    retrieved_ts: float | None = None,
    stale_after_sec: float = DEFAULT_STALE_SEC,
    extra_rejects: tuple[str, ...] = (),
    extra_unknowns: tuple[str, ...] = (),
) -> SecurityOverlay:
    """Map a frozen Lane A evaluate() dict onto Lane B states."""
    mapped = _map_lane_a(str(lane_a.get("verdict") or ""))
    extras: list[str] = []
    if extra_rejects:
        mapped = SecurityState.REJECT
        extras.extend(extra_rejects)
    elif mapped == SecurityState.PASS and extra_unknowns:
        mapped = SecurityState.INCOMPLETE
        extras.extend(extra_unknowns)
    elif extra_unknowns:
        extras.extend(extra_unknowns)

    stale = False
    if retrieved_ts is not None and (now - retrieved_ts) > stale_after_sec:
        stale = True
    if stale and mapped != SecurityState.REJECT:
        mapped = SecurityState.STALE
        extras.append("security_evidence_stale")

    reason = {
        SecurityState.REJECT: "critical_security_rejection",
        SecurityState.INCOMPLETE: "unknown_critical_security",
        SecurityState.STALE: "stale_security_evidence",
        SecurityState.PASS: "criticals_resolved_false",
    }[mapped]
    return SecurityOverlay(
        state=mapped,
        reason=reason,
        lane_a_verdict=lane_a.get("verdict"),
        veto_reasons=tuple(lane_a.get("veto_reasons") or ()) + tuple(extra_rejects),
        unknown_critical=tuple(lane_a.get("unknown_critical") or ()) + tuple(extra_unknowns),
        coverage=float(lane_a.get("coverage") or 0.0),
        computed_ts=now,
        extras=tuple(extras),
    )


def _extras_from_signals(sec: SecuritySignals, exitability: Any | None) -> tuple[tuple[str, ...], tuple[str, ...]]:
    rejects: list[str] = []
    unknowns: list[str] = []
    sellable = getattr(sec, "cannot_sell_all", None)
    if sellable is True:
        rejects.append("unsellable")
    elif sellable is None:
        unknowns.append("unsellable")
    if exitability is not None and getattr(exitability, "verdict", None) == "TRAPPED":
        rejects.append("trapped_liquidity")
    return tuple(rejects), tuple(unknowns)


def evaluate_security(
    sec: SecuritySignals | None,
    *,
    now: float,
    pair_created_ts: float | None = None,
    retrieved_ts: float | None = None,
    stale_after_sec: float = DEFAULT_STALE_SEC,
    exitability: Any | None = None,
    lane_a: dict | None = None,
) -> SecurityOverlay:
    if sec is None:
        return SecurityOverlay(
            state=SecurityState.INCOMPLETE,
            reason="missing_security_signals",
            lane_a_verdict=None,
            unknown_critical=("all",),
            computed_ts=now,
        )
    extra_rejects, extra_unknowns = _extras_from_signals(sec, exitability)
    if lane_a is None:
        checks = checks_from_signals(sec, pair_created_ts=pair_created_ts, now=now)
        lane_a = _lane_a_evaluate(checks)
    return compose_security_overlay(
        lane_a,
        now=now,
        retrieved_ts=retrieved_ts,
        stale_after_sec=stale_after_sec,
        extra_rejects=extra_rejects,
        extra_unknowns=extra_unknowns,
    )


def evaluate_security_from_candidate(
    candidate: NormalizedTokenCandidate,
    *,
    now: float,
    stale_after_sec: float = DEFAULT_STALE_SEC,
    exitability: Any | None = None,
    lane_a: dict | None = None,
) -> SecurityOverlay:
    return evaluate_security(
        candidate.security,
        now=now,
        pair_created_ts=candidate.pair_created_ts,
        retrieved_ts=candidate.retrieved_ts,
        stale_after_sec=stale_after_sec,
        exitability=exitability,
        lane_a=lane_a,
    )
