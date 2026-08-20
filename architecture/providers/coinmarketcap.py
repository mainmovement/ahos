#!/usr/bin/env python3
"""CoinMarketCap provider adapter (Month 2 — M-GAP-011).

CMC's free tier requires an API key, so this adapter is **inert until
configured**, exactly like the DEXTools adapter: without
``COINMARKETCAP_API_KEY`` it returns an explicit ``NO_KEY`` envelope and never
emits a single byte of network traffic. A configuration gap must never be
indistinguishable from an outage.

Honesty laws enforced here (mirrors the CoinGecko adapter):
  - CMC free tier exposes NO candidate-discovery listing endpoint. Discovery
    requests return an explicit ``UNSUPPORTED`` envelope — never a fabricated
    list.
  - DEX liquidity is NOT provided by CMC -> ``liquidity_usd`` stays UNKNOWN.
  - A contract address with no CMC listing returns ``OK`` with zero tokens
    ("not indexed" is a fact, not a failure — same semantics as CoinGecko's
    404).
  - Invalid/inactive keys (CMC ``status.error_code`` 1001/1002 or HTTP
    401/403) map to ``AUTH_REQUIRED``; rate ceilings map to ``RATE_LIMIT``;
    only real infrastructure failures map to ``DOWN``. The probe classifier
    keeps these distinct (M-GAP-016).

Chain -> platform matching uses CMC's own ``platform.slug``/``platform.name``
from the ``info?address=`` response, so no numeric platform ids are ever
guessed. The slug map below is fixture-verified (offline); live verification
is pending host egress (M-GAP-007) and is not assumed.
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from typing import Callable

from .adapters import BaseHttpProviderAdapter
from .contracts import (
    MarketMetrics,
    NormalizedTokenCandidate,
    ProviderResponse,
)

# CMC v2 endpoint credit costs (free tier: 10k credits/month, 30/min ceiling)
# are 1 credit each for `info` and `quotes/latest`. 0.4 rps = 24 calls/min
# keeps the adapter under the per-minute ceiling even when both calls of a
# collect are used, with margin for the monthly cap.
_RATE_LIMIT_RPS = 0.4
_TIMEOUT_SEC = 12.0


class CoinMarketCapAdapter(BaseHttpProviderAdapter):
    """Market-cap / metadata enrichment via CMC contract-address lookup.

    Keyed provider (free tier). Without a key every call returns ``NO_KEY``
    and nothing touches the network (DEXTools inert-until-configured pattern).
    """

    # Chain -> candidate CMC platform slugs/names. A listing is accepted for a
    # chain when its platform slug OR normalized name matches one of these.
    # Multiple candidates are allowed because CMC slugs drift; the matcher
    # normalizes both sides (lowercase, strip) and is deliberately permissive
    # only within the documented aliases.
    PLATFORM_MATCH = {
        "ethereum": {"slugs": {"ethereum"}, "names": {"ethereum"}},
        "eth": {"slugs": {"ethereum"}, "names": {"ethereum"}},
        "bsc": {"slugs": {"binance-smart-chain", "bnb-smart-chain", "bsc"},
                "names": {"binance smart chain", "bnb smart chain", "bnb", "bsc"}},
        "base": {"slugs": {"base"}, "names": {"base"}},
        "arbitrum": {"slugs": {"arbitrum-one", "arbitrum"},
                     "names": {"arbitrum", "arbitrum one"}},
        "polygon": {"slugs": {"polygon-pos", "polygon"},
                    "names": {"polygon", "polygon pos"}},
        "avalanche": {"slugs": {"avalanche-2", "avalanche-c-chain", "avalanche"},
                      "names": {"avalanche", "avalanche c-chain"}},
        "solana": {"slugs": {"solana"}, "names": {"solana"}},
    }

    def __init__(self, transport: Callable = urllib.request.urlopen,
                 api_key: str | None = None):
        super().__init__(
            provider_id="coinmarketcap",
            base_url="https://pro-api.coinmarketcap.com",
            capabilities=["market", "metadata", "market_cap"],
            rate_limit_rps=_RATE_LIMIT_RPS,
            timeout_sec=_TIMEOUT_SEC,
            transport=transport,
        )
        self._api_key = api_key if api_key is not None else os.environ.get(
            "COINMARKETCAP_API_KEY", "")

    @property
    def is_configured(self) -> bool:
        return bool(self._api_key)

    def health_check(self) -> bool:
        # Never emit traffic we know will be rejected with a 401/1002.
        return bool(self._api_key) and super().health_check()

    def _no_key(self, t0: float) -> ProviderResponse:
        return ProviderResponse(
            provider_id="coinmarketcap", status="NO_KEY", tokens=[],
            latency_ms=(time.time() - t0) * 1000.0,
            error_message=("COINMARKETCAP_API_KEY not set. CMC free tier requires "
                           "a key; AHOS runs without it and relies on keyless "
                           "providers (DexScreener/GeckoTerminal/CoinGecko)."),
        )

    def _headers(self) -> dict[str, str]:
        return {
            "X-CMC_PRO_API_KEY": self._api_key,
            "Accept": "application/json",
            "User-Agent": "ahos/1.0",
        }

    def _get(self, path: str) -> tuple[dict, bytes, int]:
        self._rate_limit()
        req = urllib.request.Request(f"{self._base_url}{path}", headers=self._headers())
        with self._transport(req, timeout=self._timeout_sec) as resp:
            raw = resp.read()
            status_code = resp.status
        return json.loads(raw), raw, status_code

    def fetch_candidate_tokens(self, chain: str, limit: int = 20) -> ProviderResponse:
        t0 = time.time()
        return ProviderResponse(
            provider_id="coinmarketcap",
            status="UNSUPPORTED",
            tokens=[],
            latency_ms=(time.time() - t0) * 1000.0,
            error_message=(
                "CMC free tier exposes no candidate-discovery listing endpoint; "
                "use dexscreener/geckoterminal for discovery. Never fabricated. "
                f"(key configured: {self.is_configured})"),
        )

    # -- CMC error-body helpers --------------------------------------------------

    @staticmethod
    def _cmc_error_code(raw: bytes) -> int | None:
        """Extract CMC's JSON ``status.error_code`` (1001 invalid key, 1002
        inactive key, ...) from an error body when parseable."""
        try:
            body = json.loads(raw or b"{}")
            return (body.get("status") or {}).get("error_code")
        except (ValueError, AttributeError):
            return None

    def _body_error_envelope(self, body: dict, t0: float,
                             http_status: int | None) -> ProviderResponse | None:
        """Map a CMC body-level ``status.error_code`` (which CMC can return
        inside an HTTP 200) onto a normalized envelope. None when the body
        reports success."""
        code = (body.get("status") or {}).get("error_code")
        if code in (None, 0):
            return None
        detail = f"CMC error_code {code}"
        if code in (1001, 1002):
            return ProviderResponse(
                provider_id="coinmarketcap", status="AUTH_REQUIRED", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0, http_status=http_status,
                error_message="CMC API key invalid or inactive (error_code 1001/1002)")
        if code in (1008, 1009, 1022, 1024, 1032):  # per-minute / daily / monthly ceilings
            return ProviderResponse(
                provider_id="coinmarketcap", status="RATE_LIMIT", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0, http_status=http_status,
                error_message=f"{detail} — CMC rate ceiling reached")
        return ProviderResponse(
            provider_id="coinmarketcap", status="ERROR", tokens=[],
            latency_ms=(time.time() - t0) * 1000.0, http_status=http_status,
            error_message=detail)

    # -- public fetch ------------------------------------------------------------

    def fetch_token_metrics(self, chain: str, address: str) -> ProviderResponse:
        t0 = time.time()
        ch = chain.lower()
        if not self._api_key:
            return self._no_key(t0)

        match = self.PLATFORM_MATCH.get(ch)
        if not match:
            return ProviderResponse(
                provider_id="coinmarketcap", status="ERROR", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=f"no CMC platform mapping for chain '{ch}' (fields stay UNKNOWN)",
            )

        try:
            # Step 1 — address -> CMC listings (one per chain the address lives on).
            info_data, info_raw, info_status = self._get(
                f"/v2/cryptocurrency/info?address={address}")
        except urllib.error.HTTPError as e:
            return self._http_error_envelope(e, t0)
        except Exception as e:  # network / parse failures fail closed
            return ProviderResponse(
                provider_id="coinmarketcap", status="DOWN", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=str(e)[:150],
            )

        body_err = self._body_error_envelope(info_data, t0, info_status)
        if body_err is not None:
            return body_err

        listings = info_data.get("data") or {}
        if not listings:
            return ProviderResponse(
                provider_id="coinmarketcap", status="OK", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0, http_status=info_status,
                raw_sha256=_sha(info_raw),
                error_message="address not indexed on CoinMarketCap",
            )

        listing = self._select_listing(listings, match)
        if listing is None:
            return ProviderResponse(
                provider_id="coinmarketcap", status="OK", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0, http_status=info_status,
                raw_sha256=_sha(info_raw),
                error_message=(f"address indexed on CoinMarketCap but not on "
                               f"chain '{ch}' (fields stay UNKNOWN)"),
            )

        listing_id = str(listing.get("id"))
        try:
            quote_data, quote_raw, quote_status = self._get(
                f"/v2/cryptocurrency/quotes/latest?id={listing_id}")
        except urllib.error.HTTPError as e:
            return self._http_error_envelope(e, t0)
        except Exception as e:
            return ProviderResponse(
                provider_id="coinmarketcap", status="DOWN", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0,
                error_message=str(e)[:150],
            )

        body_err = self._body_error_envelope(quote_data, t0, quote_status)
        if body_err is not None:
            return body_err

        token = self._build_token(ch, address, listing, quote_data, info_raw, quote_raw)
        return ProviderResponse(
            provider_id="coinmarketcap", status="OK", tokens=[token],
            latency_ms=(time.time() - t0) * 1000.0,
            http_status=quote_status,
            raw_sha256=_sha(info_raw + b"|" + quote_raw),
        )

    # -- parsing helpers -----------------------------------------------------------

    @staticmethod
    def _select_listing(listings: dict, match: dict) -> dict | None:
        """Pick the listing whose platform matches our chain. A listing without
        a platform block is skipped — chain cannot be verified, so it is never
        claimed."""
        want_slugs = match["slugs"]
        want_names = match["names"]
        for raw in listings.values():
            listing = raw if isinstance(raw, dict) else {}
            platform = listing.get("platform") or {}
            slug = str(platform.get("slug") or "").lower().strip()
            name = str(platform.get("name") or "").lower().strip()
            if slug in want_slugs or name in want_names:
                return listing
        return None

    @staticmethod
    def _build_token(chain: str, address: str, listing: dict,
                     quote_data: dict, info_raw: bytes, quote_raw: bytes) -> NormalizedTokenCandidate:
        quote = ((quote_data.get("data") or {}).get(str(listing.get("id"))) or {}).get("quote") or {}
        usd = quote.get("USD") or {}

        def _num(value, cast=float) -> float | None:
            try:
                return cast(value) if value is not None else None
            except (TypeError, ValueError):
                return None

        urls = listing.get("urls") or {}
        social: dict[str, str | None] = {}
        if isinstance(urls.get("twitter"), list) and urls["twitter"]:
            social["twitter"] = urls["twitter"][0]
        if isinstance(urls.get("website"), list) and urls["website"]:
            social["website"] = urls["website"][0]
        if isinstance(urls.get("reddit"), list) and urls["reddit"]:
            social["reddit"] = urls["reddit"][0]
        chats = urls.get("chat") if isinstance(urls.get("chat"), list) else []
        for link in chats:
            low = str(link).lower()
            if "t.me" in low:
                social["telegram"] = link
            elif "discord" in low:
                social["discord"] = link

        metrics = MarketMetrics(
            price_usd=_num(usd.get("price")),
            volume_24h=_num(usd.get("volume_24h")),
            fdv_usd=_num(usd.get("fully_diluted_market_cap")),
            market_cap_usd=_num(usd.get("market_cap")),
            price_change_1h=_num(usd.get("percent_change_1h")),
            price_change_6h=_num(usd.get("percent_change_6h")),
            price_change_24h=_num(usd.get("percent_change_24h")),
            # liquidity_usd: CMC does not provide DEX liquidity -> stays UNKNOWN.
        )

        token = NormalizedTokenCandidate(
            chain=chain,
            address=address,
            symbol=str(listing.get("symbol") or "UNKNOWN"),
            name=str(listing.get("name") or "Unknown Token"),
            metrics=metrics,
            social_presence=social,
            source_provider="coinmarketcap",
            retrieved_ts=time.time(),
            raw_payload_sha256=_sha(info_raw + b"|" + quote_raw),
        )
        token.identify_unknowns()
        return token

    def _http_error_envelope(self, e: urllib.error.HTTPError, t0: float) -> ProviderResponse:
        body = b""
        try:
            body = e.read() or b""
        except Exception:
            pass
        code = e.code
        detail = f"http {code}"
        if code in (401, 403):
            return ProviderResponse(
                provider_id="coinmarketcap", status="AUTH_REQUIRED", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0, http_status=code,
                error_message="CMC rejected the API key (http 401/403)",
            )
        if code == 400 and self._cmc_error_code(body) in (1001, 1002):
            return ProviderResponse(
                provider_id="coinmarketcap", status="AUTH_REQUIRED", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0, http_status=code,
                error_message="CMC API key invalid or inactive (error_code 1001/1002)",
            )
        if code == 429:
            return ProviderResponse(
                provider_id="coinmarketcap", status="RATE_LIMIT", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0, http_status=code,
                error_message="CMC rate ceiling reached (http 429)",
            )
        if code == 404:
            return ProviderResponse(
                provider_id="coinmarketcap", status="OK", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0, http_status=code,
                error_message="address not indexed on CoinMarketCap",
            )
        if code >= 500:
            return ProviderResponse(
                provider_id="coinmarketcap", status="DOWN", tokens=[],
                latency_ms=(time.time() - t0) * 1000.0, http_status=code,
                error_message=f"{detail} — provider-side failure",
            )
        return ProviderResponse(
            provider_id="coinmarketcap", status="ERROR", tokens=[],
            latency_ms=(time.time() - t0) * 1000.0, http_status=code,
            error_message=detail,
        )


def _sha(raw: bytes | str) -> str:
    b = raw if isinstance(raw, bytes) else str(raw).encode("utf-8")
    return hashlib.sha256(b).hexdigest()
