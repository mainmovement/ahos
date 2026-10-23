"""M18.N & M80 Part A (Didehban) OSINT news desk.
One source is UNKNOWN. Disagreement is CONFLICT. >=2 independent domains required for CORROBORATED.
Includes Asi's M80 v2 credibility/recency/priority math and SimHash deduplication.
"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Any, Sequence
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class NewsView:
    state: str
    claim: str | None


@dataclass(frozen=True, slots=True)
class OsintClusterResult:
    state: str
    claim: str | None
    independent_domains: tuple[str, ...]
    credibility: float
    recency: float
    priority: float
    taint_labels: tuple[str, ...]
    injection_sanitized: bool


_INJECTION_RE = re.compile(
    r"(?:ignore\s+previous\s+instructions|disregard\s+everything|bypass\s+your\s+rules|act\s+as\s+root|execute\s+this\s+code|place\s+live\s+order)",
    re.IGNORECASE,
)


def corroborate(items: list[tuple[str, str]]) -> NewsView:
    if len({source for source, _claim in items}) < 2:
        return NewsView("UNKNOWN", None)
    claims = {claim for _source, claim in items}
    if len(claims) != 1:
        return NewsView("CONFLICT", None)
    return NewsView("CORROBORATED", next(iter(claims)))


def credibility_score(source_reliabilities: Sequence[float]) -> float:
    """Asi M80 v2 formula: C = 1 - prod_j (1 - r_j)."""
    if not source_reliabilities:
        return 0.0
    prod_complement = 1.0
    for r in source_reliabilities:
        clamped = max(0.0, min(1.0, float(r)))
        prod_complement *= 1.0 - clamped
    return round(1.0 - prod_complement, 6)


def recency_score(age_seconds: float, half_life_seconds: float = 14400.0) -> float:
    """Asi M80 v2 formula: R = exp(-lambda * dt), where lambda = ln(2) / half_life."""
    if half_life_seconds <= 0:
        return 0.0
    dt = max(0.0, float(age_seconds))
    lam = math.log(2.0) / float(half_life_seconds)
    return round(math.exp(-lam * dt), 6)


def priority_score(
    source_reliabilities: Sequence[float],
    age_seconds: float,
    impact: float,
    half_life_seconds: float = 14400.0,
) -> float:
    """Asi M80 v2 formula: Priority = C * R * I."""
    c = credibility_score(source_reliabilities)
    r = recency_score(age_seconds, half_life_seconds=half_life_seconds)
    i = max(0.0, min(1.0, float(impact)))
    return round(c * r * i, 6)


def simhash_64(text: str) -> int:
    """Deterministic 64-bit SimHash over normalized word shingles."""
    tokens = re.findall(r"[a-z0-9؀-ۿ]+", text.lower())
    if not tokens:
        return 0
    weights = [0] * 64
    for tok in tokens:
        digest = hashlib.md5(tok.encode("utf-8")).digest()
        h = int.from_bytes(digest[:8], "big")
        for bit in range(64):
            if (h >> bit) & 1:
                weights[bit] += 1
            else:
                weights[bit] -= 1
    out = 0
    for bit in range(64):
        if weights[bit] > 0:
            out |= 1 << bit
    return out


def hamming_distance_64(a: int, b: int) -> int:
    return ((a ^ b) & ((1 << 64) - 1)).bit_count()


def deduplicate_headlines(items: Sequence[dict[str, Any]], max_hamming: int = 6) -> list[dict[str, Any]]:
    """Deduplicate near-identical headlines using 64-bit SimHash."""
    kept: list[dict[str, Any]] = []
    hashes: list[int] = []
    for item in items:
        text = str(item.get("headline") or item.get("title") or item.get("summary") or "")
        sh = simhash_64(text)
        if any(hamming_distance_64(sh, existing) <= max_hamming for existing in hashes):
            continue
        hashes.append(sh)
        kept.append({**item, "simhash": f"{sh:016x}"})
    return kept


def _extract_domain(source: str) -> str:
    s = source.strip().lower()
    if "://" in s:
        return urlparse(s).hostname or s
    return s.split("/")[0]


def sanitize_untrusted_headline(text: str) -> tuple[str, bool]:
    """Treat all external OSINT text purely as data; strip/neutralize prompt-injection directives."""
    if _INJECTION_RE.search(text):
        cleaned = _INJECTION_RE.sub("[SANITIZED_UNTRUSTED_TEXT]", text)
        return cleaned, True
    return text, False


def evaluate_osint_cluster(
    reports: Sequence[dict[str, Any]],
    *,
    age_seconds: float = 600.0,
    impact: float = 0.8,
) -> OsintClusterResult:
    """Evaluate a cluster of OSINT reports under the strict Two-Source Witness Law."""
    domains: list[str] = []
    claims: set[str] = set()
    reliabilities: list[float] = []
    sanitized_any = False

    for rep in reports:
        src = _extract_domain(str(rep.get("source") or rep.get("domain") or ""))
        raw_claim = str(rep.get("claim") or rep.get("direction") or "").strip()
        clean_claim, was_inj = sanitize_untrusted_headline(raw_claim)
        if was_inj:
            sanitized_any = True
        raw_title = str(rep.get("headline") or "")
        _, was_title_inj = sanitize_untrusted_headline(raw_title)
        if was_title_inj:
            sanitized_any = True
        if src:
            if src not in domains:
                domains.append(src)
                reliabilities.append(float(rep.get("reliability", 0.75)))
        if clean_claim:
            claims.add(clean_claim)

    c = credibility_score(reliabilities)
    r = recency_score(age_seconds)
    p = priority_score(reliabilities, age_seconds, impact)
    taint = ("UNTRUSTED_OSINT_DATA", "INJECTION_NEUTRALIZED") if sanitized_any else ("UNTRUSTED_OSINT_DATA",)

    if len(domains) < 2:
        return OsintClusterResult(
            state="UNKNOWN",
            claim=None,
            independent_domains=tuple(domains),
            credibility=c,
            recency=r,
            priority=p,
            taint_labels=taint,
            injection_sanitized=sanitized_any,
        )
    if len(claims) != 1:
        return OsintClusterResult(
            state="CONFLICT",
            claim=None,
            independent_domains=tuple(domains),
            credibility=c,
            recency=r,
            priority=p,
            taint_labels=taint,
            injection_sanitized=sanitized_any,
        )
    return OsintClusterResult(
        state="CORROBORATED",
        claim=next(iter(claims)),
        independent_domains=tuple(domains),
        credibility=c,
        recency=r,
        priority=p,
        taint_labels=taint,
        injection_sanitized=sanitized_any,
    )
