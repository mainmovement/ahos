import pandas as pd, numpy as np, bz2, io, json, sys
BASE="/tmp/fdb_repo/compression/"
ASSETS={"equities":"equities.bz2","etfs":"etfs.bz2","funds":"funds.bz2","indices":"indices.bz2",
        "currencies":"currencies.bz2","cryptos":"cryptos.bz2","moneymarkets":"moneymarkets.bz2"}
out={}
for name,fn in ASSETS.items():
    df=pd.read_csv(BASE+fn, compression="bz2", dtype=str, keep_default_na=False)
    sym=df.columns[0]
    print("="*78); print(f"{name.upper()}  file={fn}")
    print(f"  rows={len(df)}  cols={len(df.columns)}  index_col_name='{sym}'")
    print(f"  columns: {list(df.columns)}")
    print(f"  pandas dtypes (as read with dtype=str): {sorted(set(map(str,df.dtypes)))}")
    # emptiness: treat '' and 'nan'/'NaN' textual as empty
    empt={}
    for c in df.columns:
        s=df[c].astype(str).str.strip()
        e=int(((s=="")|(s.str.lower().isin(["nan","none","null"]))).sum())
        empt[c]=e
    print("  EMPTY-VALUE COUNTS per column (pct):")
    for c,e in empt.items():
        print(f"     {c:16} {e:>8}  {100*e/len(df):6.2f}%")
    # duplicates on symbol
    d=df[sym]
    dup=int(d.duplicated().sum())
    print(f"  DUPLICATE '{sym}' values: {dup}   unique={d.nunique()}")
    if dup:
        vc=d.value_counts(); ex=vc[vc>1].head(6)
        print(f"     examples of duplicated symbols: {dict(ex)}")
    out[name]={"rows":int(len(df)),"cols":list(df.columns),"dup_symbols":dup,"empty":empt}
json.dump(out, open("/tmp/fdb_lab/schema_audit.json","w"), indent=1, default=str)
