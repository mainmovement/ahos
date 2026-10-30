"""Copy one sqlite store with the backup API, integrity_check the copy, then delete it."""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.sqlite_backup_restore import copy_sqlite  # noqa: E402


def main() -> int:
    source = Path(sys.argv[1])
    dest = Path(sys.argv[2])
    if not source.is_file():
        print("NO_DATA")
        return 0
    try:
        copy_sqlite(source, dest)
        conn = sqlite3.connect(str(dest))
        try:
            row = conn.execute("PRAGMA integrity_check").fetchone()
        finally:
            conn.close()
        print(row[0] if row else "NO_DATA")
        return 0
    finally:
        dest.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
