import sys, os, re, signal, time
sys.path.insert(0,"/tmp/fdb_repo")
import pandas as pd, financedatabase as fd
eq=fd.Equities(use_local_location=True)
d=eq.data; idx=d.index.astype(str)

print("=== 8b. country vs listing venue ===")
sz=d[idx.str.endswith('.SZ')]
print("  .SZ (Shenzhen) rows:",len(sz),"  labelled country='United States':",int((sz['country']=='United States').sum()))
print("  .SZ sample countries:",sz['country'].value_counts().head(4).to_dict())
print("  exchange->mic 1:1 violations:",int(d[d['mic'].notna()].groupby('exchange')['mic'].nunique().gt(1).sum()))
m2e=d[d['mic'].notna()].groupby('mic')['exchange'].nunique()
print("  one MIC -> several exchange codes:",int(m2e.gt(1).sum()), m2e[m2e>1].head(6).to_dict())
print("  distinct exchange codes:",d['exchange'].nunique()," distinct MICs:",d['mic'].nunique())
print("  exchange codes with EMPTY mic:",int(d[d['mic'].isna()]['exchange'].nunique()))

print("\n=== 9. ReDoS / pathological regex exposure in search() ===")
class TO(Exception): pass
def h(s,f): raise TO()
signal.signal(signal.SIGALRM,h)
for pat in ["(a+)+$","(a|a)*$","^(a+)+b$","(x+x+)+y"]:
    signal.alarm(10); t=time.perf_counter()
    try:
        r=eq.search(name=pat); print("  %-12r -> rows=%d in %.2fs"%(pat,len(r),time.perf_counter()-t))
    except TO: print("  %-12r -> TIMEOUT >10s  (catastrophic backtracking on 112,690 rows)"%pat)
    except Exception as e: print("  %-12r -> %s: %s"%(pat,type(e).__name__,str(e)[:80]))
    finally: signal.alarm(0)
print("  NOTE: search() forwards the raw string to pandas str.contains(regex=True) with no escaping (helpers.py:151-153)")

print("\n=== 10. python / regex-engine version dependence ===")
print("  running:",sys.version.split()[0])
try:
    re.compile("C++"); print("  possessive quantifiers supported (3.11+) -> search(name='C++') silently matches every name containing c/C")
    r=eq.search(name="C++"); print("     measured rows:",len(r),"of",len(d),"=",round(100*len(r)/len(d),1),"%")
except re.error as e: print("  NOT supported ->",e)
print("  pandas:",pd.__version__)

print("\n=== 11. fail-open demonstration (the AHOS-critical one) ===")
r=eq.search(typo_column="anything")
print("  eq.search(typo_column='anything') -> rows=%d (== full universe %d): %s"%(len(r),len(d),len(r)==len(d)))
r2=eq.search(symbl="AAPL")
print("  eq.search(symbl='AAPL')  [misspelled 'symbol'] -> rows=%d"%len(r2))
r3=eq.search(index="AAPL")
print("  eq.search(index='AAPL')  [correct param]       -> rows=%d  %s"%(len(r3),r3.index.tolist()[:5]))
print("  => an operator typo returns the ENTIRE universe with only a stdout print. No exception, no status field.")

print("\n=== 12. is AAPL even present? ===")
print("  index entries containing 'AAPL':",idx[idx.str.contains('AAPL')][:12].tolist())
print("  name contains 'Apple Inc':",d[d['name'].astype(str).str.contains('Apple Inc',case=False,na=False)].index.tolist()[:8])

print("\n=== 13. memory / footprint summary ===")
import resource
print("  peak RSS: %.1f MiB"%(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024))
print("  equities deep memory: %.1f MB"%(d.memory_usage(deep=True).sum()/1e6))
print("  object/str dtype cols:",int((d.dtypes==object).sum()),"bool cols:",int((d.dtypes==bool).sum()))
