"""F1 — Objective A: re-verification of the decisive crypto verdict.

Re-runs the ORIGINAL archived probe lists (evidence/scripts/a2_crypto.py, a3_crypto2.py,
a4_identity.py) verbatim against a freshly rebuilt isolated environment pinned to the
same commit. Emits machine-readable JSON so the result can be diffed against the
original report rather than merely restated.

Read-only. Touches neither the upstream repository nor AHOS.
"""
import json
import re
import sys

import pandas as pd

B = "/tmp/fdb2_repo/compression/"
OUT = "/tmp/fdb2_lab/f1_objective_a.json"
PIN = "a174c97d3bba96fc1a82b2e1068fb3ec5e02e634"

R = {"pinned_commit": PIN, "pandas": pd.__version__, "python": sys.version.split()[0]}


def L(f, **kw):
    """main-HEAD read semantics, matching the archived scripts exactly."""
    return pd.read_csv(B + f, compression="bz2", dtype=str, keep_default_na=False, **kw)


# ---------------------------------------------------------------- CLAIM A-1 / A-2
cr = L("cryptos.bz2")
R["A1_columns_exact"] = list(cr.columns)
R["A1_column_count"] = len(cr.columns)
R["A1_rows"] = len(cr)
R["A1_claim_was"] = ["symbol", "name", "cryptocurrency", "currency", "summary", "exchange", "website"]
R["A1_MATCHES_REPORT"] = R["A1_columns_exact"] == R["A1_claim_was"]

REQUIRED = ["chain", "network", "contract", "address", "contract_address", "platform",
            "token_id", "decimals", "launch_date", "first_seen", "market_cap",
            "price", "volume", "liquidity"]
R["A2_required_fields_present"] = {c: (c in cr.columns) for c in REQUIRED}
R["A2_absent_count"] = sum(1 for c in REQUIRED if c not in cr.columns)
R["A2_total_checked"] = len(REQUIRED)
R["A2_ALL_ABSENT"] = all(c not in cr.columns for c in REQUIRED)

# ---------------------------------------------------------------- CLAIM A-3 / A-4
toks = set(cr["cryptocurrency"])
R["A3_distinct_token_tickers"] = len(toks)
R["A3_rows_per_token"] = round(len(cr) / len(toks), 2)
R["A3_SOL_rows"] = int((cr["cryptocurrency"] == "SOL").sum())
R["A3_SOL_symbol_prefix_rows"] = int(cr["symbol"].str.startswith("SOL-").sum())
R["A3_SOL_PRESENT"] = "SOL" in toks
R["A3_BTC_rows_as_token"] = int((cr["cryptocurrency"] == "BTC").sum())
R["A3_BTC_rows_as_quote_currency"] = int((cr["currency"] == "BTC").sum())

s1 = cr[cr["cryptocurrency"] == "SOL1"]
R["A4_SOL1_rows"] = len(s1)
R["A4_SOL1_names"] = sorted(set(s1["name"]))[:5]
R["A4_SOL1_PRESENT"] = len(s1) > 0
R["A4_SOL1_example_symbols"] = s1["symbol"].head(4).tolist()

# ---------------------------------------------------------------- CLAIM A-5
# probe list copied verbatim from evidence/scripts/a2_crypto.py
probe = ["BONK", "WIF", "JUP", "PYRM", "JTO", "RAY", "ORCA", "MNGO", "POPCAT", "MEW", "BOME",
         "SLERF", "MYRO", "WEN", "TRUMP", "FARTCOIN", "PNUT", "GOAT", "ACT", "GRIFFAIN",
         "CHILLGUY", "MICHI", "RETARDIO", "NEIRO", "MOODENG", "GIGA", "SPORE", "MOCA",
         "AI16Z", "VIRTUAL", "ZEREBRO", "AIXBT", "GRASS", "HYPE", "SUI", "APT", "SEI", "TIA",
         "INJ", "ONDO", "PEPE", "SHIB", "DOGE", "XRP", "BTC", "ETH", "ADA", "AVAX", "LINK",
         "UNI", "AAVE", "MKR", "LDO", "ARB", "OP", "MATIC", "DOT", "ATOM", "NEAR", "ALGO",
         "FIL", "ICP", "QNT", "VET", "HBAR", "XLM", "ETC", "BCH", "LTC", "TRX", "XMR", "ZEC",
         "DASH"]
R["A5_probe_size"] = len(probe)
R["A5_present"] = [p for p in probe if p in toks]
R["A5_absent"] = [p for p in probe if p not in toks]
R["A5_present_count"] = len(R["A5_present"])
R["A5_absent_count"] = len(R["A5_absent"])
solana_eco = ["BONK", "WIF", "JUP", "JTO", "RAY", "ORCA", "MNGO", "POPCAT", "MEW", "BOME",
              "SLERF", "MYRO", "WEN", "PYRM"]
R["A5_solana_ecosystem_absent"] = [t for t in solana_eco if t not in toks]
R["A5_ALL_SOLANA_ECOSYSTEM_ABSENT"] = len(R["A5_solana_ecosystem_absent"]) == len(solana_eco)

# ---------------------------------------------------------------- CLAIM A-6
eq = L("equities.bz2")
eqsym = set(eq["symbol"])
coll = sorted(toks & eqsym)
R["A6_crypto_token_tickers"] = len(toks)
R["A6_equity_symbols"] = len(eqsym)
R["A6_collisions"] = len(coll)
R["A6_collision_pct"] = round(100 * len(coll) / len(toks), 1)
R["A6_examples"] = coll[:20]
meta_c = cr[cr["cryptocurrency"] == "META"][["symbol", "name"]].head(2).to_dict("records")
meta_e = eq[eq["symbol"] == "META"][["symbol", "name", "country", "exchange"]].head(2).to_dict("records")
R["A6_META_crypto"] = meta_c
R["A6_META_equity"] = meta_e
go_c = cr[cr["cryptocurrency"] == "GO"][["symbol", "name"]].head(2).to_dict("records")
go_e = eq[eq["symbol"] == "GO"][["symbol", "name", "country", "exchange"]].head(2).to_dict("records")
R["A6_GO_crypto"] = go_c
R["A6_GO_equity"] = go_e

# ---------------------------------------------------------------- CLAIM A-7
SCHEMAS = ["equities", "etfs", "funds", "indices", "currencies", "cryptos", "moneymarkets"]
pat = re.compile(r"date|time|updated|asof|timestamp|snapshot|version|source|provider|retrieved",
                 re.IGNORECASE)
ts = {}
for s in SCHEMAS:
    d = L(s + ".bz2")
    hits = [c for c in d.columns if pat.search(c)]
    ts[s] = {"rows": len(d), "cols": list(d.columns), "temporal_or_provenance_columns": hits}
R["A7_temporal_scan"] = ts
R["A7_total_temporal_columns_found"] = sum(len(v["temporal_or_provenance_columns"]) for v in ts.values())
R["A7_NO_TIMESTAMPS_ANYWHERE"] = R["A7_total_temporal_columns_found"] == 0
R["A7_total_rows_all_schemas"] = sum(v["rows"] for v in ts.values())

# provenance signal: exchange codes in cryptos
R["A7_cryptos_exchange_counts"] = cr["exchange"].value_counts().to_dict()
summ = cr["summary"].str.lower()
R["A7_chain_mentions_in_summary"] = {
    kw: int(summ.str.contains(kw, regex=False).sum())
    for kw in ["ethereum", "solana", "binance smart chain", "bnb", "polygon", "avalanche",
               "arbitrum", "base", "tron", "cardano"]
}

# ---------------------------------------------------------------- CLAIM A-9 capability matrix
caps = {
    "chain_field": "chain" in cr.columns,
    "contract_address_field": any(c in cr.columns for c in ("address", "contract_address", "contract")),
    "price_field": "price" in cr.columns,
    "volume_field": "volume" in cr.columns,
    "liquidity_field": "liquidity" in cr.columns,
    "market_cap_field": "market_cap" in cr.columns,
    "fdv_field": any("fdv" in c for c in cr.columns),
    "launch_or_first_seen": any(c in cr.columns for c in ("launch_date", "first_seen")),
    "decimals_field": "decimals" in cr.columns,
    "timestamp_field": bool(ts["cryptos"]["temporal_or_provenance_columns"]),
    "security_signal_fields": any(c in cr.columns for c in ("is_honeypot", "buy_tax", "sell_tax",
                                                           "mint_authority", "freeze_authority")),
    "solana_token_present": "SOL" in toks,
    "post_2021_assets_present": any(t in toks for t in ("BONK", "WIF", "JUP", "PEPE", "ARB", "OP")),
    "automated_update_job": False,   # verified separately by workflow grep (F1b)
    "delisted_flag_for_crypto": "delisted" in cr.columns,
    "identifier_for_join": any(c in cr.columns for c in ("isin", "cusip", "figi")),
}
R["A9_capability_matrix"] = caps
R["A9_capabilities_satisfied"] = sum(1 for v in caps.values() if v)
R["A9_capabilities_total"] = len(caps)
R["A9_ALL_NEGATIVE"] = R["A9_capabilities_satisfied"] == 0

with open(OUT, "w") as f:
    json.dump(R, f, indent=2)

print(json.dumps({k: v for k, v in R.items()
                  if k.endswith(("MATCHES_REPORT", "_ABSENT", "_PRESENT", "_ANYWHERE",
                                 "_NEGATIVE")) or k.startswith(("A1_", "A3_", "A4_", "A5_p",
                                                                "A5_a", "A6_c", "A9_cap"))},
                 indent=2)[:4000])
print("\nwrote", OUT)
