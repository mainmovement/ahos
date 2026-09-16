"""F5 — Objective D: close U-12 by replicating the Check-GICS-Categorisation job locally.

Runs the EXACT logic from .github/workflows/database_update.yml (Check-GICS-Categorisation
step) against the pinned commit, read-only. The CI log could not be fetched (Azure blob
host unreachable from the audit sandbox), so the check is re-executed instead — which is
stronger evidence than the log.

Nothing is written to the repository. No --apply. Read-only.
"""
import glob
import json

import pandas as pd

REPO = "/tmp/fdb2_repo"
OUT = "/tmp/fdb2_lab/f5_gics_replication.json"
R = {}

gics = json.load(open(f"{REPO}/compression/categories/categories.json"))
R["gics_json_top_level_keys"] = sorted(gics.keys())
R["gics_n_sectors"] = len(gics)
R["gics_n_industry_groups"] = len({g for s in gics.values() for g in s})
R["gics_n_industries"] = len({i for s in gics.values() for g in s.values() for i in g})

# EXACT replication of the workflow logic (same read_csv call, no dtype override)
equities = pd.concat([pd.read_csv(f, index_col=0)
                      for f in sorted(glob.glob(f"{REPO}/database/equities/*.csv"))])
R["equities_rows"] = len(equities)

filtered = equities[equities["sector"].notna() & equities["industry_group"].notna()
                    & equities["industry"].notna()]
R["rows_with_full_gics_triple"] = len(filtered)
R["rows_excluded_missing_triple"] = len(equities) - len(filtered)

invalid = []
for index, row in filtered.iterrows():
    sector, ig, ind = row["sector"], row["industry_group"], row["industry"]
    try:
        gics[sector][ig][ind]
    except KeyError as error:
        invalid.append({"symbol": str(index), "error": str(error), "sector": str(sector),
                        "industry_group": str(ig), "industry": str(ind),
                        "name": str(row.get("name", ""))[:60],
                        "country": str(row.get("country", "")),
                        "exchange": str(row.get("exchange", ""))})

R["invalid_row_count"] = len(invalid)
R["invalid_rows"] = invalid[:400]
R["WORKFLOW_WOULD_RAISE"] = len(invalid) > 0

# classify the failures
if invalid:
    df = pd.DataFrame(invalid)
    R["by_missing_sector"] = {k: int(v) for k, v in
                              df[~df["sector"].isin(gics.keys())]["sector"].value_counts().items()}
    R["distinct_bad_sectors"] = sorted({s for s in df["sector"] if s not in gics})
    R["distinct_bad_industry_groups"] = sorted(
        {r["industry_group"] for _, r in df.iterrows()
         if r["sector"] in gics and r["industry_group"] not in gics[r["sector"]]})
    R["distinct_bad_industries"] = sorted(
        {r["industry"] for _, r in df.iterrows()
         if r["sector"] in gics and r["industry_group"] in gics[r["sector"]]
         and r["industry"] not in gics[r["sector"]][r["industry_group"]]})
    R["by_exchange"] = {k: int(v) for k, v in df["exchange"].value_counts().head(10).items()}
    R["by_country"] = {k: int(v) for k, v in df["country"].value_counts().head(10).items()}

with open(OUT, "w") as f:
    json.dump(R, f, indent=2, default=str)

print(f"categories.json: {R['gics_n_sectors']} sectors / "
      f"{R['gics_n_industry_groups']} industry groups / {R['gics_n_industries']} industries")
print(f"equities rows: {R['equities_rows']}  with full triple: {R['rows_with_full_gics_triple']}")
print(f"INVALID ROWS: {R['invalid_row_count']}   -> workflow raises: {R['WORKFLOW_WOULD_RAISE']}")
for k in ["distinct_bad_sectors", "distinct_bad_industry_groups", "distinct_bad_industries"]:
    print(f"  {k}: {R.get(k)}")
print("\nfirst 12 invalid rows:")
for r in R["invalid_rows"][:12]:
    print(f"  {r['symbol']:14} {r['error'][:70]:72} | {r['name'][:34]:36} | {r['country']}")
print("\nby exchange:", R.get("by_exchange"))
print("by country :", R.get("by_country"))
print("\nwrote", OUT)
