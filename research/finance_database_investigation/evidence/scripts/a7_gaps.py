import sys, os, time, io, contextlib, re
sys.path.insert(0,"/tmp/fdb_repo")
import pandas as pd, financedatabase as fd
eq=fd.Equities(use_local_location=True); cr=fd.Cryptos(use_local_location=True)

print("=== 1. C++ regex anomaly ===")
try: re.compile("C++"); print("  re.compile('C++') OK")
except Exception as e: print("  re.compile('C++') ->", type(e).__name__, e)
s=pd.Series(["C++","CC","C","AC+","x"])
print("  pandas str.contains('C++') ->", s.str.contains("C++",na=False).tolist())
r=eq.search(name="C++"); print(f"  eq.search(name='C++') rows={len(r)}  (total {len(eq.data)})")
print("  sample names:", r['name'].head(5).tolist())
print("  -> hypothesis: matches literal 'C' then quantifier collapse; check names all contain 'C':",
      bool(r['name'].astype(str).str.contains('C',regex=False).all()))

print("\n=== 2. search() vs select() delisted default divergence ===")
a=eq.select(sector="Energy"); b=eq.search(sector="Energy"); c=eq.search(sector="Energy",exclude_delisted=True)
print(f"  select(sector='Energy')            rows={len(a)}")
print(f"  search(sector='Energy')            rows={len(b)}")
print(f"  search(sector='Energy',exclude_delisted=True) rows={len(c)}")
print(f"  => search() docstring says exclude_delisted 'Defaults to True' but actual default = {len(b)-len(a)} extra delisted rows")
print(f"  delisted rows in search result: {int(b['delisted'].sum())}")

print("\n=== 3. list (substring) vs scalar (exact-ish) semantics in search() ===")
for v in ["Software","Energy","Bank"]:
    ex=eq.search(industry=v); li=eq.search(industry=[v])
    print(f"  industry={v!r}: scalar-str rows={len(ex)}  list rows={len(li)}  delta={len(li)-len(ex)}")
print("  list is SUBSTRING-any(): proof -> industry=['Bank'] matches:")
print("   ", sorted(eq.search(industry=["Bank"])['industry'].unique())[:8])
print("  scalar str.contains (regex) -> industry='Bank' matches:")
print("   ", sorted(eq.search(industry="Bank")['industry'].unique())[:8])
print("  select(industry='Bank') EXACT isin -> rows=", len(eq.select(industry="Bank")))
print("   unique industries:", sorted(eq.select(industry='Bank')['industry'].unique()))

print("\n=== 4. module-level show_options (categories file) vs live data drift ===")
cat=fd.show_options("equities",use_local_location=True)
live=eq.show_options()
for k in ["country","sector","industry","exchange","mic","currency","market_cap","industry_group"]:
    cs=set(map(str,cat.get(k,[]))); ls=set(map(str,live.get(k,[])))
    print(f"  {k:15} categories_file={len(cs):>4} live_data={len(ls):>4} only_in_cat={len(cs-ls):>3} only_in_live={len(ls-cs):>3}")
    if cs-ls: print(f"      only_in_categories_file: {sorted(cs-ls)[:5]}")
    if ls-cs: print(f"      only_in_live_data: {sorted(ls-cs)[:5]}")

print("\n=== 5. only_primary_listing heuristic across asset classes ===")
for nm,obj in [("Equities",eq),("Cryptos",cr)]:
    idx=obj.data.index
    DOT=re.compile(r"\.")
    nd=int(idx.astype(str).map(lambda s: bool(DOT.search(s))).sum())
    print("  %s: dotted=%d bare=%d" % (nm, nd, len(idx)-nd))
et=fd.ETFs(use_local_location=True); ix=fd.Indices(use_local_location=True); cu=fd.Currencies(use_local_location=True)
for nm,obj in [("ETFs",et),("Indices",ix),("Currencies",cu)]:
    idx=obj.data.index
    DOT=re.compile(r"\.")
    nd=int(idx.astype(str).map(lambda s: bool(DOT.search(s))).sum())
    print("  %s: dotted=%d bare=%d" % (nm, nd, len(idx)-nd))
print("  Indices sample symbols:", list(ix.data.index[:6]))
print("  -> Indices/Currencies/Moneymarkets have NO only_primary_listing param? ",
      "only_primary_listing" in fd.Indices.select.__code__.co_varnames,
      "Currencies:", "only_primary_listing" in fd.Currencies.select.__code__.co_varnames)

print("\n=== 6. duplicate-identity probe: BRK-A vs BRK/A vs BRK-B vs BRK/B ===")
for s_ in ["BRK-A","BRK/A","BRK-B","BRK/B","BRKA.VI","BRK.AX"]:
    r=eq.data.loc[eq.data.index==s_]
    if len(r): print(f"  {s_:10} name={r['name'].iloc[0]!r} isin={r['isin'].iloc[0]!r} exchange={r['exchange'].iloc[0]!r} country={r['country'].iloc[0]!r}")
    else: print(f"  {s_:10} ABSENT")
print("\n  -> same ISIN, many symbols (one security, N listings):")
sub=eq.data[(eq.data['isin']=='US0605051046')]
print(f"     isin US0605051046 (Berkshire?) rows={len(sub)} symbols={sub.index.tolist()[:10]}")

print("\n=== 7. empty-symbol / whitespace / casing anomalies ===")
idx=eq.data.index
print("  symbols with leading/trailing space:", int((idx.astype(str)!=idx.astype(str).str.strip()).sum()))
print("  symbols with internal space:", int(idx.astype(str).str.contains(' ').sum()), idx[idx.astype(str).str.contains(' ')][:5].tolist())
print("  lowercase symbols:", int((idx.astype(str)!=idx.astype(str).str.upper()).sum()), idx[idx.astype(str)!=idx.astype(str).str.upper()][:8].tolist())
print("  names with trailing space:", int((eq.data['name'].astype(str)!=eq.data['name'].astype(str).str.rstrip()).sum()))
print("  duplicate names (case-insensitive) count:", int(eq.data['name'].astype(str).str.lower().duplicated().sum()))

print("\n=== 8. country field: 'United States' mislabels ===")
print("  rows country='United States' but exchange not US:",
      int(((eq.data['country']=='United States') & (~eq.data['exchange'].isin(['NMS','NYQ','ASE','PCX','NCM','NGM','NAS','PCX','OTC','IOB','NYQ']))).sum()))
print("  exchange codes present:", len(eq.data['exchange'].unique()), sorted(eq.data['exchange'].unique())[:25])
print("  'market' values sample:", sorted(eq.data['market'].dropna().unique())[:12])
