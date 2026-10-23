#!/usr/bin/env python3
"""Export M30 Canonical Memory Consolidation store & snapshot."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from architecture.learning.memory_consolidation import consolidate_canonical_memory


def main() -> int:
    snap = consolidate_canonical_memory(root=ROOT)
    print(
        f"wrote M30 canonical memory: total={snap['total_entries']} "
        f"chain_ok={snap['chain_ok']} head={snap['head_hash'][:12]}"
    )
    return 0 if snap["chain_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
