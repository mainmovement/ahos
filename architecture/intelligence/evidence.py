#!/usr/bin/env python3
"""AHOS canonical Evidence types (Phase 4).

LAW
---
Every intelligence calculation (features, risk, scoring, explanations) consumes
`Evidence` / `EvidenceBundle` objects. Raw provider payloads, database rows, and
`NormalizedTokenCandidate` metrics are forbidden past the materialization
boundary defined here.

`materialize_evidence` is the single admitted conversion from a normalized
candidate into Evidence. Downstream modules must not import the candidate type.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Sequence


class EvidenceContractError(TypeError):
    """Raised when a calculation is handed raw data instead of Evidence."""


@dataclass(frozen=True)
class TokenRef:
    """Identity metadata for the subject of an evidence bundle.

    This is not market data. It names the token so reports can be attributed.
    """
    chain: str
    address: str
    symbol: str
    name: str
    source_provider: str
    retrieved_ts: float
    raw_payload_sha256: str = ""


@dataclass(frozen=True)
class Evidence:
    """A single observed or explicitly-unknown fact with provenance.

    status:
      VERIFIED  — measured by a provider
      DERIVED   — computed from other evidence (still an Evidence object)
      UNKNOWN   — looked for, not found (value is None)
      STALE     — measured, but older than the evaluation freshness budget
    """
    key: str
    description: str
    value: Any
    provider: str
    timestamp: float
    freshness_seconds: float
    status: str
    source_field: str = ""
    sha256: str = ""

    def is_known(self) -> bool:
        return self.status != "UNKNOWN" and self.value is not None


# Keys that appear on the public OpportunityScoreReport.evidence_items list.
# Kept identical to the pre-Phase-4 scorer so existing explainability tests hold.
REPORT_EVIDENCE_KEYS: tuple[str, ...] = (
    "liquidity_usd",
    "volume_1h",
    "is_honeypot",
    "top10_concentration",
)

_MISSING_LABELS: dict[str, str] = {
    "liquidity_usd": "نقدینگی استخر (Liquidity USD)",
    "volume_1h": "حجم معاملات ۱ ساعته",
    "is_honeypot": "بررسی Honeypot و امنیت قرارداد",
    "top10_concentration": "درصد تمرکز ۱۰ هولدر برتر",
}


def require_evidence_bundle(obj: Any, consumer: str) -> EvidenceBundle:
    """Hard gate: intelligence calculations refuse anything that is not Evidence."""
    if not isinstance(obj, EvidenceBundle):
        raise EvidenceContractError(
            f"{consumer} consumes EvidenceBundle only; "
            f"raw data ({type(obj).__name__}) is forbidden"
        )
    for item in obj.items:
        if not isinstance(item, Evidence):
            raise EvidenceContractError(
                f"{consumer} received a non-Evidence item: {type(item).__name__}"
            )
    return obj


def numeric_value(evidence: Evidence | None) -> float | None:
    """Extract a numeric observation. Booleans are not numbers (UNKNOWN stays None)."""
    if evidence is None or evidence.value is None:
        return None
    if isinstance(evidence.value, bool):
        return None
    try:
        return float(evidence.value)
    except (TypeError, ValueError):
        return None


def bool_value(evidence: Evidence | None) -> bool | None:
    if evidence is None or evidence.value is None:
        return None
    if isinstance(evidence.value, bool):
        return evidence.value
    return None


def mapping_value(evidence: Evidence | None) -> dict:
    if evidence is None or not isinstance(evidence.value, dict):
        return {}
    return evidence.value


def text_value(evidence: Evidence | None) -> str | None:
    if evidence is None or evidence.value is None:
        return None
    return str(evidence.value)


def list_value(evidence: Evidence | None) -> list:
    if evidence is None or not isinstance(evidence.value, list):
        return []
    return list(evidence.value)


def make_derived_evidence(
    key: str,
    description: str,
    value: Any,
    *,
    provider: str,
    timestamp: float,
    source_field: str,
    status: str = "DERIVED",
) -> Evidence:
    """Build a provenance-bearing derived Evidence atom (never raw data)."""
    known = value is not None and status != "UNKNOWN"
    resolved = "UNKNOWN" if not known else status
    return Evidence(
        key=key,
        description=description,
        value=value,
        provider=provider,
        timestamp=timestamp,
        freshness_seconds=0.0,
        status=resolved,
        source_field=source_field,
        sha256=_digest(key, value, provider, timestamp),
    )


def _digest(key: str, value: Any, provider: str, timestamp: float) -> str:
    payload = f"{key}|{value!r}|{provider}|{timestamp}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


#: Pre-declared evidence freshness budget (W36 phase 10). A measured item
#: older than this is STALE — still a known fact (its value stays usable for
#: scoring, which never branches on status), but visibly old in explanations
#: and calibration. Fixed before observing data; never a runtime parameter.
EVIDENCE_FRESHNESS_BUDGET_SEC = 86400.0   # 24h


def _atom(
    *,
    key: str,
    description: str,
    value: Any,
    provider: str,
    timestamp: float,
    now: float,
    source_field: str,
    known_when: bool,
) -> Evidence:
    """Build a provider-measured evidence atom with an honest status.

    The declared-but-unenforced STALE contract is now realized: a known item
    whose measurement is older than EVIDENCE_FRESHNESS_BUDGET_SEC carries
    status STALE (value intact — is_known() stays True, and no scoring math
    branches on status, so this is observability completion, not a weighting
    change). Unknown stays UNKNOWN.
    """
    status = "VERIFIED" if known_when else "UNKNOWN"
    if status == "VERIFIED":
        freshness = max(0.0, now - timestamp)
        if freshness > EVIDENCE_FRESHNESS_BUDGET_SEC:
            status = "STALE"
    return Evidence(
        key=key,
        description=description,
        value=value,
        provider=provider,
        timestamp=timestamp,
        freshness_seconds=max(0.0, now - timestamp),
        status=status,
        source_field=source_field,
        sha256=_digest(key, value, provider, timestamp),
    )


@dataclass(frozen=True)
class EvidenceBundle:
    """Closed set of Evidence for one token at one evaluation instant."""
    identity: TokenRef
    items: tuple[Evidence, ...]
    evaluated_at: float
    extra: tuple[Evidence, ...] = field(default_factory=tuple)

    def all_items(self) -> tuple[Evidence, ...]:
        return self.items + self.extra

    def get(self, key: str) -> Evidence | None:
        for item in self.all_items():
            if item.key == key:
                return item
        return None

    def known(self, key: str) -> Evidence | None:
        item = self.get(key)
        return item if item and item.is_known() else None

    def keys(self) -> set[str]:
        return {item.key for item in self.all_items()}

    def extended(self, extra: Sequence[Evidence]) -> EvidenceBundle:
        cleaned = tuple(e for e in extra if isinstance(e, Evidence))
        if not cleaned:
            return self
        return EvidenceBundle(
            identity=self.identity,
            items=self.items,
            evaluated_at=self.evaluated_at,
            extra=self.extra + cleaned,
        )

    def report_evidence(self) -> list[Evidence]:
        """The four canonical items historically exposed on the score report."""
        out: list[Evidence] = []
        for key in REPORT_EVIDENCE_KEYS:
            item = self.get(key)
            if item is None or item.value is None:
                continue
            if key in ("liquidity_usd", "volume_1h"):
                number = numeric_value(item)
                if number is None or number <= 0:
                    continue
            out.append(item)
        return out

    def missing_unknowns(self) -> list[str]:
        """Persian labels for the four canonical unknowns (legacy contract)."""
        labels: list[str] = []
        liq = self.get("liquidity_usd")
        liq_n = numeric_value(liq)
        if liq is None or liq.value is None or liq_n is None or liq_n <= 0:
            labels.append(_MISSING_LABELS["liquidity_usd"])
        vol = self.get("volume_1h")
        vol_n = numeric_value(vol)
        if vol is None or vol.value is None or vol_n is None or vol_n <= 0:
            labels.append(_MISSING_LABELS["volume_1h"])
        if self.get("is_honeypot") is None or self.get("is_honeypot").value is None:  # type: ignore[union-attr]
            labels.append(_MISSING_LABELS["is_honeypot"])
        if self.get("top10_concentration") is None or self.get("top10_concentration").value is None:  # type: ignore[union-attr]
            labels.append(_MISSING_LABELS["top10_concentration"])
        return labels

    def provenance_sha256(self) -> str:
        joined = "|".join(
            f"{e.key}:{e.sha256}" for e in sorted(self.all_items(), key=lambda x: x.key)
        )
        return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def materialize_evidence(candidate: Any, now: float | None = None) -> EvidenceBundle:
    """THE ONLY admitted conversion from a normalized candidate into Evidence.

    `candidate` is duck-typed as NormalizedTokenCandidate so this module remains
    the sole place that may read raw metric/security attributes.
    """
    ts = time.time() if now is None else now
    retrieved = float(getattr(candidate, "retrieved_ts", ts) or ts)
    provider = str(getattr(candidate, "source_provider", "unknown") or "unknown")
    metrics = getattr(candidate, "metrics", None)
    security = getattr(candidate, "security", None)
    social = getattr(candidate, "social_presence", None) or {}

    def mget(name: str) -> Any:
        return getattr(metrics, name, None) if metrics is not None else None

    def sget(name: str) -> Any:
        return getattr(security, name, None) if security is not None else None

    liq = mget("liquidity_usd")
    vol = mget("volume_1h")
    honeypot = sget("is_honeypot")
    concentration = sget("top10_holder_concentration_pct")
    proxy_flag = sget("is_proxy")
    if proxy_flag is None and security is not None:
        proxy_flag = getattr(security, "is_upgradeable", None)
    top1_share = getattr(security, "top1_holder_concentration_pct", None) if security is not None else None
    holder_count = getattr(candidate, "holder_count", None)
    prev_top10 = getattr(candidate, "previous_top10_share_pct", None)
    whale_flow = getattr(candidate, "whale_net_flow_1h", None)
    wallet_events = getattr(candidate, "wallet_events", None) or []

    atoms: list[Evidence] = [
        _atom(
            key="liquidity_usd",
            description=f"Liquidity depth ${liq:,.2f}" if isinstance(liq, (int, float)) else "Liquidity depth UNKNOWN",
            value=liq,
            provider=provider,
            timestamp=retrieved,
            now=ts,
            source_field="metrics.liquidity_usd",
            known_when=liq is not None,
        ),
        _atom(
            key="volume_1h",
            description=f"1h Volume ${vol:,.2f}" if isinstance(vol, (int, float)) else "1h Volume UNKNOWN",
            value=vol,
            provider=provider,
            timestamp=retrieved,
            now=ts,
            source_field="metrics.volume_1h",
            known_when=vol is not None,
        ),
        _atom(
            key="volume_5m",
            description="5m volume",
            value=mget("volume_5m"),
            provider=provider,
            timestamp=retrieved,
            now=ts,
            source_field="metrics.volume_5m",
            known_when=mget("volume_5m") is not None,
        ),
        _atom(
            key="volume_velocity",
            description="Volume velocity vs baseline",
            value=mget("volume_velocity"),
            provider=provider,
            timestamp=retrieved,
            now=ts,
            source_field="metrics.volume_velocity",
            known_when=mget("volume_velocity") is not None,
        ),
        _atom(
            key="price_usd",
            description="Spot price USD",
            value=mget("price_usd"),
            provider=provider,
            timestamp=retrieved,
            now=ts,
            source_field="metrics.price_usd",
            known_when=mget("price_usd") is not None,
        ),
        _atom(
            key="txns_1h_buys",
            description="1h buy transactions",
            value=mget("txns_1h_buys"),
            provider=provider,
            timestamp=retrieved,
            now=ts,
            source_field="metrics.txns_1h_buys",
            known_when=mget("txns_1h_buys") is not None,
        ),
        _atom(
            key="txns_1h_sells",
            description="1h sell transactions",
            value=mget("txns_1h_sells"),
            provider=provider,
            timestamp=retrieved,
            now=ts,
            source_field="metrics.txns_1h_sells",
            known_when=mget("txns_1h_sells") is not None,
        ),
        _atom(
            key="txns_5m_buys",
            description="5m buy transactions",
            value=mget("txns_5m_buys"),
            provider=provider,
            timestamp=retrieved,
            now=ts,
            source_field="metrics.txns_5m_buys",
            known_when=mget("txns_5m_buys") is not None,
        ),
        _atom(
            key="txns_5m_sells",
            description="5m sell transactions",
            value=mget("txns_5m_sells"),
            provider=provider,
            timestamp=retrieved,
            now=ts,
            source_field="metrics.txns_5m_sells",
            known_when=mget("txns_5m_sells") is not None,
        ),
        _atom(
            key="is_honeypot",
            description=f"Honeypot check: {honeypot}" if honeypot is not None else "Honeypot check UNKNOWN",
            value=honeypot,
            provider="security_gate",
            timestamp=retrieved,
            now=ts,
            source_field="security.is_honeypot",
            known_when=honeypot is not None,
        ),
        _atom(
            key="top10_concentration",
            description=(
                f"Top 10 concentration: {concentration:.1f}%"
                if isinstance(concentration, (int, float))
                else "Top 10 concentration UNKNOWN"
            ),
            value=concentration,
            provider="security_gate",
            timestamp=retrieved,
            now=ts,
            source_field="security.top10_holder_concentration_pct",
            known_when=concentration is not None,
        ),
        _atom(
            key="has_mint_authority",
            description="Mint authority active",
            value=sget("has_mint_authority"),
            provider="security_gate",
            timestamp=retrieved,
            now=ts,
            source_field="security.has_mint_authority",
            known_when=sget("has_mint_authority") is not None,
        ),
        _atom(
            key="has_freeze_authority",
            description="Freeze authority active",
            value=sget("has_freeze_authority"),
            provider="security_gate",
            timestamp=retrieved,
            now=ts,
            source_field="security.has_freeze_authority",
            known_when=sget("has_freeze_authority") is not None,
        ),
        _atom(
            key="is_contract_verified",
            description="Contract source verified",
            value=sget("is_contract_verified"),
            provider="security_gate",
            timestamp=retrieved,
            now=ts,
            source_field="security.is_contract_verified",
            known_when=sget("is_contract_verified") is not None,
        ),
        _atom(
            key="is_ownership_renounced",
            description="Ownership renounced",
            value=sget("is_ownership_renounced"),
            provider="security_gate",
            timestamp=retrieved,
            now=ts,
            source_field="security.is_ownership_renounced",
            known_when=sget("is_ownership_renounced") is not None,
        ),
        _atom(
            key="buy_tax_pct",
            description="Buy tax percent",
            value=sget("buy_tax_pct"),
            provider="security_gate",
            timestamp=retrieved,
            now=ts,
            source_field="security.buy_tax_pct",
            known_when=sget("buy_tax_pct") is not None,
        ),
        _atom(
            key="sell_tax_pct",
            description="Sell tax percent",
            value=sget("sell_tax_pct"),
            provider="security_gate",
            timestamp=retrieved,
            now=ts,
            source_field="security.sell_tax_pct",
            known_when=sget("sell_tax_pct") is not None,
        ),
        _atom(
            key="deployer_past_rug_count",
            description="Deployer prior rug count",
            value=sget("deployer_past_rug_count"),
            provider="security_gate",
            timestamp=retrieved,
            now=ts,
            source_field="security.deployer_past_rug_count",
            known_when=sget("deployer_past_rug_count") is not None,
        ),
        _atom(
            key="social_presence",
            description="Social presence map",
            value=dict(social) if social else {},
            provider=provider,
            timestamp=retrieved,
            now=ts,
            source_field="social_presence",
            known_when=bool(social),
        ),
        _atom(
            key="source_provider",
            description=f"Source provider {provider}",
            value=provider,
            provider=provider,
            timestamp=retrieved,
            now=ts,
            source_field="source_provider",
            known_when=bool(provider and provider != "unknown"),
        ),
        _atom(
            key="pair_created_ts",
            description="Pair created timestamp",
            value=getattr(candidate, "pair_created_ts", None),
            provider=provider,
            timestamp=retrieved,
            now=ts,
            source_field="pair_created_ts",
            known_when=getattr(candidate, "pair_created_ts", None) is not None,
        ),
    ]

    # Optional Phase 5 atoms: emit only when observed so extra Evidence can attach later.
    optional = [
        ("liquidity_locked_pct", sget("liquidity_locked_pct"), "LP lock percent",
         "security_gate", "security.liquidity_locked_pct"),
        ("liquidity_burned_pct", sget("liquidity_burned_pct"), "LP burned percent",
         "security_gate", "security.liquidity_burned_pct"),
        ("deployer_address", sget("deployer_address"), "Deployer address",
         "security_gate", "security.deployer_address"),
        ("is_proxy", proxy_flag, "Proxy / upgradeable contract",
         "security_gate", "security.is_proxy"),
        ("price_change_1h", mget("price_change_1h"), "1h price change",
         provider, "metrics.price_change_1h"),
        ("volume_24h", mget("volume_24h"), "24h volume",
         provider, "metrics.volume_24h"),
        ("top1_concentration", top1_share, "Largest-wallet share",
         "security_gate", "security.top1_holder_concentration_pct"),
        ("holder_count", holder_count, "Holder count",
         provider, "holder_count"),
        ("previous_top10_concentration", prev_top10, "Prior top-10 concentration snapshot",
         provider, "previous_top10_share_pct"),
        ("whale_net_flow_1h", whale_flow, "Whale net flow 1h USD",
         provider, "whale_net_flow_1h"),
        ("wallet_events", wallet_events if wallet_events else None, "Observed wallet events",
         provider, "wallet_events"),
    ]
    for key, value, desc, prov, field in optional:
        if value is None:
            continue
        atoms.append(_atom(
            key=key, description=desc, value=value, provider=prov,
            timestamp=retrieved, now=ts, source_field=field, known_when=True,
        ))

    identity = TokenRef(
        chain=str(getattr(candidate, "chain", "") or ""),
        address=str(getattr(candidate, "address", "") or ""),
        symbol=str(getattr(candidate, "symbol", "") or ""),
        name=str(getattr(candidate, "name", "") or ""),
        source_provider=provider,
        retrieved_ts=retrieved,
        raw_payload_sha256=str(getattr(candidate, "raw_payload_sha256", "") or ""),
    )
    return EvidenceBundle(identity=identity, items=tuple(atoms), evaluated_at=ts)


def merge_evidence(*groups: Iterable[Evidence]) -> tuple[Evidence, ...]:
    out: list[Evidence] = []
    for group in groups:
        for item in group:
            if isinstance(item, Evidence):
                out.append(item)
    return tuple(out)
