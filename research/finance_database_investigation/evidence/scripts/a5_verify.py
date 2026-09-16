import pandas as pd
B="/tmp/fdb_repo/compression/"
def L(f): return pd.read_csv(B+f,compression="bz2",dtype=str,keep_default_na=False)
cr=L("cryptos.bz2"); eq=L("equities.bz2"); et=L("etfs.bz2")
print("=== SOL1 / UNI3 / LUNA1 / DOT1 / COMP1 identity ===")
for t in ["SOL1","UNI3","LUNA1","DOT1","COMP1","COMP","ATOM1","BTC2","SOL"]:
    r=cr[cr['cryptocurrency']==t]
    if len(r): print(f"  '{t}': {len(r)} rows, name='{r['name'].iloc[0]}', summary='{r['summary'].iloc[0][:90]}'")
    else: print(f"  '{t}': ABSENT")
print()
print("=== CHAD cross-asset collision (equities vs etfs) ===")
print("  equities CHAD:"); print(eq[eq['symbol']=='CHAD'][['symbol','name','country','exchange','market','isin']].to_string(index=False))
print("  etfs CHAD:"); print(et[et['symbol']=='CHAD'][['symbol','name','currency','family','exchange','isin']].to_string(index=False))
print()
print("=== .VI symbols that are actually ISINs (symbol-field semantic drift) ===")
vi=eq[eq['symbol'].str.endswith('.VI')]
print(f"  .VI rows: {len(vi)}")
looks_isin=vi['symbol'].str.match(r'^(AT|DE|FR|NL|BE|CH|ES|IT|GB|US|IE|PT|SE|FI|DK|NO|PL|CZ|HU)[0-9A-Z]{10}\.VI$')
print(f"  .VI symbols matching ISIN-pattern: {int(looks_isin.sum())} of {len(vi)}")
print(vi[['symbol','name','country','isin']].head(8).to_string(index=False))
print()
print("=== symbol field format survey (equities) ===")
s=eq['symbol']
print("  with '.' suffix (secondary-listing style):", int(s.str.contains(r'\.',regex=True).sum()))
print("  bare (no dot):", int((~s.str.contains(r'\.',regex=True)).sum()))
print("  US multi-class dot tickers present? BRK.B:", eq[eq['symbol'].str.startswith('BRK')]['symbol'].tolist()[:12])
print("  BF.B style:", [x for x in s if x.startswith('BF.')][:8])
print()
print("=== rows with name == 'two' (data quality probe) ===")
print(eq[eq['name']=='two'][['symbol','name','country','exchange','industry']].head(6).to_string(index=False))
print()
print("=== currency 'ILA' vs 'ILS' anomaly (from website sample) ===")
print(eq['currency'].value_counts().head(12).to_string())
print("  ILA count:", int((eq['currency']=='ILA').sum()), " ILS count:", int((eq['currency']=='ILS').sum()))
print()
print("=== market_cap categories ===")
print(eq['market_cap'].value_counts(dropna=False).to_string())
print()
print("=== timestamp / freshness / provenance columns across all assets ===")
for n,f in [("equities","equities.bz2"),("etfs","etfs.bz2"),("funds","funds.bz2"),("indices","indices.bz2"),("currencies","currencies.bz2"),("cryptos","cryptos.bz2"),("moneymarkets","moneymarkets.bz2")]:
    cols=set(L(f).columns)
    ts=[c for c in cols if any(k in c.lower() for k in ['date','time','updated','asof','as_of','timestamp','snapshot','version','source','provider','retrieved'])]
    print(f"  {n:13} time/provenance columns: {ts if ts else 'NONE'}")
