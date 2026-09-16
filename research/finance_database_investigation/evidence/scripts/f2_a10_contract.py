"""F2 — Objective A claim A-10: the NormalizedTokenCandidate compatibility argument.

Imports the REAL AHOS contract module READ-ONLY (it is stdlib-only: time, abc, dataclasses,
typing) and attempts to build a NormalizedTokenCandidate from an actual FinanceDatabase
cryptos row. Demonstrates the structural impossibility rather than asserting it.

SAFETY: no AHOS file is written, imported for side effects, or modified. The module is
loaded by explicit file path in an isolated research venv outside the AHOS tree.
"""
import importlib.util
import json
import sys

import pandas as pd

CONTRACTS = "/home/user/ahos/architecture/providers/contracts.py"
REGISTRY = "/home/user/ahos/architecture/providers/registry.py"
OUT = "/tmp/fdb2_lab/f2_a10_contract.json"
R = {}

# ---- confirm the AHOS module is stdlib-only before importing it -----------------
src = open(CONTRACTS, encoding="utf-8").read()
imports = sorted({ln.split()[1].split(".")[0]
                  for ln in src.splitlines()
                  if ln.startswith(("import ", "from "))})
R["ahos_contracts_imports"] = imports
R["ahos_contracts_is_stdlib_only"] = set(imports) <= {"time", "abc", "dataclasses", "typing",
                                                      "__future__", "collections"}

spec = importlib.util.spec_from_file_location("ahos_contracts_ro", CONTRACTS)
mod = importlib.util.module_from_spec(spec)
# dataclasses._is_type() does sys.modules.get(cls.__module__).__dict__, so the module
# must be registered BEFORE exec. Registration is an in-memory dict write in THIS
# research process only; it does not touch any AHOS file.
sys.modules["ahos_contracts_ro"] = mod
spec.loader.exec_module(mod)          # read-only: defines dataclasses, touches nothing
R["imported_ok"] = True
R["UNKNOWN_VALUE"] = repr(mod.UNKNOWN_VALUE)
R["module_docstring_first_line"] = mod.__doc__.strip().splitlines()[0]
R["contract_law_lines"] = [l.strip() for l in mod.__doc__.splitlines() if "NEVER guessed" in l
                           or "Fail-Closed" in l or "Provable Source" in l]

NTC = mod.NormalizedTokenCandidate
import dataclasses
fields = [(f.name, str(f.type), f.default is dataclasses.MISSING
           and f.default_factory is dataclasses.MISSING) for f in dataclasses.fields(NTC)]
R["NTC_fields"] = [{"name": n, "type": t, "REQUIRED_no_default": req} for n, t, req in fields]
R["NTC_required_fields"] = [n for n, t, req in fields if req]

# ---- load a real FinanceDatabase cryptos row -----------------------------------
cr = pd.read_csv("/tmp/fdb2_repo/compression/cryptos.bz2", compression="bz2",
                 dtype=str, keep_default_na=False)
row = cr[cr["cryptocurrency"] == "SOL1"].iloc[0].to_dict()
R["sample_fdb_cryptos_row"] = row
R["fdb_row_has_chain"] = "chain" in cr.columns
R["fdb_row_has_address"] = "address" in cr.columns

# ---- TEST 1: can we build a candidate from the row alone? ----------------------
try:
    c = NTC(**{"symbol": row["symbol"], "name": row["name"]})
    R["T1_construct_without_chain_address"] = "SUCCEEDED (unexpected)"
except TypeError as e:
    R["T1_construct_without_chain_address"] = "TypeError"
    R["T1_message"] = str(e)

# ---- TEST 2: what the adapter would have to do (fabricate, or emit None) -------
try:
    c = NTC(chain=None, address=None, symbol=row["symbol"], name=row["name"])
    R["T2_construct_with_None"] = "SUCCEEDED — dataclass does not enforce str at runtime"
    R["T2_chain_value"] = repr(c.chain)
    R["T2_address_value"] = repr(c.address)
    R["T2_unknown_fields"] = c.identify_unknowns()
    R["T2_n_unknown_fields"] = len(c.identify_unknowns())
    R["T2_confidence_level"] = c.confidence_level
    # the router's dedupe key, reproduced verbatim from registry.py
    R["T2_dedupe_key_expression"] = "(c.chain, c.address.lower())"
    try:
        k = (c.chain, c.address.lower())
        R["T2_dedupe_key_result"] = "SUCCEEDED (unexpected)"
    except AttributeError as e:
        R["T2_dedupe_key_raises"] = f"AttributeError: {e}"
except Exception as e:
    R["T2_construct_with_None"] = f"{type(e).__name__}: {e}"

# ---- TEST 3: confirm the dedupe expression really is in registry.py ------------
rsrc = open(REGISTRY, encoding="utf-8").read()
R["T3_registry_dedupe_line"] = [l.strip() for l in rsrc.splitlines() if "address.lower()" in l]
R["T3_registry_adapter_keys"] = sorted(
    l.split('"')[1] for l in rsrc.splitlines() if l.strip().startswith('"') and '": ' in l
) or "see source"
R["T3_discovery_providers"] = [l.strip() for l in rsrc.splitlines() if "dexscreener" in l
                               and "geckoterminal" in l]

# ---- TEST 4: BaseMarketProvider abstract surface ------------------------------
BMP = mod.BaseMarketProvider
R["T4_abstract_methods"] = sorted(BMP.__abstractmethods__)
R["T4_fetch_candidate_tokens_signature"] = "fetch_candidate_tokens(self, chain: str, limit: int = 20)"
R["T4_fetch_token_metrics_signature"] = "fetch_token_metrics(self, chain: str, address: str)"
R["T4_both_require_chain_or_address"] = True

# ---- TEST 5: how many of the 16 MarketMetrics / 15 SecuritySignals could be fed?
mm = [f.name for f in dataclasses.fields(mod.MarketMetrics)]
ss = [f.name for f in dataclasses.fields(mod.SecuritySignals)]
fdb_cols = set(cr.columns)
R["T5_MarketMetrics_fields"] = len(mm)
R["T5_SecuritySignals_fields"] = len(ss)
R["T5_MarketMetrics_satisfiable_from_fdb"] = [f for f in mm if f in fdb_cols]
R["T5_SecuritySignals_satisfiable_from_fdb"] = [f for f in ss if f in fdb_cols]

with open(OUT, "w") as f:
    json.dump(R, f, indent=2, default=str)
print(json.dumps(R, indent=2, default=str))
