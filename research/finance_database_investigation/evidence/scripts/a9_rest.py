import sys, os, re, signal
sys.path.insert(0,"/tmp/fdb_repo")
import pandas as pd, financedatabase as fd
eq=fd.Equities(use_local_location=True); cr=fd.Cryptos(use_local_location=True)
et=fd.ETFs(use_local_location=True); ix=fd.Indices(use_local_location=True)
cu=fd.Currencies(use_local_location=True); fu=fd.Funds(use_local_location=True)
mm=fd.Moneymarkets(use_local_location=True)
DOT=re.compile(r"\.")
def dotted(idx): return sum(1 for s in idx.astype(str) if DOT.search(s))

print("=== 4. categories-file vs live-data drift ===")
cat=fd.show_options("equities",use_local_location=True); live=eq.show_options()
for k in ["country","sector","industry","exchange","mic","currency","market_cap","industry_group"]:
    cs=set(map(str,cat.get(k,[]))); ls=set(map(str,live.get(k,[])))
    print("  %-15s categories_file=%4d live_data=%4d only_in_cat=%3d only_in_live=%3d"%(k,len(cs),len(ls),len(cs-ls),len(ls-cs)))
    if cs-ls: print("      only_in_categories_file:",sorted(cs-ls)[:6])
    if ls-cs: print("      only_in_live_data:",sorted(ls-cs)[:6])
ccat=fd.show_options("cryptos",use_local_location=True); clive=cr.show_options()
for k in ["cryptocurrency","currency"]:
    cs=set(map(str,ccat.get(k,[]))); ls=set(map(str,clive.get(k,[])))
    print("  cryptos %-15s categories_file=%4d live_data=%4d only_in_cat=%3d only_in_live=%3d"%(k,len(cs),len(ls),len(cs-ls),len(ls-cs)))
    if cs-ls: print("      only_in_categories_file:",sorted(cs-ls)[:6])
    if ls-cs: print("      only_in_live_data:",sorted(ls-cs)[:6])

print("\n=== 5. only_primary_listing heuristic coverage per asset class ===")
for nm,obj in [("Equities",eq),("ETFs",et),("Funds",fu),("Indices",ix),("Currencies",cu),("Cryptos",cr),("Moneymarkets",mm)]:
    n=dotted(obj.data.index)
    has=("only_primary_listing" in obj.select.__code__.co_varnames)
    print("  %-13s rows=%6d dotted=%6d (%5.1f%%) select(has only_primary_listing)=%s"%(nm,len(obj.data),n,100*n/len(obj.data),has))
print("  Indices sample symbols:",list(ix.data.index[:8]))
print("  Currencies sample:",list(cu.data.index[:5]))
print("  -> for Indices/Currencies/Moneymarkets the param is absent; for Equities/ETFs/Funds dotted = non-US local codes")

print("\n=== 6. duplicate-identity probe (Berkshire) ===")
for s_ in ["BRK-A","BRK/A","BRK-B","BRK/B","BRKA.VI","BRK.AX","BRK.L"]:
    r=eq.data.loc[eq.data.index==s_]
    print(("  %-9s name=%-45r isin=%-14r exchange=%-5r country=%r"%(s_,r['name'].iloc[0],r['isin'].iloc[0],r['exchange'].iloc[0],r['country'].iloc[0])) if len(r) else "  %-9s ABSENT"%s_)
print("  rows sharing isin US0605051046:",len(eq.data[eq.data['isin']=='US0605051046']), eq.data[eq.data['isin']=='US0605051046'].index.tolist()[:8])

print("\n=== 7. symbol/name hygiene ===")
idx=eq.data.index.astype(str)
print("  symbols w/ leading-trailing space:",int((idx!=idx.str.strip()).sum()))
print("  symbols w/ internal space:",int(idx.str.contains(" ").sum()), idx[idx.str.contains(" ")][:6].tolist())
print("  symbols not all-uppercase:",int((idx!=idx.str.upper()).sum()), idx[idx!=idx.str.upper()][:8].tolist())
nm=eq.data['name'].astype(str)
print("  names w/ trailing space:",int((nm!=nm.str.rstrip()).sum()))
print("  duplicated lowercase names:",int(nm.str.lower().duplicated().sum()))
print("  name == 'two':",int((nm=='two').sum()),"  name=='' :",int((nm.str.strip()=='').sum()))

print("\n=== 8. country/exchange/market consistency ===")
us=eq.data[eq.data['country']=='United States']
print("  country='United States' rows:",len(us))
print("  their exchange codes:",us['exchange'].value_counts().head(10).to_dict())
nonus_ex=us[~us['exchange'].isin(['NMS','NYQ','ASE','PCX','NCM','NGM','NAS','PK','OTC','IOB','NYQ','BTS','CBOE'])]
print("  US-country rows on non-US-plausible exchange codes:",len(nonus_ex), nonus_ex['exchange'].value_counts().head(6).to_dict())
sz=eq.data[eq.data['symbol'].str.endswith('.SZ')]
print("  .SZ (Shenzhen) rows labelled country='United States':",int((sz['country']=='United States').sum()),"of",len(sz))
print("  exchange code count:",eq.data['exchange'].nunique()," mic count:",eq.data['mic'].nunique())
e2m=eq.data[eq.data['mic'].str.strip()!=''].drop_duplicates('exchange').set_index('exchange')['mic']
print("  exchange->mic 1:1 violations:",int(eq.data[eq.data['mic'].str.strip()!=''].groupby('exchange')['mic'].nunique().gt(1).sum()))
m2e=eq.data[eq.data['mic'].str.strip()!=''].groupby('mic')['exchange'].nunique()
print("  mic->multiple exchange codes:",int(m2e.gt(1).sum()), m2e[m2e>1].head(5).to_dict())

print("\n=== 9. ReDoS / pathological regex exposure in search() ===")
class TO(Exception): pass
def h(s,f): raise TO()
signal.signal(signal.SIGALRM,h)
for pat in ["(a+)+$","(a|aa)+$","^(a+)+b$"]:
    signal.alarm(12)
    t=__import__('time').perf_counter()
    try:
        r=eq.search(name=pat); print("  pattern %-12r -> rows=%d in %.2fs"%(pat,len(r),__import__('time').perf_counter()-t))
    except TO: print("  pattern %-12r -> TIMEOUT >12s (ReDoS-susceptible)"%pat)
    except Exception as e: print("  pattern %-12r -> %s: %s"%(pat,type(e).__name__,str(e)[:70]))
    finally: signal.alarm(0)

print("\n=== 10. python version ===")
print("  running:",sys.version.split()[0])
print("  possessive-quantifier support (3.11+):", end=" ")
try: re.compile("C++"); print("YES -> search(name='C++') silently matches 'c'")
except re.error as e: print("NO ->",e)
