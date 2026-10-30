"""Public CFTC positioning as a whale-family vote. PAPER_ONLY. Composite weight stays 0.

Source: https://www.cftc.gov/dea/newcot/f_disagg.txt
Futures-only disaggregated file, no header row. Published column order:
0 market name, 2 report date (YYYY-MM-DD), 7 open interest,
13 managed-money long, 14 managed-money short.
The contracts below were present in that file on 2026-10-30.
Fixture percentiles in macro_overlays are not a source and are not read here.
"""
from __future__ import annotations

import csv
import json
import math
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.markets import signal_brain as sb

COT_URL = "https://www.cftc.gov/dea/newcot/f_disagg.txt"
COT_SCALE = 0.05  # pre-registered: net managed-money of 5% of open interest is tanh(1)
CACHE_NAME = "cftc_f_disagg_cache.txt"
CACHE_META = "cftc_f_disagg_cache.json"
CACHE_MAX_AGE_S = 10 * 24 * 3600

# Exact market names from the live file. Unlisted desks stay absent.
COT_CONTRACTS: dict[tuple[str, str], str] = {
    ("OIL", "BRENT"): "BRENT LAST DAY - NEW YORK MERCANTILE EXCHANGE",
    ("OIL", "WTI"): "CRUDE OIL, LIGHT SWEET-WTI - ICE FUTURES EUROPE",
    ("GOLD", "XAU"): "GOLD - COMMODITY EXCHANGE INC.",
}


def positioning_score(open_interest: float, managed_long: float, managed_short: float) -> float | None:
    if open_interest <= 0:
        return None
    frac = (managed_long - managed_short) / open_interest
    return round(max(-1.0, min(1.0, math.tanh(frac / COT_SCALE))), 4)


def parse_cot_row(text: str, market_name: str) -> dict[str, Any] | None:
    target = market_name.strip()
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            fields = next(csv.reader([line]))
        except csv.Error:
            continue
        if len(fields) <= 14 or fields[0].strip() != target:
            continue
        try:
            oi = float(fields[7].replace(",", "").strip())
            mm_long = float(fields[13].replace(",", "").strip())
            mm_short = float(fields[14].replace(",", "").strip())
        except ValueError:
            return None
        return {
            "market": target,
            "as_of": fields[2].strip(),
            "open_interest": oi,
            "managed_money_long": mm_long,
            "managed_money_short": mm_short,
            "score": positioning_score(oi, mm_long, mm_short),
        }
    return None


def _cache_paths(root: Path) -> tuple[Path, Path]:
    folder = root / "reports" / "grok" / "PAPER"
    return folder / CACHE_NAME, folder / CACHE_META


def _read_cache(root: Path, now: float) -> tuple[str | None, dict[str, Any]]:
    text_path, meta_path = _cache_paths(root)
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        fetched = float(meta.get("fetched_at_unix") or 0)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None, {"cache": "ABSENT"}
    age = now - fetched
    if age < 0 or age > CACHE_MAX_AGE_S:
        return None, {"cache": "STALE", "age_s": round(age, 1)}
    try:
        return text_path.read_text(encoding="latin-1"), {"cache": "HIT", "age_s": round(age, 1), "as_of_fetch": meta.get("fetched_at")}
    except OSError:
        return None, {"cache": "ABSENT"}


def load_cot_text(root: Path, *, now: float | None = None, fetch: bool = True) -> tuple[str | None, dict[str, Any]]:
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    if fetch:
        try:
            req = urllib.request.Request(COT_URL, headers={"User-Agent": "Mozilla/5.0 (AHOS paper research)"})
            with urllib.request.urlopen(req, timeout=25) as response:
                raw = response.read()
            text = raw.decode("latin-1", "replace")
        except (OSError, TimeoutError, ValueError):
            text = None
        else:
            if "BRENT LAST DAY" not in text:
                text = None
            else:
                text_path, meta_path = _cache_paths(root)
                try:
                    text_path.parent.mkdir(parents=True, exist_ok=True)
                    text_path.write_text(text, encoding="latin-1")
                    stamp = datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                    meta_path.write_text(
                        json.dumps({"fetched_at": stamp, "fetched_at_unix": now, "url": COT_URL, "bytes": len(raw)}),
                        encoding="utf-8",
                    )
                except OSError:
                    pass
                return text, {"cache": "REFRESHED", "url": COT_URL}
    cached, meta = _read_cache(root, now)
    if cached is not None:
        meta["url"] = COT_URL
        return cached, meta
    return None, {**meta, "url": COT_URL, "reason": "FEED_UNAVAILABLE"}


def cftc_cot_signal(root: Path, desk: str, symbol: str, *, text: str | None = None, meta: dict[str, Any] | None = None) -> dict[str, Any] | None:
    market = COT_CONTRACTS.get((desk, symbol))
    if market is None:
        return None
    if text is None:
        text, meta = load_cot_text(root)
    meta = dict(meta or {})
    evidence: dict[str, Any] = {
        "desk": desk,
        "symbol": symbol,
        "contract": market,
        "url": COT_URL,
        "composite_weight": 0.0,
        "authority": "ADVISORY_POSITIONING",
        "not_macro_overlay_fixture": True,
        "paper_only": True,
        **meta,
    }
    if not text:
        return sb._sig("cftc_cot", None, {**evidence, "reason": "FEED_UNAVAILABLE"}, COT_URL, "public_cot")
    row = parse_cot_row(text, market)
    if row is None or row.get("score") is None:
        return sb._sig("cftc_cot", None, {**evidence, "reason": "CONTRACT_ROW_MISSING"}, COT_URL, "public_cot")
    evidence.update(row)
    return sb._sig("cftc_cot", float(row["score"]), evidence, COT_URL, "public_cot")
