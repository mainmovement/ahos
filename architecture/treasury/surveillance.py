#!/usr/bin/env python3
"""M42 treasury surveillance — the two §7.0 checks that can stop the system.

Vision §7.0 (v1.6, review 2026-10-03 23:21, SUPERSEDES 7.1-7.4) names exactly
two treasury checks as halt-capable:

* *"هر بروکر ≤ ۴۰٪"* — no single broker carries more than 40% of the exposure
  placed. This is the concentration half of the layered-custody law (cold
  ≥ 60%, warm ≤ 25%, hot ≤ 15%): even a venue that is fully eligible must not
  become the system.
* *"پایش depeg USDT: > ۰٫۵٪ ⇒ halt"* — a USDT peg deviation beyond 0.5%
  halts. USDT is the settlement unit of the treasury, so its peg is a
  precondition for every paper number denominated in it.

Both checks are **fail-closed in the direction that matters**: a measurement
that cannot be made is reported as ``UNMEASURED`` and refuses to certify the
limit held, but it does not sound the HALT. Only a measured breach does that.
An unmeasured limit is not a satisfied limit, and it is not an emergency
either — it is an honest gap, and the nightly reconcile reports it as one
rather than presenting it as either green or red.

PAPER_ONLY. These checks never touch funds, keys or a broker API. The broker
list is an owner gate (vision §11.0.3: brokers, their whitelists and their key
capabilities are UNKNOWN to the system until the owner declares them), so the
concentration check reads a registry the owner fills in and says
``UNMEASURED`` while that registry is empty rather than assuming a safe
distribution.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

#: Vision §7.0: "هر بروکر ≤ ۴۰٪" — each broker ≤ 40% of the exposure placed.
MAX_BROKER_SHARE = 0.40

#: Vision §7.0: USDT depeg beyond 0.5% halts.
DEPEG_THRESHOLD_PCT = 0.5

#: The owner's two-source law (see ``architecture/providers/gold.py:5-12``)
#: applied to the peg: a single quote cannot certify it, and two quotes that
#: disagree certify nothing either. 1% is the *agreement* band, not the peg
#: band — two fiat-pegged stablecoin feeds this close are corroborating.
DEPEG_AGREEMENT_PCT = 1.0

WITHIN_LIMIT = "WITHIN_LIMIT"
BREACH = "BREACH"
UNMEASURED = "UNMEASURED"

ARMED = "ARMED"
DEPEG = "DEPEG"

#: The peg the treasury settles in. Anything else is not a depeg of *this*
#: stablecoin and is out of scope here.
PEG_USD = 1.0

COINGECKO_USDT_URL = "https://api.coingecko.com/api/v3/simple/price?ids=tether&vs_currencies=usd"
COINGECKO_PROVIDER_ID = "coingecko:simple/price"
DEFILLAMA_PROVIDER_ID = "defillama:coins/prices"
#: USDT on the chains the treasury could settle on; the first reachable one
#: is the quote. Ethereum first because it is the deepest USDT book.
USDT_CHAIN_ADDRESS: dict[str, str] = {
    "ethereum": "0xdac17f958d2ee523a2206206994597c13d831ec7",
    "tron": "trx:TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
    "bsc": "bsc:0x55d398326f99059ff775485246999027b3197955",
}


# ------------------------------------------------------- broker concentration --

@dataclass(frozen=True)
class ConcentrationVerdict:
    """Each broker ≤ 40% of the exposure placed.

    ``allowed`` answers "is the concentration limit certified to hold?" —
    ``False`` for a breach *and* for an unmeasured book, so a caller that
    gates on it stops rather than passing on a missing measurement.
    """

    state: str
    limit_share: float = MAX_BROKER_SHARE
    shares: dict[str, float] = field(default_factory=dict)
    total_exposure_usd: float | None = None
    worst_broker: str | None = None
    findings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def allowed(self) -> bool:
        return self.state == WITHIN_LIMIT


def concentration_check(
    exposures: dict[str, float] | Sequence["BrokerExposure"] | None,
    *,
    total_exposure_usd: float | None = None,
    limit_share: float = MAX_BROKER_SHARE,
) -> ConcentrationVerdict:
    """Each broker's share of the exposure placed, against the 40% limit.

    ``exposures`` is ``{broker_id: exposure_usd}``. ``total_exposure_usd`` is
    the denominator; when it is omitted the exposure placed is used, which is
    the right denominator when the treasury is fully placed and wrong when it
    is not — supply it explicitly when the base includes unplaced capital.
    """
    if exposures is None:
        return ConcentrationVerdict(
            UNMEASURED, limit_share=limit_share,
            findings=("no broker exposures were supplied; the concentration limit "
                      "was not evaluated (the broker registry is an owner gate, "
                      "vision §11.0.3)",))
    if isinstance(exposures, dict):
        exposures = [BrokerExposure(b, float(v)) for b, v in exposures.items()]
    exposures = list(exposures)

    if not exposures:
        return ConcentrationVerdict(
            UNMEASURED, limit_share=limit_share,
            findings=("no broker carries exposure; the concentration limit has "
                      "nothing to measure (the broker registry is an owner gate, "
                      "vision §11.0.3)",))

    total = (float(total_exposure_usd) if total_exposure_usd is not None
             else sum(e.exposure_usd for e in exposures))
    if not total > 0.0:
        # Mirrors architecture/markets/risk.py:241-254: a non-positive
        # denominator is an unevaluable limit, not zero exposure.
        return ConcentrationVerdict(
            UNMEASURED, limit_share=limit_share, total_exposure_usd=total,
            findings=(f"the exposure denominator is {total}; a non-positive base "
                      "makes every share unevaluable rather than small",))

    shares = {e.broker_id: e.exposure_usd / total * 100.0 for e in exposures}
    findings: list[str] = []
    breaches: list[str] = []
    for e in exposures:
        if e.eligible is False:
            # Reported, not conflated with the limit: venue eligibility is
            # AG-39's declaration and M41's key self-check, a different gate
            # from this law. A breach here must mean the 40% law was broken,
            # or a caller reading ``state == BREACH`` cannot tell which
            # control fired -- and the finding is recorded either way.
            findings.append(f"broker {e.broker_id} carries {e.exposure_usd:.2f} USD "
                            "of exposure and is not declared ELIGIBLE (venue "
                            "eligibility is AG-39's to declare, never assumed)")
    worst = max(shares, key=lambda b: shares[b])
    for broker, share in sorted(shares.items(), key=lambda kv: -kv[1]):
        if share > limit_share * 100.0:
            breaches.append(f"broker {broker} carries {share:.2f}% of exposure, "
                            f"above the limit of {limit_share * 100.0:.2f}%")
    findings.extend(breaches)
    state = BREACH if breaches else WITHIN_LIMIT
    return ConcentrationVerdict(state, limit_share=limit_share, shares=shares,
                                total_exposure_usd=total, worst_broker=worst,
                                findings=tuple(findings))


@dataclass(frozen=True)
class BrokerExposure:
    """Exposure placed at one broker. ``eligible`` is None when undeclared."""

    broker_id: str
    exposure_usd: float
    eligible: bool | None = None


# ------------------------------------------------------------- USDT depeg ----

@dataclass(frozen=True)
class StableQuote:
    """One USD quote for the pegged asset, with its provenance."""

    provider_id: str
    price_usd: float
    observed_at: float
    source_detail: str = ""


@dataclass(frozen=True)
class DepegVerdict:
    """The peg's state. Only a measured deviation beyond the threshold halts.

    ``allowed`` answers "is the peg certified intact?" — ``False`` for DEPEG
    *and* for UNMEASURED, so a caller that gates new risk on it stops on a
    missing quote rather than passing on it.
    """

    state: str
    deviation_pct: float | None = None
    mean_price_usd: float | None = None
    quotes: tuple[StableQuote, ...] = field(default_factory=tuple)
    findings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def allowed(self) -> bool:
        return self.state == ARMED


def depeg_check(
    quotes: Sequence[StableQuote] | None,
    *,
    threshold_pct: float = DEPEG_THRESHOLD_PCT,
    agreement_pct: float = DEPEG_AGREEMENT_PCT,
) -> DepegVerdict:
    """The two-source peg law, over the quotes supplied.

    One quote certifies nothing: a single feed can misprice, and a halt built
    on one feed halts the system on one provider's bad tick. Two quotes from
    *distinct* providers that agree within ``agreement_pct`` corroborate the
    level; their mean's deviation from $1 is the measurement. Fewer than two,
    or two that disagree, is ``UNMEASURED`` — the peg is not certified and not
    breached, and the reconcile reports the gap.
    """
    if not quotes:
        return DepegVerdict(UNMEASURED,
                            findings=("no quote for the peg asset; the peg is not "
                                      "certified (two independent sources are required, "
                                      "see architecture/providers/gold.py:5-12)",))
    seen: dict[str, StableQuote] = {}
    for q in quotes:
        if q.price_usd is None or q.price_usd <= 0.0:
            continue
        seen.setdefault(q.provider_id, q)
    if len(seen) < 2:
        return DepegVerdict(
            UNMEASURED, quotes=tuple(seen.values()),
            findings=(f"only {len(seen)} independent quote(s) for the peg asset "
                      f"({sorted(seen)}); the two-source law is not satisfied",))
    independent = sorted(seen.values(), key=lambda q: q.provider_id)
    lo = min(q.price_usd for q in independent)
    hi = max(q.price_usd for q in independent)
    spread_pct = (hi - lo) / hi * 100.0
    if spread_pct > agreement_pct:
        return DepegVerdict(
            UNMEASURED, quotes=tuple(independent),
            findings=(f"the independent quotes disagree by {spread_pct:.4f}% "
                      f"({[q.provider_id for q in independent]}), wider than the "
                      f"{agreement_pct:.2f}% agreement band; the level is not "
                      "measured and the peg is not certified",))
    mean = sum(q.price_usd for q in independent) / len(independent)
    deviation = abs(mean - PEG_USD) * 100.0
    if deviation > threshold_pct:
        return DepegVerdict(
            DEPEG, deviation_pct=deviation, mean_price_usd=mean,
            quotes=tuple(independent),
            findings=(f"USDT is at {mean:.6f} USD, {deviation:.4f}% from the peg, "
                      f"beyond the {threshold_pct:.2f}% halt threshold "
                      "(vision §7.0): HALT",))
    return DepegVerdict(ARMED, deviation_pct=deviation, mean_price_usd=mean,
                        quotes=tuple(independent))


# ------------------------------------------------------------- the live feeds --

Transport = Callable[[str, float], Any]


def _default_transport(url: str, timeout: float) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "ahos-m42-depeg"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def coingecko_usdt_quote(*, transport: Transport = _default_transport,
                         timeout: float = 10.0,
                         now: Callable[[], float] = time.time) -> StableQuote | None:
    """CoinGecko's keyless USD quote for tether.

    The endpoint needs no key; an optional demo key is not used here because a
    depeg monitor must not depend on a metered credential for a safety signal.
    Returns None on any failure — no quote is fabricated.
    """
    try:
        body = transport(COINGECKO_USDT_URL, timeout)
    except Exception:                                        # noqa: BLE001
        return None
    try:
        price = float(((body or {}).get("tether") or {}).get("usd"))
    except (TypeError, ValueError, AttributeError):
        return None
    if not price > 0.0:
        return None
    return StableQuote(COINGECKO_PROVIDER_ID, price, observed_at=now(),
                       source_detail="api.coingecko.com simple/price")


def defillama_usdt_quote(*, chain: str = "ethereum",
                         address: str | None = None,
                         transport: Transport = _default_transport,
                         timeout: float = 10.0) -> StableQuote | None:
    """DefiLlama's keyless per-token USD quote, reusing the existing adapter.

    ``architecture/providers/defillama.py`` already resolves chain+address to a
    USD price with a confidence field; this is that quote, dressed as a peg
    observation. Returns None on any failure.
    """
    from ..providers.defillama import DefiLlamaAdapter
    try:
        row = DefiLlamaAdapter().get_token_price(
            chain, address or USDT_CHAIN_ADDRESS.get(chain, ""))
    except Exception:                                        # noqa: BLE001
        return None
    if not isinstance(row, dict):
        return None
    try:
        price = float(row.get("price_usd"))
        observed = float(row.get("timestamp") or 0.0) or time.time()
    except (TypeError, ValueError):
        return None
    if not price > 0.0:
        return None
    return StableQuote(DEFILLAMA_PROVIDER_ID, price, observed_at=observed,
                       source_detail=f"coins.llama.fi {chain}")


def collect_usdt_quotes(*, transport: Transport = _default_transport,
                        timeout: float = 10.0,
                        feeds: Sequence[Callable[[], StableQuote | None]] | None = None,
                        ) -> list[StableQuote]:
    """Both keyless feeds, in a fixed order. A feed that fails contributes
    nothing; the two-source law in ``depeg_check`` then reports UNMEASURED."""
    if feeds is None:
        feeds = (lambda: coingecko_usdt_quote(transport=transport, timeout=timeout),
                 lambda: defillama_usdt_quote(transport=transport, timeout=timeout))
    out: list[StableQuote] = []
    for feed in feeds:
        try:
            q = feed()
        except Exception:                                    # noqa: BLE001
            q = None
        if q is not None:
            out.append(q)
    return out


def load_broker_registry(path: str | Path) -> dict[str, Any]:
    """The owner-gated broker registry (``config/broker_registry.yaml``).

    Empty by design: the vision makes brokers, their whitelists and their key
    capabilities an owner UNKNOWN (§11.0.3), so the registry ships with no
    brokers and the concentration check reports UNMEASURED until the owner
    declares them.
    """
    import yaml
    with Path(path).open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return data if isinstance(data, dict) else {}


def exposures_from_registry(registry: dict[str, Any]) -> list[BrokerExposure]:
    """Registry rows -> broker exposures. No exposure is invented: a broker
    row without a declared exposure is skipped, not assumed."""
    rows = registry.get("brokers") or []
    out: list[BrokerExposure] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        broker_id = row.get("broker_id") or row.get("id")
        exposure = row.get("exposure_usd")
        if broker_id is None or exposure is None:
            continue
        out.append(BrokerExposure(str(broker_id), float(exposure),
                                  eligible=row.get("eligible")))
    return out
