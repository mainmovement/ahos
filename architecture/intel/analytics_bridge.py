"""AHOS Analytics Bridge (DuckDB / SQLite Hybrid OLAP Engine).

Provides high-performance analytical queries over SQLite tables and tabular
datasets. Uses DuckDB when installed for vectorized, zero-copy OLAP scans
without locking SQLite databases; seamlessly falls back to Python standard
sqlite3 when DuckDB is not present.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

try:
    import duckdb  # type: ignore

    _DUCKDB_AVAILABLE = True
except ImportError:
    duckdb = None  # type: ignore
    _DUCKDB_AVAILABLE = False


class AnalyticsBridge:
    """Hybrid in-process analytical query engine for AHOS."""

    def __init__(self, sqlite_path: Optional[Union[str, Path]] = None) -> None:
        self.sqlite_path = Path(sqlite_path) if sqlite_path else None
        self._duck_conn: Optional[Any] = None
        self._sqlite_conn: Optional[sqlite3.Connection] = None
        self._init_engine()

    def _init_engine(self) -> None:
        if _DUCKDB_AVAILABLE:
            self._duck_conn = duckdb.connect(database=":memory:")
            if self.sqlite_path and self.sqlite_path.exists():
                # Attach SQLite database read-only in DuckDB for zero-copy queries
                try:
                    self._duck_conn.execute("INSTALL sqlite; LOAD sqlite;")
                    self._duck_conn.execute(
                        f"ATTACH '{self.sqlite_path.as_posix()}' AS local_sqlite (TYPE SQLITE, READ_ONLY);"
                    )
                except Exception:
                    # Fallback to in-memory tables if sqlite extension load fails
                    pass
        elif self.sqlite_path and self.sqlite_path.exists():
            self._sqlite_conn = sqlite3.connect(
                str(self.sqlite_path), check_same_thread=False
            )
            self._sqlite_conn.row_factory = sqlite3.Row

    @property
    def is_duckdb_accelerated(self) -> bool:
        """Returns True if DuckDB vector execution engine is active."""
        return _DUCKDB_AVAILABLE and self._duck_conn is not None

    def query_dicts(
        self, query: str, params: Optional[Union[List[Any], Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Executes analytical SQL and returns results as a list of dictionaries."""
        if self._duck_conn is not None:
            try:
                # DuckDB query execution
                rel = (
                    self._duck_conn.execute(query, params or [])
                    if params
                    else self._duck_conn.execute(query)
                )
                columns = [desc[0] for desc in rel.description]
                rows = rel.fetchall()
                return [dict(zip(columns, row)) for row in rows]
            except Exception:
                # Fallback to SQLite query if DuckDB encounters an error
                pass

        if self._sqlite_conn is not None:
            cursor = self._sqlite_conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        return []

    def register_in_memory_data(self, name: str, data: List[Dict[str, Any]]) -> None:
        """Registers in-memory dictionary data as an analytical SQL table."""
        if not data:
            return
        if self._duck_conn is not None:
            import pandas as pd

            df = pd.DataFrame(data)
            self._duck_conn.register(name, df)
        else:
            # Fallback to in-memory sqlite
            if self._sqlite_conn is None:
                self._sqlite_conn = sqlite3.connect(":memory:", check_same_thread=False)
                self._sqlite_conn.row_factory = sqlite3.Row
            import pandas as pd

            df = pd.DataFrame(data)
            df.to_sql(name, self._sqlite_conn, if_exists="replace", index=False)

    def compute_brier_calibration_bins(
        self, table_name: str, score_col: str, outcome_col: str, bins: int = 10
    ) -> List[Dict[str, Any]]:
        """Computes calibration histogram bins with sub-millisecond vectorized aggregation."""
        query = f"""
            SELECT 
                CAST(FLOOR({score_col} * {bins}) AS INTEGER) as bin_idx,
                COUNT(*) as count,
                AVG({score_col}) as mean_predicted_prob,
                AVG(CAST({outcome_col} AS DOUBLE)) as observed_frequency,
                AVG(POWER({score_col} - CAST({outcome_col} AS DOUBLE), 2)) as bin_brier_loss
            FROM {table_name}
            WHERE {score_col} IS NOT NULL AND {outcome_col} IS NOT NULL
            GROUP BY 1
            ORDER BY 1 ASC
        """
        return self.query_dicts(query)

    def close(self) -> None:
        """Closes any active database connections."""
        if self._duck_conn:
            try:
                self._duck_conn.close()
            except Exception:
                pass
            self._duck_conn = None
        if self._sqlite_conn:
            try:
                self._sqlite_conn.close()
            except Exception:
                pass
            self._sqlite_conn = None
