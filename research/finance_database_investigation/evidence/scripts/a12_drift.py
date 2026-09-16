import sys; sys.path.insert(0,"/tmp/fdb_repo")
import financedatabase as fd
eq=fd.Equities(use_local_location=True); d=eq.data
cat=fd.show_options("equities",use_local_location=True)
phantom=sorted(set(map(str,cat['country']))-set(map(str,eq.show_options()['country'])))
print("phantom countries advertised by fd.show_options('equities'):",phantom)
for c in phantom:
    sub=d[d['country']==c]
    print(f"  '{c}': rows={len(sub)}  delisted=True rows={int(sub['delisted'].sum())}  symbols={sub.index.tolist()[:5]}")
print()
print("=> MECHANISM: fd.show_options() derives from ALL database rows (incl. delisted);")
print("   Equities.show_options()/select() derive from rows AFTER exclude_delisted=True.")
print()
print("=== PROOF: select() rejects a value that show_options() advertises ===")
for c in phantom[:3]:
    try:
        r=eq.select(country=c); print(f"  select(country={c!r}) -> rows={len(r)}")
    except ValueError as e:
        print(f"  select(country={c!r}) -> ValueError: {str(e)[:95]}")
print()
print("=== same test with exclude_delisted=False ===")
for c in phantom[:3]:
    try:
        r=eq.select(country=c,exclude_delisted=False); print(f"  select(country={c!r}, exclude_delisted=False) -> rows={len(r)}")
    except ValueError as e: print(f"  -> ValueError: {str(e)[:80]}")
