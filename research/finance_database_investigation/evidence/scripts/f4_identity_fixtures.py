"""F4 — Objective B: verify the reported identity edge cases and extract exact source records.

For each reported case, pulls the ACTUAL rows so a fixture can be specified from real
data rather than from prose. Read-only.

Cases: CHAD cross-asset collision | BRK-A / BRK/A venue contradiction | MMM repeated
ticker | ISIN-to-many-symbol | 'two' placeholder records.
"""
import json

import pandas as pd

B = "/tmp/fdb2_repo/compression/"
OUT = "/tmp/fdb2_lab/f4_identity.json"
R = {}


def L(f):
    return pd.read_csv(B + f, compression="bz2", dtype=str, keep_default_na=False)


eq, et, fu = L("equities.bz2"), L("etfs.bz2"), L("funds.bz2")
ix, cu, cr, mm = L("indices.bz2"), L("currencies.bz2"), L("cryptos.bz2"), L("moneymarkets.bz2")
ALL = {"equities": eq, "etfs": et, "funds": fu, "indices": ix,
       "currencies": cu, "cryptos": cr, "moneymarkets": mm}
SHOW = ["name", "country", "exchange", "mic", "market", "currency", "isin", "cusip", "figi"]


def rows(df, sym, cols=None):
    c = [x for x in (cols or SHOW) if x in df.columns]
    sub = df[df["symbol"] == sym]
    return sub[c].to_dict("records") if len(sub) else []


# ---------------- CASE 1: CHAD cross-asset collision ----------------
R["CHAD"] = {}
for k, df in ALL.items():
    if "symbol" in df.columns:
        r = rows(df, "CHAD")
        if r:
            R["CHAD"][k] = r
R["CHAD_classes_present"] = sorted(R["CHAD"])
R["CHAD_is_cross_asset_collision"] = len(R["CHAD_classes_present"]) > 1
# full cross-asset collision census on the SYMBOL column
sym_sets = {k: set(df["symbol"]) for k, df in ALL.items() if "symbol" in df.columns}
ks = list(sym_sets)
pairs = {}
for i, a in enumerate(ks):
    for b in ks[i + 1:]:
        sh = sym_sets[a] & sym_sets[b]
        if sh:
            pairs[f"{a}<->{b}"] = {"n": len(sh), "examples": sorted(sh)[:8]}
R["cross_asset_symbol_collisions"] = pairs
R["cross_asset_total_pairs_with_collisions"] = len(pairs)

# ---------------- CASE 2: BRK venue contradiction ----------------
brk = {}
for k, df in ALL.items():
    if "symbol" in df.columns:
        sub = df[df["symbol"].str.upper().str.replace(".", "", regex=False)
                 .str.replace("/", "", regex=False).str.startswith("BRK")]
        if len(sub):
            c = [x for x in ["symbol", "name", "country", "exchange", "mic", "market",
                             "currency", "isin", "cusip", "figi", "shareclass_figi"]
                 if x in df.columns]
            brk[k] = sub[c].to_dict("records")
R["BRK_all_rows"] = brk
berk = [r for k in brk for r in brk[k]
        if "Berkshire" in str(r.get("name", ""))]
R["BRK_berkshire_rows"] = berk
R["BRK_berkshire_count"] = len(berk)
R["BRK_distinct_exchanges"] = sorted({r.get("exchange", "") for r in berk})
R["BRK_VENUE_CONTRADICTION"] = len(R["BRK_distinct_exchanges"]) > 1
R["BRK_isin_populated"] = [r.get("isin", "") for r in berk]
R["BRK_all_isin_empty"] = all(not str(v).strip() for v in R["BRK_isin_populated"])

# ---------------- CASE 3: MMM repeated ticker ----------------
base = eq["symbol"].str.split(".").str[0]
vc = base.value_counts()
R["MMM_rows"] = eq[base == "MMM"][[x for x in ["symbol", "name", "country", "exchange",
                                               "mic", "currency", "isin"] if x in eq.columns]].to_dict("records")
R["MMM_count"] = int(vc.get("MMM", 0))
R["MMM_distinct_names"] = sorted(set(eq.loc[base == "MMM", "name"]))
R["top_repeated_bare_tickers"] = {k: int(v) for k, v in vc.head(10).items()}
R["distinct_bare_tickers"] = int(base.nunique())
R["bare_tickers_appearing_more_than_once"] = int((vc > 1).sum())
R["total_equity_rows"] = len(eq)

# ---------------- CASE 4: ISIN -> many symbols ----------------
pop = eq[eq["isin"].str.strip() != ""]
g = pop.groupby("isin")["symbol"].nunique().sort_values(ascending=False)
R["ISIN_populated_rows"] = len(pop)
R["ISIN_populated_pct"] = round(100 * len(pop) / len(eq), 1)
R["ISIN_distinct"] = int(g.shape[0])
R["ISIN_max_fanout"] = int(g.iloc[0])
top = g.head(5)
R["ISIN_top_fanout"] = {}
for isin, n in top.items():
    sub = pop[pop["isin"] == isin]
    R["ISIN_top_fanout"][isin] = {
        "n_symbols": int(n),
        "name": sub["name"].iloc[0],
        "country": sorted(set(sub["country"]))[:4],
        "example_symbols": sub["symbol"].head(6).tolist(),
        "distinct_names": int(sub["name"].nunique()),
    }
R["ISIN_fanout_gt_1"] = int((g > 1).sum())

# ---------------- CASE 5: 'two' placeholder records ----------------
two = eq[eq["name"].str.strip().str.lower() == "two"]
c = [x for x in ["symbol", "name", "country", "exchange", "mic", "industry", "sector",
                 "currency", "isin"] if x in eq.columns]
R["TWO_rows"] = two[c].to_dict("records")
R["TWO_count"] = len(two)
R["TWO_distinct_countries"] = sorted(set(two["country"]))
R["TWO_distinct_industries"] = sorted(set(two["industry"])) if "industry" in two else []
R["TWO_symbol_suffixes"] = sorted({s.split(".")[-1] for s in two["symbol"] if "." in s})
# also check 'two' across all classes
R["TWO_other_classes"] = {k: int((df["name"].str.strip().str.lower() == "two").sum())
                          for k, df in ALL.items() if "name" in df.columns
                          and int((df["name"].str.strip().str.lower() == "two").sum()) > 0}
# whitespace / placeholder census (context for fixture realism)
R["CENSUS_names_with_trailing_ws"] = int((eq["name"] != eq["name"].str.rstrip()).sum())
R["CENSUS_symbols_with_whitespace"] = int(eq["symbol"].str.contains(r"\s", regex=True).sum())
R["CENSUS_lowercase_duplicate_names"] = int(eq["name"].str.lower().duplicated().sum())
R["CENSUS_name_counts_top"] = {k: int(v) for k, v in
                               eq["name"].value_counts().head(5).items()}

with open(OUT, "w") as f:
    json.dump(R, f, indent=2, default=str)

for k in ["CHAD_classes_present", "CHAD_is_cross_asset_collision",
          "cross_asset_total_pairs_with_collisions", "BRK_berkshire_count",
          "BRK_distinct_exchanges", "BRK_VENUE_CONTRADICTION", "BRK_all_isin_empty",
          "MMM_count", "MMM_distinct_names", "distinct_bare_tickers",
          "bare_tickers_appearing_more_than_once", "ISIN_max_fanout", "ISIN_distinct",
          "ISIN_populated_pct", "ISIN_fanout_gt_1", "TWO_count", "TWO_distinct_countries"]:
    print(f"{k:44} = {json.dumps(R.get(k), default=str)[:180]}")
print("\ncross-asset collision pairs:")
for k, v in R["cross_asset_symbol_collisions"].items():
    print(f"  {k:28} n={v['n']:<4} e.g. {v['examples'][:5]}")
print("\nISIN top fanout:")
for k, v in R["ISIN_top_fanout"].items():
    print(f"  {k} n={v['n_symbols']:<3} {v['name'][:44]:46} countries={v['country'][:3]}")
print("\nwrote", OUT)
