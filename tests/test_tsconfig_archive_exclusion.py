"""Phase 3 M1 - archived divergent TS copies are excluded from `tsc --noEmit`.

docs/archive/** holds historical snapshots whose relative imports no longer
resolve; type-checking them produced 9 false errors. Live code must not import
from the archive (so excluding it cannot hide a real error). Self-test only.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_tsconfig_excludes_docs_archive_and_keeps_existing_excludes():
    cfg = json.loads((ROOT / "tsconfig.json").read_text(encoding="utf-8"))
    ex = cfg["exclude"]
    assert "docs/archive" in ex
    assert "node_modules" in ex and "01" in ex
    assert "**/*.ts" in cfg["include"] and "**/*.tsx" in cfg["include"]
    assert cfg["compilerOptions"]["strict"] is True


def test_live_ts_never_imports_from_docs_archive():
    import os
    pat = re.compile(r"""from\s+["'][^"']*docs/archive|import\(\s*["'][^"']*docs/archive""")
    prune = {"node_modules", ".next", "docs", "01", ".git", ".venv", "venv", "data", "reports", "__pycache__"}
    hits = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in prune and not d.startswith(".")]
        for fn in filenames:
            if fn.endswith((".ts", ".tsx")):
                p = Path(dirpath) / fn
                if pat.search(p.read_text(encoding="utf-8", errors="ignore")):
                    hits.append(str(p.relative_to(ROOT)))
    assert hits == [], hits
