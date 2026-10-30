"""Public positioning as a whale-family vote. PAPER_ONLY. Composite weight stays 0.

Contracts are chosen by code, never by a name substring.

WTI is CFTC contract-market code 067651.
Gold is CFTC contract-market code 088691.
Brent is whichever of these has the higher open interest in the current file:
ICE futures-only Brent (market ICEU, commodity code B, FutOnly) or
NYMEX Brent financial (CFTC code 06765T). The chosen code is logged.

The score is tanh(z / 2), where z is the current managed-money net/open-interest
versus that contract's own prior 52 weekly readings. CFTC codes use the free
annual futures-only disaggregated files. The ICE Brent code uses the free ICE
historical CSV, because that contract is not in the CFTC file. A short history
does not fall back to a fixed scale.

Fixture percentiles in macro_overlays are not a source and are not read here.
"""
from __future__ import annotations

import csv
import io
import json
import math
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from architecture.markets import signal_brain as sb

CFTC_CURRENT_URL = "https://www.cftc.gov/dea/newcot/f_disagg.txt"
CFTC_HIST_URL = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
ICE_HIST_URL = "https://www.ice.com/publicdocs/futures/COTHist{year}.csv"

WTI_CODE = "067651"
GOLD_CODE = "088691"
NYMEX_BRENT_CODE = "06765T"
ICE_BRENT_CODE = "ICEU:B:FutOnly"
BRENT_CODES = frozenset({ICE_BRENT_CODE, NYMEX_BRENT_CODE})

HISTORY_WEEKS = 52
Z_DIVISOR = 2.0
CACHE_SCHEMA = 2
CACHE_MAX_AGE_S = 6 * 24 * 3600
CACHE_STALE_MAX_AGE_S = 21 * 24 * 3600

FIXED_CODES: dict[tuple[str, str], str] = {
    ("OIL", "WTI"): WTI_CODE,
    ("GOLD", "XAU"): GOLD_CODE,
}


def selection_record() -> dict[str, Any]:
    return {
        "WTI": {"cftc_contract_market_code": WTI_CODE},
        "XAU": {"cftc_contract_market_code": GOLD_CODE},
        "BRENT": {
            "rule": "highest_open_interest",
            "codes": [ICE_BRENT_CODE, NYMEX_BRENT_CODE],
            "chosen_code": "logged on the cycle",
        },
    }


def net_fraction(open_interest: float, managed_long: float, managed_short: float) -> float | None:
    if open_interest <= 0:
        return None
    return (managed_long - managed_short) / open_interest


def tanh_z_score(current: float, history: list[float]) -> tuple[float | None, dict[str, Any]]:
    """tanh(z/2) against the last 52 prior weekly net/open-interest readings."""
    if len(history) < HISTORY_WEEKS:
        return None, {"reason": "HISTORY_SHORT", "history_weeks": len(history), "history_weeks_required": HISTORY_WEEKS}
    window = history[-HISTORY_WEEKS:]
    mean = sum(window) / HISTORY_WEEKS
    var = sum((value - mean) ** 2 for value in window) / (HISTORY_WEEKS - 1)
    stdev = math.sqrt(var)
    if stdev == 0.0:
        return None, {"reason": "HISTORY_ZERO_VARIANCE", "history_weeks": HISTORY_WEEKS}
    z = (current - mean) / stdev
    score = round(max(-1.0, min(1.0, math.tanh(z / Z_DIVISOR))), 4)
    return score, {
        "z": round(z, 4),
        "mean_net_oi": round(mean, 6),
        "stdev_net_oi": round(stdev, 6),
        "history_weeks": HISTORY_WEEKS,
        "scale": "tanh(z/2)",
    }


def _num(value: str) -> float | None:
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def _iso_from_parts(month: str, day: str, year: str) -> str | None:
    try:
        return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    except ValueError:
        return None


def rows_from_cftc_text(text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            fields = next(csv.reader([line]))
        except csv.Error:
            continue
        if len(fields) <= 14:
            continue
        code = fields[3].strip()
        as_of = fields[2].strip()
        oi = _num(fields[7])
        mm_long = _num(fields[13])
        mm_short = _num(fields[14])
        if not code or oi is None or mm_long is None or mm_short is None or len(as_of) != 10:
            continue
        frac = net_fraction(oi, mm_long, mm_short)
        if frac is None:
            continue
        out.append(
            {
                "code": code,
                "market_name": fields[0].strip(),
                "as_of": as_of,
                "open_interest": oi,
                "managed_money_long": mm_long,
                "managed_money_short": mm_short,
                "net_oi": frac,
                "source": "cftc",
            }
        )
    return out


def rows_from_ice_text(text: str) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")))
    for row in reader:
        if not isinstance(row, dict):
            continue
        if (row.get("FutOnly_or_Combined") or "").strip() != "FutOnly":
            continue
        market = (row.get("CFTC_Market_Code") or "").strip()
        commodity = (row.get("CFTC_Commodity_Code") or "").strip()
        if not market or not commodity:
            continue
        date = (row.get("As_of_Date_Form_MM/DD/YYYY") or "").strip()
        parts = date.split("/")
        as_of = _iso_from_parts(*parts) if len(parts) == 3 else None
        oi = _num(row.get("Open_Interest_All") or "")
        mm_long = _num(row.get("M_Money_Positions_Long_All") or "")
        mm_short = _num(row.get("M_Money_Positions_Short_All") or "")
        if as_of is None or oi is None or mm_long is None or mm_short is None:
            continue
        frac = net_fraction(oi, mm_long, mm_short)
        if frac is None:
            continue
        out.append(
            {
                "code": f"{market}:{commodity}:FutOnly",
                "market_name": (row.get("Market_and_Exchange_Names") or "").strip(),
                "as_of": as_of,
                "open_interest": oi,
                "managed_money_long": mm_long,
                "managed_money_short": mm_short,
                "net_oi": frac,
                "source": "ice",
            }
        )
    return out


def select_contract(desk: str, symbol: str, rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    if (desk, symbol) == ("OIL", "BRENT"):
        found = [row for row in rows if row.get("code") in BRENT_CODES]
        if not found:
            return None
        latest: dict[str, dict[str, Any]] = {}
        for row in found:
            prev = latest.get(row["code"])
            if prev is None or row["as_of"] >= prev["as_of"]:
                latest[row["code"]] = row
        ordered = sorted(latest.values(), key=lambda row: (-float(row["open_interest"]), str(row["code"])))
        chosen = dict(ordered[0])
        chosen["chosen_code"] = chosen["code"]
        chosen["candidates"] = [
            {"code": row["code"], "open_interest": row["open_interest"], "as_of": row["as_of"]} for row in ordered
        ]
        return chosen
    code = FIXED_CODES.get((desk, symbol))
    if code is None:
        return None
    found = [row for row in rows if row.get("code") == code]
    if not found:
        return None
    found.sort(key=lambda row: row["as_of"])
    chosen = dict(found[-1])
    chosen["chosen_code"] = code
    chosen["candidates"] = [{"code": code, "open_interest": chosen["open_interest"], "as_of": chosen["as_of"]}]
    return chosen


def trailing_net_oi(points: list[tuple[str, float]], as_of: str) -> list[float]:
    dedup: dict[str, float] = {}
    for date, frac in points:
        if date < as_of:
            dedup[date] = frac
    return [dedup[date] for date in sorted(dedup)]


def _cache_dir(root: Path) -> Path:
    return root / "reports" / "grok" / "PAPER" / "cot_cache"


def _read_cached(root: Path, key: str, now: float, max_age: float) -> bytes | None:
    folder = _cache_dir(root)
    try:
        meta = json.loads((folder / f"{key}.json").read_text(encoding="utf-8"))
        if meta.get("schema") != CACHE_SCHEMA:
            return None
        age = now - float(meta["fetched_at_unix"])
        if age < 0 or age > max_age:
            return None
        return (folder / key).read_bytes()
    except (OSError, json.JSONDecodeError, TypeError, ValueError, KeyError):
        return None


def _write_cached(root: Path, key: str, raw: bytes, url: str, now: float) -> None:
    folder = _cache_dir(root)
    try:
        folder.mkdir(parents=True, exist_ok=True)
        (folder / key).write_bytes(raw)
        stamp = datetime.fromtimestamp(now, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        (folder / f"{key}.json").write_text(
            json.dumps({"schema": CACHE_SCHEMA, "fetched_at": stamp, "fetched_at_unix": now, "url": url, "bytes": len(raw)}),
            encoding="utf-8",
        )
    except OSError:
        return


def _fetch(url: str) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AHOS paper research)"})
        with urllib.request.urlopen(req, timeout=60) as response:
            return response.read()
    except (OSError, TimeoutError, ValueError):
        return None


def load_bytes(root: Path, key: str, url: str, *, now: float | None = None) -> tuple[bytes | None, dict[str, Any]]:
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    fresh = _read_cached(root, key, now, CACHE_MAX_AGE_S)
    if fresh is not None:
        return fresh, {"cache": "HIT", "url": url}
    raw = _fetch(url)
    if raw is not None:
        _write_cached(root, key, raw, url, now)
        return raw, {"cache": "REFRESHED", "url": url}
    stale = _read_cached(root, key, now, CACHE_STALE_MAX_AGE_S)
    if stale is not None:
        return stale, {"cache": "STALE", "url": url}
    return None, {"cache": "ABSENT", "url": url, "reason": "FEED_UNAVAILABLE"}


def _history_points_cftc(blob: bytes, code: str) -> list[tuple[str, float]]:
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            text = archive.read(archive.namelist()[0]).decode("latin-1", "replace")
    except (zipfile.BadZipFile, IndexError, OSError):
        return []
    return [(row["as_of"], float(row["net_oi"])) for row in rows_from_cftc_text(text) if row["code"] == code]


def _history_points_ice(text: str, code: str) -> list[tuple[str, float]]:
    return [(row["as_of"], float(row["net_oi"])) for row in rows_from_ice_text(text) if row["code"] == code]


def load_history(root: Path, code: str, source: str, as_of: str, *, now: float | None = None) -> tuple[list[float], str]:
    year = int(as_of[:4])
    points: list[tuple[str, float]] = []
    if source == "ice":
        for item in (year - 1, year):
            raw, _meta = load_bytes(root, f"COTHist{item}.csv", ICE_HIST_URL.format(year=item), now=now)
            if raw is None:
                continue
            points.extend(_history_points_ice(raw.decode("utf-8-sig", "replace"), code))
        return trailing_net_oi(points, as_of), ICE_HIST_URL.format(year=year)
    for item in (year - 1, year):
        raw, _meta = load_bytes(root, f"fut_disagg_{item}.zip", CFTC_HIST_URL.format(year=item), now=now)
        if raw is None:
            continue
        points.extend(_history_points_cftc(raw, code))
    return trailing_net_oi(points, as_of), CFTC_HIST_URL.format(year=year)


def load_current_rows(root: Path, desk: str, symbol: str, *, now: float | None = None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw, meta = load_bytes(root, "f_disagg.txt", CFTC_CURRENT_URL, now=now)
    rows = rows_from_cftc_text(raw.decode("latin-1", "replace")) if raw else []
    if (desk, symbol) == ("OIL", "BRENT"):
        year = datetime.now(timezone.utc).year
        ice_raw, ice_meta = load_bytes(root, f"COTHist{year}.csv", ICE_HIST_URL.format(year=year), now=now)
        meta = {**meta, "ice": ice_meta}
        if ice_raw:
            rows.extend(rows_from_ice_text(ice_raw.decode("utf-8-sig", "replace")))
    return rows, meta


def cftc_cot_signal(
    root: Path,
    desk: str,
    symbol: str,
    *,
    rows: list[dict[str, Any]] | None = None,
    history: dict[str, list[tuple[str, float]]] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if (desk, symbol) not in FIXED_CODES and (desk, symbol) != ("OIL", "BRENT"):
        return None
    if rows is None:
        rows, meta = load_current_rows(root, desk, symbol)
    meta = dict(meta or {})
    chosen = select_contract(desk, symbol, rows)
    evidence: dict[str, Any] = {
        "desk": desk,
        "symbol": symbol,
        "composite_weight": 0.0,
        "authority": "ADVISORY_POSITIONING",
        "not_macro_overlay_fixture": True,
        "paper_only": True,
        "scale": "tanh(z/2)",
        **meta,
    }
    if chosen is None:
        return sb._sig("cftc_cot", None, {**evidence, "reason": "CONTRACT_ROW_MISSING"}, CFTC_CURRENT_URL, "public_cot")
    evidence.update(
        {
            "chosen_code": chosen["chosen_code"],
            "candidates": chosen.get("candidates"),
            "market_name": chosen.get("market_name"),
            "as_of": chosen.get("as_of"),
            "open_interest": chosen.get("open_interest"),
            "managed_money_long": chosen.get("managed_money_long"),
            "managed_money_short": chosen.get("managed_money_short"),
            "net_oi": round(float(chosen["net_oi"]), 6),
            "history_source": "ice" if chosen.get("source") == "ice" else "cftc",
        }
    )
    if history is None:
        series, hist_url = load_history(root, chosen["chosen_code"], evidence["history_source"], chosen["as_of"])
        evidence["history_url"] = hist_url
    else:
        series = trailing_net_oi(history.get(chosen["chosen_code"]) or [], chosen["as_of"])
    score, detail = tanh_z_score(float(chosen["net_oi"]), series)
    evidence.update(detail)
    if score is None:
        return sb._sig("cftc_cot", None, evidence, CFTC_CURRENT_URL, "public_cot")
    return sb._sig("cftc_cot", score, evidence, CFTC_CURRENT_URL, "public_cot")
