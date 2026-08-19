"""AHOS Columnar Knowledge Store (DuckDB & SQLite Analytics).

Provides persistent storage, querying, and analytical filtering over
hypotheses, research runs, backtest metrics, and market evidence.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class ColumnarKnowledgeStore:
    """Stores and queries structured research hypotheses and evidence records."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or Path("database/knowledge_analytics.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS research_hypotheses (
                    hypothesis_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    win_rate REAL,
                    oos_efficiency REAL,
                    created_at_utc TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
            """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_hypotheses_status 
                ON research_hypotheses (status, category)
            """
            )
            conn.commit()

    def record_hypothesis_evaluation(
        self,
        hypothesis_id: str,
        title: str,
        category: str,
        status: str,
        sharpe_ratio: float,
        max_drawdown: float,
        win_rate: float,
        oos_efficiency: float,
        created_at_utc: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Inserts or updates a hypothesis evaluation record."""
        meta_str = json.dumps(metadata or {}, sort_keys=True)
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO research_hypotheses (
                    hypothesis_id, title, category, status,
                    sharpe_ratio, max_drawdown, win_rate, oos_efficiency,
                    created_at_utc, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    hypothesis_id,
                    title,
                    category,
                    status,
                    float(sharpe_ratio),
                    float(max_drawdown),
                    float(win_rate),
                    float(oos_efficiency),
                    created_at_utc,
                    meta_str,
                ),
            )
            conn.commit()

    def query_accepted_hypotheses(
        self, min_sharpe: float = 1.2, max_dd: float = 0.25
    ) -> List[Dict[str, Any]]:
        """Queries all validated hypotheses meeting acceptance thresholds."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM research_hypotheses
                WHERE status = 'ACCEPTED' 
                  AND sharpe_ratio >= ? 
                  AND max_drawdown <= ?
                ORDER BY sharpe_ratio DESC
            """,
                (min_sharpe, max_dd),
            )
            rows = cursor.fetchall()
            results = []
            for row in rows:
                item = dict(row)
                item["metadata"] = json.loads(item.pop("metadata_json", "{}"))
                results.append(item)
            return results

    def summary_stats(self) -> Dict[str, Any]:
        """Returns aggregate research statistics."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_hypotheses,
                    SUM(CASE WHEN status = 'ACCEPTED' THEN 1 ELSE 0 END) as accepted_count,
                    SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) as rejected_count,
                    AVG(sharpe_ratio) as avg_sharpe,
                    AVG(win_rate) as avg_win_rate
                FROM research_hypotheses
            """
            )
            row = cursor.fetchone()
            return dict(row) if row else {}
