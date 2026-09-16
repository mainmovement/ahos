import sys, time, io, contextlib, resource, os, json, traceback
sys.path.insert(0,"/tmp/fdb_repo")   # emulate CI editable-install layout
import financedatabase as fd
print("imported from:", fd.__file__)
print("DATA_REPO     :", fd.helpers.DATA_REPO)
print("file_path     :", fd.helpers.file_path, " exists:", os.path.isdir(str(fd.helpers.file_path)))
R=[]
def rec(op,inp,exp,act,ev):
    R.append({"op":op,"input":inp,"expected":exp,"actual":act,"evidence":ev})

def cap(fn,*a,**k):
    buf=io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            t=time.perf_counter(); out=fn(*a,**k); dt=time.perf_counter()-t
        return ("OK",out,dt,buf.getvalue())
    except Exception as e:
        return ("RAISED",f"{type(e).__name__}: {str(e)[:160]}",0.0,buf.getvalue())

# ---------- C: default REMOTE load (raw.githubusercontent.com) ----------
print("\n=== TEST C: default remote load ===")
st,out,dt,so=cap(lambda: fd.Cryptos())
print(f"  fd.Cryptos() default remote -> {st}  ({dt:.2f}s)")
print(f"  detail: {out if st=='RAISED' else 'loaded rows='+str(len(out.data))}")
rec("Cryptos()","default remote URL","loads 3367 rows from GitHub raw",f"{st}: {str(out)[:120]}","runtime observation, sandbox host")

# ---------- A: pip-installed use_local_location ----------
print("\n=== TEST A: use_local_location with a site-packages install ===")
import subprocess
code=("import sys;sys.path=[p for p in sys.path if 'fdb_repo' not in p];"
      "import financedatabase as fd;print('pkg:',fd.__file__);"
      "print('file_path:',fd.helpers.file_path);"
      "import os;print('exists:',os.path.isdir(str(fd.helpers.file_path)));"
      "try:\n fd.Cryptos(use_local_location=True);print('RESULT: LOADED')\n"
      "except Exception as e:\n print('RESULT: RAISED',type(e).__name__,str(e)[:200])")
p=subprocess.run(["/tmp/fdb_venv/bin/python","-c",code],capture_output=True,text=True,cwd="/tmp")
print("  "+p.stdout.strip().replace("\n","\n  ")); print("  stderr:",p.stderr.strip()[-300:] if p.stderr.strip() else "(none)")

# ---------- B: repo-local load (CI layout) ----------
print("\n=== TEST B: use_local_location from repo root (CI layout) ===")
t=time.perf_counter(); eq=fd.Equities(use_local_location=True); t_eq=time.perf_counter()-t
t=time.perf_counter(); cr=fd.Cryptos(use_local_location=True); t_cr=time.perf_counter()-t
print(f"  Equities loaded rows={len(eq.data)} cols={len(eq.data.columns)} in {t_eq:.2f}s")
print(f"  Cryptos  loaded rows={len(cr.data)} in {t_cr:.2f}s")
rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0
print(f"  peak RSS after both loads: {rss:.1f} MiB")
print(f"  dtypes: {dict((str(k),int(v)) for k,v in eq.data.dtypes.value_counts().items())}")
rec("Equities(use_local_location=True)","repo-root cwd","loads local bz2",f"OK rows={len(eq.data)} in {t_eq:.2f}s","runtime observation")

# ---------- select() ----------
print("\n=== select() truth table ===")
for label,kw,exp in [
  ("country='Netherlands'",dict(country="Netherlands"),"exact, case-insensitive"),
  ("country='netherlands' (lower)",dict(country="netherlands"),"should still match (code lowercases)"),
  ("country='Netherland' (typo)",dict(country="Netherland"),"ValueError (validated against options)"),
  ("sector='Energy'",dict(sector="Energy"),"exact match on GICS sector"),
  ("sector='ener'",dict(sector="ener"),"ValueError? (no substring support)"),
  ("country+sector (AND)",dict(country="United States",sector="Energy"),"AND semantics"),
  ("country list",dict(country=["United States","Canada"]),"OR within param"),
  ("market_cap='Mega Cap'",dict(market_cap="Mega Cap"),"bucket label filter"),
  ("only_primary_listing=True",dict(country="China",only_primary_listing=True),"drops dotted symbols"),
  ("exclude_delisted=False",dict(country="United States",exclude_delisted=False),"includes delisted"),
  ("exchange='NMS'",dict(exchange="NMS"),"filter"),
  ("mic='XNAS'",dict(mic="XNAS"),"filter"),
  ("no args",dict(),"returns ALL rows (minus delisted)"),
]:
    st,out,dt,so=cap(lambda: eq.select(**kw))
    if st=="OK":
        act=f"OK rows={len(out)} in {dt:.3f}s"
        if so.strip(): act+=f" | stdout='{so.strip()[:90]}'"
    else: act=f"{out}"
    print(f"  {label:38} -> {act}")
    rec("select",label,exp,act,"source Equities.py:23-222 + runtime")

print("\n=== only_primary_listing vs Chinese primary listings ===")
st,allc,_,_=cap(lambda: eq.select(country="China",exclude_delisted=False))
st,pri,_,so=cap(lambda: eq.select(country="China",only_primary_listing=True,exclude_delisted=False))
print(f"  China all={len(allc)}  only_primary_listing={len(pri)}  dropped={len(allc)-len(pri)}")
print(f"  000002.SZ present in all: {'000002.SZ' in allc.index}   in primary-only: {'000002.SZ' in pri.index}")
print(f"  stdout: {so.strip()[:120]}")
rec("select(only_primary_listing=True)","country=China","keeps primary listings",
    f"dropped {len(allc)-len(pri)}/{len(allc)}; 000002.SZ kept={'000002.SZ' in pri.index}",
    "runtime; heuristic at Equities.py:208-220 uses index.str.contains(r'\\.')")

print("\n=== exclude_delisted default behaviour ===")
print("  default select() rows:", len(eq.select()))
print("  exclude_delisted=False rows:", len(eq.select(exclude_delisted=False)))
print("  delisted True count in data:", int(eq.data['delisted'].sum()))

# ---------- search() ----------
print("\n=== search() truth table ===")
for label,kw,exp in [
  ("name='Apple'",dict(name="Apple"),"substring, case-insensitive"),
  ("name='APPLE' case_sensitive=True",dict(name="APPLE",case_sensitive=True),"no matches"),
  ("name='APPLE' case_sensitive='True'",dict(name="APPLE",case_sensitive="True"),"treated True (string in list)"),
  ("name='APPLE' case_sensitive='true'",dict(name="APPLE",case_sensitive="true"),"-> False! ('true' not in [True,'True'])"),
  ("name='APPLE' case_sensitive=1",dict(name="APPLE",case_sensitive=1),"-> False! (1 not in [True,'True'])"),
  ("symbol='TSLA' (DOCSTRING EXAMPLE)",dict(symbol="TSLA"),"docstring says works; symbol is the INDEX not a column"),
  ("nonexistent_column='x'",dict(nonexistent_column="x"),"prints warning, returns UNFILTERED (fail-open)"),
  ("industry=['Software']",dict(industry=["Software"]),"list -> SUBSTRING any() semantics"),
  ("sector=['Energy']",dict(sector=["Energy"]),"list -> substring"),
  ("name='AT&T' (regex '&')",dict(name="AT&T"),"regex ok"),
  ("name='C++' (invalid regex)",dict(name="C++"),"regex error?"),
  ("name='(unclosed' (invalid regex)",dict(name="(unclosed"),"regex error expected"),
  ("index='BTC'",dict(index="BTC"),"regex on index"),
  ("index=['AAVE-USD','ETH-USD']",dict(index=["AAVE-USD","ETH-USD"]),"exact isin on index"),
  ("exclude_delisted=True",dict(exclude_delisted=True),"filters delisted"),
  ("only_primary_listing=True",dict(only_primary_listing=True),"drops dotted"),
  ("two kwargs (AND)",dict(country="United States",sector="Energy"),"AND"),
]:
    st,out,dt,so=cap(lambda: eq.search(**kw))
    if st=="OK":
        act=f"OK rows={len(out)} in {dt:.3f}s"
        if so.strip(): act+=f" | stdout='{so.strip()[:70]}'"
    else: act=f"{out}"
    print(f"  {label:44} -> {act}")
    rec("search",label,exp,act,"source helpers.py:81-155 + runtime")

print("\n=== search() determinism / idempotence ===")
a=eq.search(country="United States",sector="Energy"); b=eq.search(country="United States",sector="Energy")
print("  identical index:", a.index.equals(b.index), " identical values:", a.equals(b))
print("  ordering: is result sorted?", list(a.index[:5]))
print("  data.order == source order:", list(eq.data.index[:3]))
print("  mutating returned frame does not affect source? ")
a2=eq.search(country="United States"); n0=len(eq.data); a2.drop(a2.index[:5],inplace=True)
print(f"    source rows before={n0} after={len(eq.data)}  returned rows after={len(a2)}")
rec("search determinism","same query twice","identical results",f"index equal={a.index.equals(b.index)}","runtime")

# ---------- show_options ----------
print("\n=== show_options ===")
st,out,dt,so=cap(lambda: eq.show_options())
print(f"  Equities().show_options() -> {st} keys={list(out.keys()) if st=='OK' and isinstance(out,dict) else out}")
st,o2,dt2,so2=cap(lambda: eq.show_options(selection="country"))
print(f"  show_options(selection='country') -> {st} n={len(o2) if st=='OK' else o2} in {dt2:.3f}s sample={list(o2[:4]) if st=='OK' else ''}")
st,o3,_,_=cap(lambda: eq.show_options(selection="bogus"))
print(f"  show_options(selection='bogus') -> {st} {str(o3)[:90]}")
st,o4,dt4,so4=cap(lambda: fd.show_options("equities",use_local_location=True))
print(f"  fd.show_options('equities',use_local_location=True) -> {st} in {dt4:.2f}s keys={list(o4.keys()) if st=='OK' else str(o4)[:120]}")
st,o5,_,_=cap(lambda: fd.show_options("bogus"))
print(f"  fd.show_options('bogus') -> {st} {str(o5)[:80]}")
st,o6,_,_=cap(lambda: fd.show_options(None))
print(f"  fd.show_options(None) -> {st} {str(o6)[:80]}")
rec("show_options","selection='country'","ndarray of unique countries",f"{st} n={len(o2) if st=='OK' else '-'}","Equities.py:224-316 + runtime")
rec("fd.show_options","'equities' local","dict of column->options",f"{st} in {dt4:.2f}s","helpers.py:280-358 + runtime")

# ---------- Cryptos select ----------
print("\n=== Cryptos.select() — the SOL identity trap ===")
for t in ["SOL","SOL1","BTC","ETH","sol","Metadium","META"]:
    st,out,_,_=cap(lambda: cr.select(cryptocurrency=t))
    print(f"  select(cryptocurrency={t!r}) -> {st} " + (f"rows={len(out)} names={out['name'].unique()[:2].tolist()}" if st=="OK" else str(out)[:100]))
    rec("Cryptos.select",f"cryptocurrency={t!r}","token filter",f"{st} "+(f"rows={len(out)}" if st=="OK" else str(out)[:90]),"Cryptos.py:27-90 + runtime")

# ---------- performance ----------
print("\n=== PERFORMANCE (isolated venv, container) ===")
import pandas as pd
def bench_load(fn):
    t=time.perf_counter(); d=pd.read_csv("/tmp/fdb_repo/compression/"+fn,compression="bz2",index_col=0); return time.perf_counter()-t, len(d)
for f in ["cryptos.bz2","currencies.bz2","moneymarkets.bz2","indices.bz2","etfs.bz2","funds.bz2","equities.bz2"]:
    dt,n=bench_load(f); sz=os.path.getsize("/tmp/fdb_repo/compression/"+f)
    print(f"  {f:18} {sz/1e6:7.2f} MB  rows={n:>7}  read+decompress={dt:6.2f}s")
print(f"  peak RSS at end: {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024.0:.1f} MiB")
mem=eq.data.memory_usage(deep=True).sum()/1e6
print(f"  Equities DataFrame in-memory (deep): {mem:.1f} MB  ({mem/ (os.path.getsize('/tmp/fdb_repo/compression/equities.bz2')/1e6):.1f}x the bz2 size)")
ts=[]
for _ in range(20):
    t=time.perf_counter(); eq.select(country="United States",sector="Energy"); ts.append(time.perf_counter()-t)
print(f"  select(country,sector) x20: min={min(ts)*1000:.1f}ms median={sorted(ts)[10]*1000:.1f}ms max={max(ts)*1000:.1f}ms")
ts=[]
for _ in range(10):
    t=time.perf_counter(); eq.search(name="Apple"); ts.append(time.perf_counter()-t)
print(f"  search(name='Apple') x10: min={min(ts)*1000:.1f}ms median={sorted(ts)[5]*1000:.1f}ms max={max(ts)*1000:.1f}ms")
t=time.perf_counter(); eq.show_options(selection="country"); print(f"  show_options(selection='country'): {(time.perf_counter()-t)*1000:.1f}ms")
t=time.perf_counter(); eq.show_options(); print(f"  show_options() all columns: {(time.perf_counter()-t)*1000:.1f}ms")
t=time.perf_counter(); eq.select(); print(f"  select() no-args full copy: {(time.perf_counter()-t)*1000:.1f}ms")
json.dump(R,open("/tmp/fdb_lab/query_truth_table.json","w"),indent=1,default=str)
print("\nwrote /tmp/fdb_lab/query_truth_table.json")
