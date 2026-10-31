"""Dated free-data caches for the shadow strategies that had no input. PAPER_ONLY.

A cache is not a promotion. Name-level factor loadings are not invented from
the Kenneth French factor file. A session range is not a quoted spread.
"""
from __future__ import annotations

import csv
import io
import json
import math
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

CACHE_REL = Path("reports") / "grok" / "PAPER" / "free_data"
STATUS_REL = CACHE_REL / "status.json"
UA = "Mozilla/5.0 (AHOS paper research)"
MIN_Z = 8

# The sixteen library rules that did not signal on a close-only frame.
GAPS = (
    "cs_momentum",
    "pairs_zscore",
    "futures_carry",
    "turn_of_month",
    "overnight_intraday",
    "commodity_calendar",
    "pre_fomc",
    "pead",
    "news_shock",
    "macro_surprise",
    "low_vol",
    "cot_extreme",
    "liquidations",
    "funding_oi_squeeze",
    "wick_sweep",
    "fama_french",
)


def _utc(moment: datetime | None = None) -> str:
    now = moment or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return now.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def last_z(values: list[float]) -> float | None:
    """Z of the last point against the earlier points. One print is not a z-score."""
    if len(values) < MIN_Z:
        return None
    prior = values[:-1]
    mean = sum(prior) / len(prior)
    var = sum((item - mean) ** 2 for item in prior) / (len(prior) - 1)
    if var <= 0:
        return None
    return round((values[-1] - mean) / math.sqrt(var), 4)


def write_cache(root: Path, name: str, doc: dict[str, Any]) -> Path:
    stamp = str(doc.get("fetched_at") or _utc())
    folder = Path(root) / CACHE_REL / name
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{stamp[:10]}.json"
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return path


def _get(url: str, timeout: float = 20.0) -> tuple[int | None, bytes]:
    req = Request(url, headers={"User-Agent": UA, "Accept": "text/csv,application/json,*/*"})
    try:
        with urlopen(req, timeout=timeout) as resp:
            return int(getattr(resp, "status", 200) or 200), resp.read()
    except HTTPError as exc:
        return int(exc.code), b""
    except (URLError, TimeoutError, OSError, ValueError):
        return None, b""


def parse_fred_csv(text: str) -> list[tuple[str, float]]:
    rows: list[tuple[str, float]] = []
    for record in csv.DictReader(io.StringIO(text)):
        raw = record.get("CPIAUCSL") or record.get("VALUE") or record.get("UNRATE")
        day = record.get("DATE") or record.get("observation_date")
        if not day or raw in (None, "", "."):
            continue
        try:
            rows.append((day, float(raw)))
        except ValueError:
            continue
    return rows


def parse_french_factors(text: str) -> list[dict[str, float]]:
    """Monthly market, size, and value factors. These are not a stock's loadings."""
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if "Mkt-RF" in line), None)
    if start is None:
        return []
    out: list[dict[str, float]] = []
    for record in csv.DictReader(io.StringIO("\n".join(lines[start:]))):
        try:
            out.append({
                "mkt_rf": float(record["Mkt-RF"]),
                "smb": float(record["SMB"]),
                "hml": float(record["HML"]),
            })
        except (KeyError, TypeError, ValueError):
            if out:
                break
    return out


def cot_z_from_zip(blob: bytes, code: str) -> dict[str, Any]:
    from architecture.markets.cftc_cot import rows_from_cftc_text

    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            text = archive.read(archive.namelist()[0]).decode("latin-1", "replace")
    except (zipfile.BadZipFile, IndexError, OSError):
        return {"status": "UNAVAILABLE", "reason": "CFTC_ZIP_UNREADABLE", "n": 0, "z": None}
    points = [float(row["net_oi"]) for row in rows_from_cftc_text(text) if row["code"] == code]
    score = last_z(points)
    if score is None:
        return {"status": "UNAVAILABLE", "reason": "CFTC_HISTORY_SHORT", "n": len(points), "z": None}
    return {"status": "READY", "reason": None, "n": len(points), "z": score}


def classify(facts: dict[str, Any]) -> list[dict[str, Any]]:
    """One row per gap. READY only when the cited input is actually in hand."""
    cot = facts.get("cot") or {}
    funding = facts.get("funding") or {}
    ohlc = facts.get("ohlc") or {}
    second = facts.get("second_contract") or {}
    french = facts.get("french") or {}
    fred = facts.get("fred") or {}
    earnings = facts.get("earnings") or {}
    liquid = facts.get("liquidations") or {}
    bars_ok = bool(ohlc.get("bars", 0) >= 5 and ohlc.get("has_ohlc"))
    rows = {
        "cs_momentum": ("UNAVAILABLE", "NO_ALIGNED_PRICE_PANEL"),
        "pairs_zscore": ("UNAVAILABLE", "NO_ALIGNED_PRICE_PANEL"),
        "low_vol": ("UNAVAILABLE", "NO_ALIGNED_PRICE_PANEL"),
        "turn_of_month": ("UNAVAILABLE", "NO_ALIGNED_DAY_SERIES"),
        "pre_fomc": ("UNAVAILABLE", "NO_ALIGNED_DAY_SERIES"),
        "commodity_calendar": ("UNAVAILABLE", "NO_MONTH_PATH"),
        "news_shock": ("UNAVAILABLE", "NO_KEYLESS_NUMERIC_NEWS"),
        "macro_surprise": (
            "UNAVAILABLE",
            "FRED_HAS_ACTUAL_NOT_CONSENSUS" if fred.get("n") else "FRED_UNAVAILABLE",
        ),
        "pead": (
            "UNAVAILABLE",
            "NO_EARNINGS_SURPRISE" if earnings.get("dates") else str(earnings.get("reason") or "NO_EARNINGS_SURPRISE"),
        ),
        "futures_carry": (
            ("READY", None) if second.get("front") is not None and second.get("back") is not None
            else ("UNAVAILABLE", str(second.get("reason") or "NO_SECOND_CONTRACT"))
        ),
        "overnight_intraday": ("READY", None) if bars_ok else ("UNAVAILABLE", str(ohlc.get("reason") or "NO_INTRADAY_OHLC")),
        "wick_sweep": ("READY", None) if bars_ok else ("UNAVAILABLE", str(ohlc.get("reason") or "NO_INTRADAY_OHLC")),
        "cot_extreme": ("READY", None) if cot.get("status") == "READY" else ("UNAVAILABLE", str(cot.get("reason") or "CFTC_HISTORY_NOT_PULLED")),
        "funding_oi_squeeze": (
            ("READY", None) if funding.get("funding_z") is not None and funding.get("oi_z") is not None
            else ("UNAVAILABLE", str(funding.get("reason") or "ONE_PRINT_IS_NOT_A_Z"))
        ),
        "liquidations": ("UNAVAILABLE", str(liquid.get("reason") or "NO_KEYLESS_LIQUIDATION_PRINT")),
        "fama_french": (
            "UNAVAILABLE",
            "FACTORS_HAVE_NO_NAME_LOADING" if french.get("n") else str(french.get("reason") or "FRENCH_FILE_ABSENT"),
        ),
    }
    out = []
    for name in GAPS:
        status, reason = rows[name]
        out.append({
            "strategy": name,
            "data": status,
            "reason": reason,
            "applied_to_live": False,
            "promoted": False,
        })
    return out


def fetch_funding_oi(root: Path) -> dict[str, Any]:
    code, raw = _get("https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&limit=30")
    rates: list[float] = []
    if code == 200 and raw:
        try:
            payload = json.loads(raw.decode("utf-8"))
            rates = [float(row["fundingRate"]) for row in payload if isinstance(row, dict) and "fundingRate" in row]
        except (json.JSONDecodeError, TypeError, ValueError, KeyError):
            rates = []
    code_oi, raw_oi = _get("https://fapi.binance.com/futures/data/openInterestHist?symbol=BTCUSDT&period=1h&limit=30")
    ois: list[float] = []
    if code_oi == 200 and raw_oi:
        try:
            payload = json.loads(raw_oi.decode("utf-8"))
            ois = [float(row["sumOpenInterest"]) for row in payload if isinstance(row, dict) and "sumOpenInterest" in row]
        except (json.JSONDecodeError, TypeError, ValueError, KeyError):
            ois = []
    fz, oz = last_z(rates), last_z(ois)
    reason = None
    if fz is None or oz is None:
        reason = "ONE_PRINT_IS_NOT_A_Z" if (rates or ois) else "BINANCE_PUBLIC_EMPTY"
    doc = {
        "schema": "ahos.free_funding.v1",
        "paper_only": True,
        "fetched_at": _utc(),
        "source": "binance_fapi_public",
        "n_funding": len(rates),
        "n_oi": len(ois),
        "funding_z": fz,
        "oi_z": oz,
        "reason": reason,
        "applied_to_live": False,
    }
    write_cache(root, "funding_oi", doc)
    return doc


def fetch_fred_actuals(root: Path) -> dict[str, Any]:
    code, raw = _get("https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL")
    rows = parse_fred_csv(raw.decode("utf-8", "replace")) if code == 200 and raw else []
    doc = {
        "schema": "ahos.free_fred.v1",
        "paper_only": True,
        "fetched_at": _utc(),
        "series": "CPIAUCSL",
        "http_status": code,
        "n": len(rows),
        "last_date": rows[-1][0] if rows else None,
        "consensus": None,
        "reason": None if rows else "FRED_UNAVAILABLE",
        "surprise": "UNAVAILABLE",
        "surprise_reason": "FRED_HAS_ACTUAL_NOT_CONSENSUS",
        "applied_to_live": False,
    }
    write_cache(root, "fred", doc)
    return doc


def fetch_french_factors(root: Path) -> dict[str, Any]:
    url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/F-F_Research_Data_Factors_CSV.zip"
    code, raw = _get(url, timeout=30.0)
    factors: list[dict[str, float]] = []
    reason = None
    if code != 200 or not raw:
        reason = "FRENCH_HTTP_FAILED"
    else:
        try:
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                name = next(item for item in archive.namelist() if item.lower().endswith(".csv"))
                factors = parse_french_factors(archive.read(name).decode("utf-8", "replace"))
        except (zipfile.BadZipFile, StopIteration, OSError):
            reason = "FRENCH_ZIP_UNREADABLE"
        if not factors and reason is None:
            reason = "FRENCH_PARSE_EMPTY"
    doc = {
        "schema": "ahos.free_french.v1",
        "paper_only": True,
        "fetched_at": _utc(),
        "http_status": code,
        "n": len(factors),
        "name_loadings": None,
        "reason": "FACTORS_HAVE_NO_NAME_LOADING" if factors else reason,
        "applied_to_live": False,
    }
    write_cache(root, "french", doc)
    return doc


def fetch_cot_local(root: Path) -> dict[str, Any]:
    folder = Path(root) / "reports" / "grok" / "PAPER" / "cot_cache"
    points: list[float] = []
    for name in ("fut_disagg_2025.zip", "fut_disagg_2026.zip"):
        path = folder / name
        if not path.is_file():
            continue
        from architecture.markets.cftc_cot import rows_from_cftc_text
        try:
            with zipfile.ZipFile(path) as archive:
                text = archive.read(archive.namelist()[0]).decode("latin-1", "replace")
        except (zipfile.BadZipFile, IndexError, OSError):
            continue
        points.extend(float(row["net_oi"]) for row in rows_from_cftc_text(text) if row["code"] == "088691")
        del text
    score = last_z(points)
    if not points:
        doc = {"status": "UNAVAILABLE", "reason": "CFTC_HISTORY_NOT_PULLED", "n": 0, "z": None}
    elif score is None:
        doc = {"status": "UNAVAILABLE", "reason": "CFTC_HISTORY_SHORT", "n": len(points), "z": None}
    else:
        doc = {"status": "READY", "reason": None, "n": len(points), "z": score}
    doc.update({
        "schema": "ahos.free_cot.v1",
        "paper_only": True,
        "fetched_at": _utc(),
        "code": "088691",
        "source": "local_cftc_zip",
        "applied_to_live": False,
    })
    write_cache(root, "cot", doc)
    return doc


def fetch_second_contract(root: Path) -> dict[str, Any]:
    front = _yahoo_close("GC=F")
    back = _yahoo_close("GCZ26.CME")
    reason = None if front is not None and back is not None else "NO_SECOND_CONTRACT"
    doc = {
        "schema": "ahos.free_second_contract.v1",
        "paper_only": True,
        "fetched_at": _utc(),
        "front_symbol": "GC=F",
        "back_symbol": "GCZ26.CME",
        "front": front,
        "back": back,
        "reason": reason,
        "applied_to_live": False,
    }
    write_cache(root, "second_contract", doc)
    return doc


def _yahoo_close(symbol: str) -> float | None:
    code, raw = _get(
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        + symbol
        + "?range=5d&interval=1d"
    )
    if code != 200 or not raw:
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
        result = ((payload.get("chart") or {}).get("result") or [None])[0] or {}
        closes = ((result.get("indicators") or {}).get("quote") or [{}])[0].get("close") or []
        nums = [float(value) for value in closes if isinstance(value, (int, float))]
    except (json.JSONDecodeError, TypeError, ValueError, IndexError, AttributeError):
        return None
    return nums[-1] if nums else None


def _binance_klines() -> dict[str, Any]:
    code, raw = _get("https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=5m&limit=30")
    if code != 200 or not raw:
        return {"bars": 0, "has_ohlc": False, "reason": "NO_INTRADAY_OHLC", "symbol": "BTCUSDT"}
    try:
        payload = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {"bars": 0, "has_ohlc": False, "reason": "NO_INTRADAY_OHLC", "symbol": "BTCUSDT"}
    highs, lows, closes = [], [], []
    for row in payload:
        if not isinstance(row, list) or len(row) < 5:
            continue
        try:
            highs.append(float(row[2]))
            lows.append(float(row[3]))
            closes.append(float(row[4]))
        except (TypeError, ValueError):
            continue
    has = len(closes) >= 5 and len(highs) == len(closes) and len(lows) == len(closes)
    return {
        "symbol": "BTCUSDT",
        "bars": len(closes),
        "has_ohlc": has,
        "reason": None if has else "NO_INTRADAY_OHLC",
        "stock_reason": "YAHOO_5M_EMPTY",
    }


def fetch_intraday(root: Path) -> dict[str, Any]:
    from architecture.markets.equity_universe import fetch_intraday_bars

    got = fetch_intraday_bars(["NASDAQ:INTC"])
    row = got.get("NASDAQ:INTC") or {}
    closes = [float(v) for v in (row.get("closes") or []) if isinstance(v, (int, float))]
    has = bool(row.get("high") is not None and row.get("low") is not None and len(closes) >= 5)
    if has:
        doc = {
            "symbol": "NASDAQ:INTC",
            "bars": len(closes),
            "has_ohlc": True,
            "reason": None,
        }
    else:
        doc = _binance_klines()
    doc.update({
        "schema": "ahos.free_ohlc.v1",
        "paper_only": True,
        "fetched_at": _utc(),
        "applied_to_live": False,
    })
    write_cache(root, "ohlc", doc)
    return doc


def fetch_earnings_dates(root: Path) -> dict[str, Any]:
    code, raw = _get("https://www.sec.gov/files/company_tickers.json", timeout=25.0)
    dates: list[str] = []
    reason = "SEC_TICKERS_UNAVAILABLE"
    if code == 200 and raw:
        try:
            payload = json.loads(raw.decode("utf-8"))
            cik = next(
                str(row["cik_str"]).zfill(10)
                for row in payload.values()
                if isinstance(row, dict) and str(row.get("ticker") or "").upper() == "INTC"
            )
        except (json.JSONDecodeError, StopIteration, TypeError, ValueError, KeyError):
            cik = ""
        if cik:
            code2, body = _get(f"https://data.sec.gov/submissions/CIK{cik}.json", timeout=25.0)
            if code2 == 200 and body:
                try:
                    doc = json.loads(body.decode("utf-8"))
                    recent = (doc.get("filings") or {}).get("recent") or {}
                    forms = recent.get("form") or []
                    filed = recent.get("filingDate") or []
                    dates = [filed[i] for i, form in enumerate(forms) if form in {"10-Q", "10-K", "8-K"} and i < len(filed)][:12]
                    reason = "NO_EARNINGS_SURPRISE"
                except (json.JSONDecodeError, TypeError, ValueError):
                    reason = "SEC_SUBMISSIONS_UNREADABLE"
            else:
                reason = "SEC_SUBMISSIONS_UNAVAILABLE"
    doc = {
        "schema": "ahos.free_earnings.v1",
        "paper_only": True,
        "fetched_at": _utc(),
        "symbol": "INTC",
        "dates": dates,
        "surprise": None,
        "reason": reason,
        "applied_to_live": False,
    }
    write_cache(root, "earnings", doc)
    return doc


def fetch_liquidations(root: Path) -> dict[str, Any]:
    code, _raw = _get("https://fapi.binance.com/fapi/v1/allForceOrders?symbol=BTCUSDT&limit=5")
    doc = {
        "schema": "ahos.free_liquidations.v1",
        "paper_only": True,
        "fetched_at": _utc(),
        "http_status": code,
        "reason": "NO_KEYLESS_LIQUIDATION_PRINT",
        "applied_to_live": False,
    }
    write_cache(root, "liquidations", doc)
    return doc


def _latest(root: Path, name: str) -> dict[str, Any]:
    folder = Path(root) / CACHE_REL / name
    files = sorted(folder.glob("*.json")) if folder.is_dir() else []
    if not files:
        return {}
    try:
        doc = json.loads(files[-1].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return doc if isinstance(doc, dict) else {}


def assemble(root: Path, *, peak_mb: float | None = None) -> dict[str, Any]:
    pieces = {name: _latest(root, name) for name in (
        "cot", "funding_oi", "ohlc", "second_contract", "french", "fred", "earnings", "liquidations",
    )}
    pieces["funding"] = pieces.pop("funding_oi", {})
    return build_status(root, pieces, peak_mb=peak_mb)


def build_status(root: Path, pieces: dict[str, Any], *, peak_mb: float | None) -> dict[str, Any]:
    rows = classify({
        "cot": pieces.get("cot") or {},
        "funding": pieces.get("funding") or {},
        "ohlc": pieces.get("ohlc") or {},
        "second_contract": pieces.get("second_contract") or {},
        "french": pieces.get("french") or {},
        "fred": pieces.get("fred") or {},
        "earnings": pieces.get("earnings") or {},
        "liquidations": pieces.get("liquidations") or {},
    })
    doc = {
        "schema": "ahos.mega14_free_data.v1",
        "paper_only": True,
        "fetched_at": _utc(),
        "strategies": rows,
        "ready": sum(1 for row in rows if row["data"] == "READY"),
        "unavailable": sum(1 for row in rows if row["data"] == "UNAVAILABLE"),
        "peak_rss_mb": peak_mb,
        "promoted": False,
        "applied_to_live": False,
    }
    path = Path(root) / STATUS_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return doc


def publish(root: Path, status: dict[str, Any]) -> None:
    """Merge the data receipt into traces. Leave every other section in place."""
    from agent_org.contracts import AgentMessage, RequiredAction
    from architecture.mission.world_state import MessageBus, WorldStateStore
    from architecture.university.tech_scout import negahban_review

    review = negahban_review({"kind": "data", "license": "CC0-1.0", "idea": "free keyless caches"})
    root = Path(root)
    store = WorldStateStore(root)
    prev = store.read()
    traces = dict((prev.get("sections") or {}).get("traces") or {})
    traces["mega14_data"] = {
        "ts": status.get("fetched_at"),
        "ready": status.get("ready"),
        "unavailable": status.get("unavailable"),
        "peak_rss_mb": status.get("peak_rss_mb"),
        "negahban": review.get("verdict"),
        "promoted": False,
        "decides": False,
    }
    store.commit({"traces": traces}, {"traces": "AG-33"})
    MessageBus(root).deliver(AgentMessage(
        "AG-33", "AG-09", (str(STATUS_REL).replace("\\", "/"),),
        "free data caches logged",
        1.0, RequiredAction.OBSERVE,
    ))
    status["negahban"] = review
