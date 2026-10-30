"""Write the per-desk family coverage table. Does not fetch and does not score."""
from __future__ import annotations

import json
from pathlib import Path

from architecture.markets.family_coverage import family_coverage


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    doc = family_coverage()
    path = root / "reports" / "grok" / "PAPER" / "family_coverage.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    print(path)


if __name__ == "__main__":
    main()
