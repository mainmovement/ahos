import pandas as pd, io, bz2
p="/tmp/fdb_repo/compression/equities.bz2"
# RELEASE 2.4.0 semantics: pd.read_csv(path, compression='bz2', index_col=0)
rel=pd.read_csv(p,compression="bz2",index_col=0)
# MAIN HEAD semantics: + keep_default_na=False, na_values=['']
head=pd.read_csv(p,compression="bz2",index_col=0,keep_default_na=False,na_values=[""])
print("=== RELEASE 2.4.0 vs MAIN HEAD read_csv semantics (same file) ===")
print(f"  release rows={len(rel)} cols={len(rel.columns)}")
print(f"  main    rows={len(head)} cols={len(head.columns)}")
print(f"  index entries that are NaN in release: {int(rel.index.isna().sum())}")
print(f"  index entries that are NaN in main   : {int(head.index.isna().sum())}")
ri=set(map(str,rel.index)); hi=set(map(str,h.head(0).index)) if False else set(map(str,head.index))
print(f"  symbols present in main but MISSING/mangled in release: {sorted(hi-ri)[:10]}")
print()
print("  --- cell-level NaN count divergence per column ---")
for c in rel.columns:
    a=int(rel[c].isna().sum()); b=int(head[c].isna().sum())
    if a!=b: print(f"    {c:16} release_NaN={a:>7}  main_NaN={b:>7}  delta={a-b:>+7}")
print()
print("  --- is the ticker 'NA' (Nano Labs) recoverable under each? ---")
print("    release: 'NA' in index ->", 'NA' in rel.index, " | NaN count in index ->", int(rel.index.isna().sum()))
print("    main   : 'NA' in index ->", 'NA' in head.index)
try:
    print("    release row for 'NA':", rel.loc['NA'][['name','country','exchange']].to_dict())
except Exception as e: print("    release .loc['NA'] ->", type(e).__name__, str(e)[:80])
print()
print("  --- Equities.select() under RELEASE semantics: what happens to the NaN symbol? ---")
import sys; sys.path.insert(0,"/tmp/fdb_repo")
print("    (main-HEAD helpers.py in use here; simulating release by monkeypatching)")
