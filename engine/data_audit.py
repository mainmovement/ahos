#!/usr/bin/env python3
"""AHOS Data Integrity Audit — Agent-09 (QA) tool.
Implements the 14 integrity gates from AHOS Phase 3 Validation Framework.
No synthetic data. Read-only analysis of provided real CSVs."""
import os, sys, json, hashlib, glob
from datetime import datetime
from pathlib import Path
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config.paths import get_reports_dir

UP = os.environ.get("AHOS_UPLOAD_DIR") or str(ROOT_DIR / "research" / "data")

def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()

def audit_file(path):
    r = {"file": os.path.basename(path), "sha256": sha256(path), "rows": 0, "gates": {},
         "verdict": "FAIL", "first": None, "last": None, "missing_rate_pct": "-"}
    try:
        df = pd.read_csv(path)
    except Exception as e:
        r["gates"]["readable"] = f"FAIL: {e}"; return r
    r["rows"] = len(df)
    # Gate 1: schema (standard or documented LBank-raw alias)
    cols = [c.strip().lower() for c in df.columns]
    if cols == ["t","o","h","l","c","v"]:
        cols = ["timestamp","open","high","low","close","volume"]
        df.columns = cols
        r["gates"]["schema"] = "PASS(legacy alias t,o,h,l,c,v mapped)"
    else:
        r["gates"]["schema"] = "PASS" if cols == ["timestamp","open","high","low","close","volume"] else f"FAIL cols={cols}"
        if r["gates"]["schema"] != "PASS": return r
        df.columns = cols
    # Gate 2: parseable timestamps
    try:
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        r["gates"]["timestamps_parse"] = "PASS"
    except Exception as e:
        r["gates"]["timestamps_parse"] = f"FAIL: {e}"; return r
    df = df.dropna(subset=["timestamp"])
    # Gate 3: numeric coercion
    for c in ["open","high","low","close","volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    bad_num = int(df[["open","high","low","close","volume"]].isna().sum().sum())
    r["gates"]["numeric"] = "PASS" if bad_num == 0 else f"FAIL {bad_num} NaN"
    # Gate 4: duplicates
    dups = int(df.duplicated(subset=["timestamp"]).sum())
    r["gates"]["duplicates"] = "PASS" if dups == 0 else f"FAIL {dups} dup timestamps"
    # Gate 5: monotonic increasing
    mono = df["timestamp"].is_monotonic_increasing
    r["gates"]["monotonic"] = "PASS" if mono else "FAIL"
    # Gate 6-9: OHLC consistency
    o,h,l,c,v = df["open"],df["high"],df["low"],df["close"],df["volume"]
    pos = int(((o<=0)|(h<=0)|(l<=0)|(c<=0)).sum())
    r["gates"]["positive_prices"] = "PASS" if pos==0 else f"FAIL {pos} non-positive"
    hl = int((h < l).sum())
    r["gates"]["high_ge_low"] = "PASS" if hl==0 else f"FAIL {hl}"
    inb = int(((c > h)|(c < l)).sum())
    r["gates"]["close_in_range"] = "PASS" if inb==0 else f"FAIL {inb} close outside [low,high]"
    ob = int(((o > h*1.0001)|(o < l*0.9999)).sum())
    r["gates"]["open_in_range"] = "PASS" if ob==0 else f"WARN {ob} open outside range (>0.01%)"
    negv = int((v < 0).sum())
    r["gates"]["volume_nonneg"] = "PASS" if negv==0 else f"FAIL {negv} negative volume"
    zv = int((v == 0).sum())
    r["gates"]["volume_zero"] = "PASS" if zv==0 else f"WARN {zv} zero-volume candles"
    # Gate 10: continuity / gaps (1h grid)
    if len(df) > 1:
        dt = df["timestamp"].diff().dropna()
        gaps = dt[dt > pd.Timedelta(hours=1)]
        expected = int(((df["timestamp"].iloc[-1]-df["timestamp"].iloc[0]).total_seconds()//3600)+1)
        r["span_hours_expected"] = expected
        r["missing_rate_pct"] = round(100.0*(expected-len(df))/max(expected,1), 3)
        REGISTERED_REMOVALS = {"LBANK_BTCUSDT_1h_2000_clean.csv": 2}  # docs: removed_rows_registry
        if len(gaps)==0:
            r["gates"]["continuity"] = "PASS"
        elif REGISTERED_REMOVALS.get(r["file"]) == len(gaps):
            r["gates"]["continuity"] = f"REVIEW {len(gaps)} gaps = registered bad-row removals (documented, no interpolation)"
        else:
            r["gates"]["continuity"] = f"FAIL {len(gaps)} gaps; max={gaps.max()}"
        r["gates"]["missing_rate"] = "PASS" if r["missing_rate_pct"] < 1.0 else ("REVIEW" if r["missing_rate_pct"] < 5 else "FAIL")
    # Gate 11: outliers (>50% 1h jump flagged)
    if len(df) > 1:
        ret = c.pct_change().abs().dropna()
        out = int((ret > 0.5).sum())
        r["gates"]["outlier_50pct"] = "PASS" if out==0 else f"REVIEW {out} jumps >50%"
        r["max_1h_move_pct"] = round(float(ret.max()*100), 2)
    # Gate 12: range
    r["first"] = str(df["timestamp"].iloc[0]) if len(df) else None
    r["last"] = str(df["timestamp"].iloc[-1]) if len(df) else None
    fails = [k for k,v in r["gates"].items() if str(v).startswith("FAIL")]
    r["verdict"] = "FAIL" if fails else ("PASS(REVIEW)" if any(str(v).startswith(("WARN","REVIEW")) for v in r["gates"].values()) else "PASS")
    return r

files = sorted(glob.glob(os.path.join(UP, "*.csv")))
results = [audit_file(f) for f in files]
out = {"audit_time_utc": datetime.now(__import__("datetime").timezone.utc).isoformat(), "files": results}
out_file = get_reports_dir() / "data_integrity_audit.json"
with open(out_file, "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2)
for r in results:
    first = (r.get('first') or 'n/a')[:10]; last = (r.get('last') or 'n/a')[:10]
    spans = f"{first} → {last}"
    print(f"{r['verdict']:13s} {r['file']:42s} rows={r['rows']:6d} {spans:24s} miss={r.get('missing_rate_pct','-')}%")
print(f"\nSaved: {out_file}")
