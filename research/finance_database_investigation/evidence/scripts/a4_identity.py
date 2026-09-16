import pandas as pd
B="/tmp/fdb_repo/compression/"
def L(f): return pd.read_csv(B+f,compression="bz2",dtype=str,keep_default_na=False)
cr=L("cryptos.bz2"); eq=L("equities.bz2"); et=L("etfs.bz2"); fu=L("funds.bz2"); ix=L("indices.bz2"); cu=L("currencies.bz2"); mm=L("moneymarkets.bz2")

print("=== 1. BTC / Bitcoin probe (verify headline claim) ===")
print("rows with name containing 'Bitcoin':")
print(cr[cr['name'].str.contains('Bitcoin',case=False)][['symbol','name','cryptocurrency','currency']].head(25).to_string(index=False))
print()
print("=== 2. Yahoo-style numeric-suffix token tickers (identity mangling) ===")
suffixed=sorted([t for t in cr['cryptocurrency'].unique() if t and t[-1].isdigit() and not t[:-1].isdigit()])
print(f"count={len(suffixed)}: {suffixed}")
for t in suffixed[:12]:
    nm=cr.loc[cr['cryptocurrency']==t,'name'].iloc[0]
    print(f"   '{t}' -> name '{nm}'")
print()
print("=== 3. CROSS-ASSET SYMBOL COLLISIONS (full symbol) ===")
sets={"equities":set(eq['symbol']),"etfs":set(et['symbol']),"funds":set(fu['symbol']),
      "indices":set(ix['symbol']),"currencies":set(cu['symbol']),"cryptos":set(cr['symbol']),
      "moneymarkets":set(mm['symbol'])}
ks=list(sets)
for i,a in enumerate(ks):
    for b in ks[i+1:]:
        sh=sets[a]&sets[b]
        if sh: print(f"   {a} <-> {b}: {len(sh)} collisions, e.g. {sorted(sh)[:6]}")
print("   (none printed above => no full-symbol collisions across asset classes)")
print()
print("=== 4. CRYPTO TOKEN TICKER vs EQUITY SYMBOL collisions (the real AHOS risk) ===")
toks={t for t in cr['cryptocurrency'].unique() if t}
coll=sorted(toks & sets["equities"])
print(f"   {len(coll)} of {len(toks)} crypto token tickers are ALSO equity symbols ({100*len(coll)/len(toks):.1f}%)")
print(f"   examples: {coll[:40]}")
print()
print("   -- worked example: token ticker 'META' --")
print("   crypto rows:", cr[cr['cryptocurrency']=='META'][['symbol','name']].to_string(index=False))
print("   equity rows:", eq[eq['symbol']=='META'][['symbol','name','country','exchange']].to_string(index=False))
print()
print("   -- worked example: token ticker 'GO' --")
print("   crypto rows:", cr[cr['cryptocurrency']=='GO'][['symbol','name']].head(3).to_string(index=False))
print("   equity rows:", eq[eq['symbol']=='GO'][['symbol','name','country','exchange']].to_string(index=False))
print()
print("=== 5. SAME-SYMBOL-DIFFERENT-INSTRUMENT within equities (multi-listing) ===")
# strip exchange suffix to find the same underlying listed in several places
base=eq['symbol'].str.split('.').str[0]
vc=base.value_counts()
multi=vc[vc>1]
print(f"   distinct bare tickers: {base.nunique()}   bare tickers appearing >1 time: {len(multi)}")
print(f"   top duplicated bare tickers: {dict(multi.head(8))}")
ex=multi.index[0]
print(f"   example '{ex}' listings:")
print(eq[base==ex][['symbol','name','country','exchange','mic','market','currency','isin']].head(8).to_string(index=False))
print()
print("=== 6. identifier uniqueness WITHIN equities (isin/cusip/figi) ===")
for c in ['isin','cusip','figi','composite_figi','shareclass_figi']:
    s=eq[c][eq[c].str.strip()!='']
    print(f"   {c}: populated={len(s)} ({100*len(s)/len(eq):.1f}%) unique={s.nunique()} duplicated_values={int(s.duplicated().sum())}")
    if s.duplicated().sum():
        d=s[s.duplicated(keep=False)].value_counts().head(3)
        print(f"      most duplicated {c}: {dict(d)}")
print()
print("=== 7. one ISIN -> multiple symbols (multi-listing of one security) ===")
s=eq[eq['isin'].str.strip()!='']
g=s.groupby('isin')['symbol'].nunique().sort_values(ascending=False)
print("   top ISINs by number of distinct symbols:"); print(g.head(6).to_string())
top=g.index[0]
print(f"   ISIN {top} -> symbols:")
print(s[s['isin']==top][['symbol','name','country','exchange','market']].head(10).to_string(index=False))
print()
print("=== 8. one company (name) -> many symbols ===")
nm=eq['name'][eq['name'].str.strip()!=''].value_counts()
print("   top repeated company names:"); print(nm.head(6).to_string())
print()
print("=== 9. delisted distribution (equities) ===")
print(eq['delisted'].value_counts().to_string())
print()
print("=== 10. exchange/market mislabel evidence (workflow line 175-176) ===")
print("   rows exchange=='ASE':", int((eq['exchange']=='ASE').sum()))
print(eq[eq['exchange']=='ASE']['market'].value_counts().to_string())
print("   rows exchange=='NMS':", int((eq['exchange']=='NMS').sum()))
print(eq[eq['exchange']=='NMS']['market'].value_counts().to_string())
print()
print("=== 11. 'new ticker' signature (empty isin+cusip+figi+summary) ===")
sig=eq[(eq['isin'].str.strip()=='')&(eq['cusip'].str.strip()=='')&(eq['figi'].str.strip()=='')&(eq['summary'].str.strip()=='')]
print(f"   rows with ALL of isin,cusip,figi,summary empty: {len(sig)} ({100*len(sig)/len(eq):.1f}%)")
print("   their exchange distribution:"); print(sig['exchange'].value_counts().head(6).to_string())
print("   their market_cap distribution:"); print(sig['market_cap'].value_counts().head(8).to_string())
