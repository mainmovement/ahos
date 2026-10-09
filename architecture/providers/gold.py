#!/usr/bin/env python3
"""Gold (XAU) price providers and the two-source witness for the gold market.

M13's gold-first paper track. The owner's two-source law
(``حافظه_ادامه/2026-10-09_04-46_قانون_شاهد_دو_منبعی_همه_بازارها.md``) is binding on
every market, and its gold clause (line 15) is specific: *"Gold: two
independent spot or futures price feeds."* The law's general clauses fill in
the rest: one source only, empty, stale or unreachable is UNKNOWN and never
PASS (line 7); disagreement past a coded tolerance is CONFLICT and never PASS
(line 8); independence means *different providers with different upstream data,
not two mirrors of one feed* (line 9); tolerances are defined in code and
tested, never left to a model's judgement at decision time (line 11).

Two providers are wired, chosen for genuine independence -- different
companies, different upstream tapes -- not two endpoints of one feed:

* :class:`GoldApiSpotAdapter` -- ``api.gold-api.com/price/XAU``. Aggregated
  spot, keyless, answers ``price``/``symbol``/``currency``/``updatedAt``.
* :class:`YahooGoldFuturesAdapter` -- ``query1.finance.yahoo.com`` ``GC=F``.
  The COMEX gold *futures* tape (instrumentType ``FUTURE``, exchange ``CMX``),
  keyless, answers ``regularMarketPrice``/``regularMarketTime``. The gold
  clause says "spot **or futures**", so a futures tape satisfies it.

The spot-vs-futures basis is why :data:`GOLD_TOLERANCE_PCT` is 2.0% rather than
the ~0.1% a same-venue pair would justify: a futures contract prices expected
future delivery and normally sits a fraction of a percent from spot, but the
two tapes also tick at different instants, so the tolerance must absorb both
the basis and the sampling skew or the witness would report CONFLICT on data
that actually agrees. Measured 2026-10-09: spot 4196.90 vs futures 4220.30,
0.55% apart. The tolerance is a named constant, tested at both sides, and is
not consulted as a judgement at decision time.

A PAXG-style token price is deliberately NOT used as a source. It is a proxy
for spot, not spot itself (Astra reverse-engineering memo, 2026-10-09: "Never
present proxy as spot gold"), and the gold clause requires spot or futures.

The class contract is deliberately NOT :class:`BaseMarketProvider`: that ABC is
token-shaped (``fetch_candidate_tokens`` / ``fetch_token_metrics`` over a chain
and an address) and gold has neither. Gold needs its own one-method contract,
so the Liskov-substitutability of the token hierarchy is not abused by
fabricating a chain/address for a metal.

Provenance follows ``architecture/providers/contracts.py``: every quote carries
its provider id, the observation timestamp the provider itself declared, and a
SHA-256 of the raw response body, so a downstream ledger entry can be audited
back to the bytes that produced it.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

# ------------------------------------------------------------------ market --

GOLD_MARKET = "gold"                     # XAU/USD, US dollars per troy ounce
GOLD_UNIT = "USD/oz t"                   # COMEX and XAU/USD both quote per troy oz

#: Disagreement tolerance for the gold pair. See the module docstring for why
#: this is percent-scale and not basis-points-scale.
GOLD_TOLERANCE_PCT = 2.0

#: A quote whose provider-declared timestamp is older than this is STALE and
#: contributes nothing. One uniform window for both feeds -- the spot tape and
#: the futures tape have genuinely different tick cadences (the COMEX
#: front-month print is the last actual trade and can sit unchanged for hours
#: between sessions; measured 2026-10-09 the Yahoo regularMarketTime was 3493s
#: old at every interval from 1m to 1d), but giving futures a wider window
#: would be tuning the freshness gate to make the trade happen. When the
#: futures tape is between sessions the witness correctly reports UNRESOLVED
#: and the paper track records NO_DATA rather than trading on spot alone.
GOLD_MAX_AGE_SEC = 3600

#: The two-source law's minimum. Below this the witness is UNRESOLVED -- never
#: a downgrade of one source into evidence.
MIN_INDEPENDENT_SOURCES = 2

# Witness states mirror architecture/identity/resolution.py's vocabulary so the
# gold market reports the same truth states the token market already does.
VERIFIED = "VERIFIED"
CONFLICT = "CONFLICT"
STALE = "STALE"
UNRESOLVED = "UNRESOLVED"

INSTRUMENT_SPOT = "spot"
INSTRUMENT_FUTURES = "futures"


@dataclass(frozen=True)
class GoldQuote:
    """One provider's quote, with its own provenance."""

    provider_id: str
    price_usd: float
    instrument: str           # spot | futures -- the gold clause admits both
    unit: str
    observed_at: float        # epoch seconds, as declared by the provider
    raw_sha256: str           # SHA-256 of the raw response body
    url: str


@dataclass(frozen=True)
class GoldPriceWitness:
    """The two-source verdict for the gold price.

    ``price_usd`` is None unless the state is VERIFIED. A CONFLICT still
    reports the quotes and the measured spread, because a conflict is
    evidence to show an operator, not a number to average into a decision.
    """

    state: str
    reason: str
    price_usd: float | None
    quotes: tuple[GoldQuote, ...] = field(default_factory=tuple)
    spread_pct: float | None = None
    tolerance_pct: float = GOLD_TOLERANCE_PCT
    checked_at: float = 0.0


class GoldPriceError(Exception):
    """A provider answered but the answer cannot be used as a price."""


class GoldPriceAdapter(ABC):
    """The gold price contract: one quote per call.

    ``requires_credentials`` defaults to True -- the opposite of what gold
    actually needs -- for exactly the reason ``BaseHttpProviderAdapter``'s
    defaults True: a provider that forgets to declare itself keyless must
    never be silently counted as a free unattended source. Both concrete
    adapters here declare False explicitly.
    """

    provider_id: str = ""
    requires_credentials: bool = True
    instrument: str = INSTRUMENT_SPOT
    url: str = ""

    def __init__(self, transport: Callable = urllib.request.urlopen,
                 timeout_sec: float = 10.0, rate_limit_rps: float = 1.0):
        self._transport = transport
        self._timeout_sec = timeout_sec
        self._rate_limit_rps = rate_limit_rps
        self._last_call_ts = 0.0

    def _rate_limit(self) -> None:
        interval = 1.0 / max(self._rate_limit_rps, 0.1)
        now = time.time()
        elapsed = now - self._last_call_ts
        if elapsed < interval:
            time.sleep(interval - elapsed)
        self._last_call_ts = time.time()

    def _get(self, url: str, headers: dict[str, str]) -> tuple[dict, bytes]:
        self._rate_limit()
        req = urllib.request.Request(url, headers=headers)
        with self._transport(req, timeout=self._timeout_sec) as resp:
            raw = resp.read()
        try:
            return json.loads(raw), raw
        except (ValueError, TypeError) as exc:
            raise GoldPriceError(f"{self.provider_id}: body is not JSON") from exc

    @abstractmethod
    def fetch_price(self, *, now: float) -> GoldQuote:
        """Fetch one quote. Raises GoldPriceError on an unusable answer."""


class GoldApiSpotAdapter(GoldPriceAdapter):
    """api.gold-api.com XAU spot. Keyless, aggregated spot tape."""

    provider_id = "goldapi_spot"
    requires_credentials = False
    instrument = INSTRUMENT_SPOT
    url = "https://api.gold-api.com/price/XAU"

    def fetch_price(self, *, now: float) -> GoldQuote:
        body, raw = self._get(
            self.url, {"User-Agent": "ahos-provider/1.0", "Accept": "application/json"})
        try:
            price = float(body["price"])
        except (KeyError, TypeError, ValueError) as exc:
            raise GoldPriceError(
                f"{self.provider_id}: no usable 'price' in {body!r}") from exc
        if not (price > 0.0):
            raise GoldPriceError(f"{self.provider_id}: non-positive price {price!r}")
        observed = _parse_timestamp(body.get("updatedAt"))
        if observed is None:
            # A price with no declared observation time cannot be freshness
            # checked, and the law's stale clause then applies to it directly.
            raise GoldPriceError(f"{self.provider_id}: no usable 'updatedAt' in {body!r}")
        symbol = str(body.get("symbol") or "XAU").upper()
        if symbol != "XAU":
            raise GoldPriceError(
                f"{self.provider_id}: symbol is {symbol!r}, not XAU -- wrong instrument")
        return GoldQuote(
            provider_id=self.provider_id,
            price_usd=price,
            instrument=self.instrument,
            unit=GOLD_UNIT,
            observed_at=observed,
            raw_sha256=hashlib.sha256(raw).hexdigest(),
            url=self.url,
        )


class YahooGoldFuturesAdapter(GoldPriceAdapter):
    """query1.finance.yahoo.com GC=F. Keyless COMEX gold *futures* tape.

    The gold clause admits futures explicitly, and a futures tape from a
    different vendor than the spot adapter is exactly the "different provider,
    different upstream data" the law's independence clause requires.
    """

    provider_id = "yahoo_gc_futures"
    requires_credentials = False
    instrument = INSTRUMENT_FUTURES
    url = ("https://query1.finance.yahoo.com/v8/finance/chart/GC=F"
           "?range=1d&interval=1d")

    def fetch_price(self, *, now: float) -> GoldQuote:
        body, raw = self._get(
            self.url, {"User-Agent": "ahos-provider/1.0", "Accept": "application/json"})
        try:
            result = body["chart"]["result"][0]
            meta = result["meta"]
            price = float(meta["regularMarketPrice"])
            observed = float(meta["regularMarketTime"])
        except (KeyError, TypeError, ValueError, IndexError) as exc:
            raise GoldPriceError(
                f"{self.provider_id}: no usable market price/time in {body!r}") from exc
        if not (price > 0.0):
            raise GoldPriceError(f"{self.provider_id}: non-positive price {price!r}")
        if str(meta.get("instrumentType") or "").upper() != "FUTURE":
            # Guards the clause's "spot or futures" wording: if the symbol ever
            # resolves to something else the witness must not claim a futures
            # reading it does not have.
            raise GoldPriceError(
                f"{self.provider_id}: instrumentType is "
                f"{meta.get('instrumentType')!r}, expected FUTURE")
        return GoldQuote(
            provider_id=self.provider_id,
            price_usd=price,
            instrument=self.instrument,
            unit=GOLD_UNIT,
            observed_at=observed,
            raw_sha256=hashlib.sha256(raw).hexdigest(),
            url=self.url,
        )


def _parse_timestamp(value: object) -> float | None:
    """ISO-8601 (gold-api) or epoch seconds, as the provider declared it."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    try:
        return float(text)
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(
            text.replace("Z", "+00:00").replace("z", "+00:00")
        ).timestamp()
    except ValueError:
        return None


def production_gold_adapters(
    transport: Callable = urllib.request.urlopen,
) -> tuple[GoldPriceAdapter, ...]:
    """The unattended gold pair, in independence order.

    Both adapters declare ``requires_credentials = False``; this function is
    the place that choice becomes structural, and it is what a caller uses when
    it wants the witness the law describes rather than a hand-picked list.
    """
    return (
        GoldApiSpotAdapter(transport=transport),
        YahooGoldFuturesAdapter(transport=transport),
    )


def resolve_gold_price(
    adapters: tuple[GoldPriceAdapter, ...] | list[GoldPriceAdapter],
    *,
    now: float,
    tolerance_pct: float = GOLD_TOLERANCE_PCT,
    max_age_sec: float = GOLD_MAX_AGE_SEC,
    min_sources: int = MIN_INDEPENDENT_SOURCES,
) -> GoldPriceWitness:
    """Run the two-source witness over the gold pair.

    Fail-closed by construction: an exception from an adapter is caught here and
    the provider counts as unreachable, which is one of the law's single-source
    conditions. ``price_usd`` is set only on VERIFIED.

    The independence clause is enforced by counting *distinct provider ids*, so
    the same adapter passed twice cannot satisfy the minimum.
    """
    # The independence clause is enforced by counting *distinct provider ids*, so
    # the same adapter passed twice cannot satisfy the minimum.
    if not adapters:
        return GoldPriceWitness(
            state=UNRESOLVED,
            reason="no_sources_configured",
            price_usd=None,
            quotes=tuple(),
            checked_at=now,
        )

    if not is_keyless_pair(adapters):
        # A paid source cannot serve an unattended witness; a provider that
        # declared a key requirement (or forgot to declare at all) is excluded
        # rather than counted. This mirrors build_production_resolver's refusal
        # to build over a keyed default set.
        keyed = [a.provider_id for a in adapters
                 if getattr(a, "requires_credentials", True) is not False]
        return GoldPriceWitness(
            state=UNRESOLVED,
            reason=("keyed_provider_present (" + ",".join(keyed)
                    + ") -- an unattended two-source witness must be keyless"),
            price_usd=None,
            quotes=tuple(),
            checked_at=now,
        )

    quotes: list[GoldQuote] = []
    failures: list[str] = []
    for adapter in adapters:
        try:
            quotes.append(adapter.fetch_price(now=now))
        except GoldPriceError as exc:
            failures.append(f"{adapter.provider_id}: {exc}")
        except Exception as exc:  # noqa: BLE001 - a down provider is evidence, not a crash
            failures.append(f"{adapter.provider_id}: unreachable ({type(exc).__name__})")

    # Drop stale quotes; a stale source contributes nothing (law line 7).
    fresh: list[GoldQuote] = []
    stale: list[str] = []
    for quote in quotes:
        if (now - quote.observed_at) > max_age_sec:
            stale.append(quote.provider_id)
        else:
            fresh.append(quote)

    distinct_ids = {q.provider_id for q in fresh}
    if len(distinct_ids) < min_sources:
        # Covers empty, unreachable, stale-everything and one-source-only.
        parts = []
        if fresh:
            parts.append(f"only {sorted(distinct_ids)} answered fresh")
        else:
            parts.append("no fresh source answered")
        if failures:
            parts.append("failures: " + "; ".join(failures))
        if stale:
            parts.append(f"stale: {sorted(stale)}")
        return GoldPriceWitness(
            state=UNRESOLVED,
            reason="insufficient_independent_sources (" + "; ".join(parts) + ")",
            price_usd=None,
            quotes=tuple(quotes),
            checked_at=now,
        )

    lo = min(fresh, key=lambda q: q.price_usd)
    hi = max(fresh, key=lambda q: q.price_usd)
    spread_pct = (hi.price_usd - lo.price_usd) / lo.price_usd * 100.0
    if spread_pct > tolerance_pct:
        return GoldPriceWitness(
            state=CONFLICT,
            reason=(f"source_disagreement:{hi.provider_id} "
                    f"({hi.price_usd:.2f}) vs {lo.provider_id} "
                    f"({lo.price_usd:.2f}) = {spread_pct:.3f}% > {tolerance_pct}%"),
            price_usd=None,
            quotes=tuple(quotes),
            spread_pct=spread_pct,
            tolerance_pct=tolerance_pct,
            checked_at=now,
        )

    # The witnesses agree: the price is the mean of the independent readings.
    # A mean is used only after agreement has been established, never to hide
    # a disagreement.
    price = sum(q.price_usd for q in fresh) / len(fresh)
    return GoldPriceWitness(
        state=VERIFIED,
        reason=(f"min_sources_met ({len(fresh)} independent: "
                f"{sorted(distinct_ids)}), spread {spread_pct:.3f}%"),
        price_usd=price,
        quotes=tuple(quotes),
        spread_pct=spread_pct,
        tolerance_pct=tolerance_pct,
        checked_at=now,
    )


def is_keyless_pair(adapters: tuple[GoldPriceAdapter, ...] | list[GoldPriceAdapter]) -> bool:
    """The gold analogue of the identity resolver's keyless gate.

    Every adapter must declare ``requires_credentials = False`` for the pair to
    count as an unattended witness. A provider that forgets to declare itself
    keyless is excluded rather than assumed free -- the same default-flipped
    logic ``BaseHttpProviderAdapter`` uses, so the gold market cannot quietly
    become dependent on a paid key.
    """
    return bool(adapters) and all(getattr(a, "requires_credentials", True) is False
                                  for a in adapters)
