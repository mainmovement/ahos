"""F3 — Objective C: verify the reported `NA` ticker release regression.

Compares the RELEASE 2.4.0 loader against the MAIN loader, finds the exact source
record, measures both behaviours on the same bytes, and — new — tests whether the
defect affects only equities or all seven asset classes.

Read-only. Isolated research venv. Neither upstream nor AHOS is modified.
"""
import bz2
import glob
import io
import json
import re
import subprocess
import sys

import pandas as pd

REPO = "/tmp/fdb2_repo"
SP = "/tmp/fdb2_venv/lib/python3.11/site-packages/financedatabase"
OUT = "/tmp/fdb2_lab/f3_na_regression.json"
R = {}

# ---- C-1/C-2/C-3: the two loader implementations and their exact difference ----
rel_helpers = open(f"{SP}/helpers.py", encoding="utf-8").read().splitlines()
main_helpers = open(f"{REPO}/financedatabase/helpers.py", encoding="utf-8").read().splitlines()


def find_read_csv(lines):
    return [(i + 1, l.strip()) for i, l in enumerate(lines) if "read_csv" in l]


R["C1_release_read_csv_lines"] = find_read_csv(rel_helpers)
R["C2_main_read_csv_lines"] = find_read_csv(main_helpers)
R["C1_release_has_keep_default_na"] = any("keep_default_na" in l for l in rel_helpers)
R["C2_main_has_keep_default_na"] = any("keep_default_na" in l for l in main_helpers)
R["C3_line_count_release"] = len(rel_helpers)
R["C3_line_count_main"] = len(main_helpers)

d = subprocess.run(["diff", "-u", f"{SP}/helpers.py", f"{REPO}/financedatabase/helpers.py"],
                   capture_output=True, text=True)
R["C3_diff_rc"] = d.returncode
R["C3_diff_unified"] = d.stdout
R["C3_diff_added_lines"] = [l for l in d.stdout.splitlines() if l.startswith("+") and not l.startswith("+++")]
R["C3_diff_removed_lines"] = [l for l in d.stdout.splitlines() if l.startswith("-") and not l.startswith("---")]

# also diff the whole package
d2 = subprocess.run(["diff", "-rq", SP, f"{REPO}/financedatabase"], capture_output=True, text=True)
R["C3_package_diff"] = d2.stdout.strip().splitlines()

# ---- C-4: the exact NA record in the SOURCE csv (not the compressed artifact) ----
hits = []
for p in sorted(glob.glob(f"{REPO}/database/equities/*.csv")):
    with open(p, encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            first = line.split(",")[0].strip('"')
            if first == "NA":
                hits.append({"file": p.replace(REPO + "/", ""), "line": i,
                             "raw_first_field": first,
                             "record_preview": line[:180].rstrip()})
R["C4_source_records_with_symbol_NA"] = hits
R["C4_count"] = len(hits)

# ---- C-5/C-6: both behaviours on the SAME bytes ----
p = f"{REPO}/compression/equities.bz2"
rel = pd.read_csv(p, compression="bz2", index_col=0)                                   # release
head = pd.read_csv(p, compression="bz2", index_col=0,
                   keep_default_na=False, na_values=[""])                              # main
R["C5_release_rows"] = len(rel)
R["C6_main_rows"] = len(head)
R["C5_release_index_nan_count"] = int(rel.index.isna().sum())
R["C6_main_index_nan_count"] = int(head.index.isna().sum())
R["C5_release_NA_in_index"] = bool("NA" in rel.index)
R["C6_main_NA_in_index"] = bool("NA" in head.index)
try:
    r = rel.loc["NA"]
    R["C5_release_loc_NA"] = {"name": r["name"], "country": r["country"], "exchange": r["exchange"]}
except Exception as e:
    R["C5_release_loc_NA"] = f"{type(e).__name__}: {str(e)[:100]}"
try:
    h = head.loc["NA"]
    R["C6_main_loc_NA"] = {"name": h["name"], "country": h["country"], "exchange": h["exchange"],
                           "isin": h.get("isin"), "summary_present": bool(str(h.get("summary")) != "")}
except Exception as e:
    R["C6_main_loc_NA"] = f"{type(e).__name__}: {str(e)[:100]}"

# cell-level divergence
div = {}
for c in rel.columns:
    a, b = int(rel[c].isna().sum()), int(head[c].isna().sum())
    if a != b:
        div[c] = {"release_NaN": a, "main_NaN": b, "delta": a - b}
R["C5_cell_level_divergence"] = div
R["C5_cell_level_divergence_empty"] = (div == {})

# ---- C-10: NEW — does this affect all seven asset classes? ----
PANDAS_DEFAULT_NA = {"", "#N/A", "#N/A N/A", "#NA", "-1.#IND", "-1.#QNAN", "-NaN", "-nan",
                     "1.#IND", "1.#QNAN", "<NA>", "N/A", "NA", "NULL", "NaN", "None",
                     "n/a", "nan", "null"}
R["C10_pandas_default_na_strings"] = sorted(PANDAS_DEFAULT_NA)
per_class = {}
for cls in ["equities", "etfs", "funds", "indices", "currencies", "cryptos", "moneymarkets"]:
    f = f"{REPO}/compression/{cls}.bz2"
    raw = pd.read_csv(f, compression="bz2", index_col=0, dtype=str, keep_default_na=False)
    idx = set(raw.index.astype(str))
    vulnerable = sorted(idx & PANDAS_DEFAULT_NA)
    dfault = pd.read_csv(f, compression="bz2", index_col=0)
    per_class[cls] = {
        "rows": len(raw),
        "index_values_matching_pandas_default_NA": vulnerable,
        "n_vulnerable": len(vulnerable),
        "release_index_nan_count": int(dfault.index.isna().sum()),
        "rows_lost_under_release_semantics": len(raw) - len(dfault.dropna(how="all")),
    }
R["C10_per_asset_class"] = per_class
R["C10_classes_affected"] = [k for k, v in per_class.items() if v["n_vulnerable"] > 0]
R["C10_ONLY_EQUITIES_AFFECTED"] = R["C10_classes_affected"] == ["equities"]

# also scan the SOURCE csvs for NA-like first fields across all classes
src_hits = {}
for pat in [f"{REPO}/database/*/*.csv", f"{REPO}/database/*.csv"]:
    for p in sorted(glob.glob(pat)):
        with open(p, encoding="utf-8") as f:
            next(f, None)
            for line in f:
                first = line.split(",")[0].strip('"')
                if first in PANDAS_DEFAULT_NA and first != "":
                    src_hits.setdefault(p.replace(REPO + "/", ""), []).append(first)
R["C10_source_csv_NA_like_first_fields"] = src_hits

# ---- C-8/C-9: was the fix released? git history of the fix ----
log = subprocess.run(["git", "-C", REPO, "log", "--format=%H|%ad|%an|%s", "--date=short",
                      "--", "financedatabase/helpers.py"], capture_output=True, text=True)
R["C8_helpers_history"] = log.stdout.strip().splitlines()[:12]
blame = subprocess.run(["git", "-C", REPO, "log", "-S", "keep_default_na", "--format=%H|%ad|%s",
                        "--date=iso", "--", "financedatabase/helpers.py"],
                       capture_output=True, text=True)
R["C9_commits_introducing_keep_default_na"] = blame.stdout.strip().splitlines()
tags = subprocess.run(["git", "-C", REPO, "tag", "--sort=-creatordate"], capture_output=True, text=True)
R["C8_tags"] = tags.stdout.strip().splitlines()[:6]
R["C8_release_2.4.0_date"] = "2026-06-02 (PyPI upload_time, recorded in 16_EVIDENCE_REGISTER)"

with open(OUT, "w") as f:
    json.dump(R, f, indent=2, default=str)
print(json.dumps({k: v for k, v in R.items() if not k.startswith("C3_diff_unified")},
                 indent=2, default=str)[:9000])
print("\nwrote", OUT)
