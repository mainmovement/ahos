import os, sys
# ensure the repo root is NOT on sys.path -> use the pip-installed copy in site-packages
sys.path = [p for p in sys.path if "fdb_repo" not in p]
import financedatabase as fd
print("pkg __file__ :", fd.__file__)
print("file_path    :", fd.helpers.file_path)
print("dir exists   :", os.path.isdir(str(fd.helpers.file_path)))
try:
    d = fd.Cryptos(use_local_location=True)
    print("RESULT: LOADED rows=", len(d.data))
except Exception as e:
    print("RESULT: RAISED", type(e).__name__)
    print("        ", str(e)[:300])
print()
print("--- also: is financetoolkit importable in this venv (installed --no-deps)? ---")
try:
    import financetoolkit; print("  financetoolkit PRESENT", financetoolkit.__version__ if hasattr(financetoolkit,'__version__') else "")
except ImportError as e:
    print("  financetoolkit ABSENT ->", type(e).__name__, str(e)[:100])
print("--- does `import financedatabase` still work without financetoolkit? ---")
print("  YES (proves financetoolkit is a hard *declared* dep but not an import-time dep)")
print("--- to_toolkit() behaviour without financetoolkit ---")
try:
    d = fd.Cryptos.__new__(fd.Cryptos)
    import pandas as pd
    d.data = pd.DataFrame(index=pd.Index(["BTC-USD"], name="symbol"))
    fr = fd.helpers.FinanceFrame(d.data)
    fr.to_toolkit()
except ImportError as e:
    print("  RAISED ImportError:", str(e)[:150])
except Exception as e:
    print("  RAISED", type(e).__name__, str(e)[:200])
