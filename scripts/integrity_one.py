"""Print one integrity_check word for a sqlite path. A missing file is NO_DATA."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.paths import connect_sqlite_ro  # noqa: E402


def main() -> int:
    path = Path(sys.argv[1])
    if not path.is_file():
        print("NO_DATA")
        return 0
    conn = connect_sqlite_ro(path)
    try:
        row = conn.execute("PRAGMA integrity_check").fetchone()
    finally:
        conn.close()
    print(row[0] if row else "NO_DATA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
