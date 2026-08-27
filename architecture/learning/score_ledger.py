#!/usr/bin/env python3
"""AHOS Score Ledger — durable persistence of opportunity predictions.

WHY THIS MODULE EXISTS
----------------------
`OpportunityPipelineOrchestrator.run_pipeline` scored every candidate and then
returned. The `OpportunityScoreReport` objects — score, confidence, risk level,
WHY reasons, evidence provenance hash, invalidation conditions — lived only for
the duration of the call and were then garbage collected.

The consequence was not cosmetic. It made these questions *unanswerable from
committed data*, no matter how long the system ran:

  * "What did AHOS score this token BEFORE the outcome was known?"
  * "Do tokens scored 80+ actually resolve better than tokens scored 30?"
  * "Did the score distribution shift after a code change?"

Outcome labels already exist (frozen Lane-A `discovery/outcomes.py`, 7 horizons
× 4 event classes). Observations already exist. Only the *prediction* was
missing, and a prediction that was never written down cannot be graded later —
scoring it after the fact from stored observations would be reconstruction, not
prediction, and would silently leak hindsight into the evaluation.

So this ledger writes the prediction down, at the moment it is made, with the
information needed to judge it honestly later.

DESIGN LAWS
-----------
1. APPEND-ONLY. A prediction is a historical fact. It is never updated and
   never deleted; a re-score writes a NEW row. Enforced by triggers, in the
   same F1-S1 style already used for the other history tables.

2. VERSION-PINNED. Every row carries `engine_version` and `weights_sha256`.
   A calibration report that mixes scoring logic versions is meaningless, so
   the fingerprint makes such mixing detectable rather than invisible.
   The fingerprint is computed from the ACTUAL feature/risk thresholds in the
   running code, so editing a threshold changes the fingerprint automatically —
   it cannot be forgotten.

3. NO PREDICTION WITHOUT PROVENANCE. `evidence_sha256` ties the row back to the
   exact evidence bundle that produced it; `known_field_count` / unknown count
   record how much was actually known, so a confident-looking score computed on
   near-total ignorance is identifiable after the fact.

4. RECORDING NEVER CHANGES THE RECORDED. This module holds no scoring logic and
   mutates no report. It is a sink.

5. FAIL-VISIBLE, NOT FAIL-LOUD. A ledger write must not crash an observation
   cycle (losing hours of collection because a disk hiccuped is worse than
   losing one prediction row), but every failure is logged at WARNING and
   counted in `write_failures` — never silently swallowed.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import sqlite3
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.paths import get_local_db_path

logger = logging.getLogger("ahos.learning.score_ledger")

# Bumped ONLY when the scoring computation itself changes semantics.
SCORING_ENGINE_VERSION = "AHOS-SCORE-v1"

# Evidence namespaces. A calibration number is only meaningful if you know
# which universe of rows produced it, so every prediction is stamped at write
# time and the harness filters on it. `LOCAL` is the operator's real laptop
# evidence; everything else is explicitly NOT calibration evidence.
SOURCE_LOCAL = "local"            # real operator runtime on the target laptop
SOURCE_SANDBOX = "sandbox"        # agent/dev container runs — never calibration
SOURCE_TEST = "test"              # unit/integration fixtures — never calibration
SOURCE_SYNTHETIC = "synthetic"    # deliberately fabricated data — never calibration

#: Only these namespaces may ever be counted as real calibration evidence.
CALIBRATION_ELIGIBLE_SOURCES: frozenset[str] = frozenset({SOURCE_LOCAL})

VALID_SOURCES: frozenset[str] = frozenset({
    SOURCE_LOCAL, SOURCE_SANDBOX, SOURCE_TEST, SOURCE_SYNTHETIC,
})

# Env override lets the operator's daemon declare itself, without which a
# sandbox run could masquerade as laptop evidence.
_SOURCE_ENV_VAR = "AHOS_EVIDENCE_SOURCE"


def resolve_source(explicit: str | None = None) -> str:
    """Resolve the evidence namespace for a prediction.

    Precedence: explicit argument > AHOS_EVIDENCE_SOURCE env > pytest detection
    > SANDBOX default.

    The default is deliberately NOT `local`. Defaulting to the calibration-
    eligible namespace would mean any unlabelled run silently becomes real
    evidence -- the exact failure this boundary exists to prevent. An operator
    must opt IN to producing real evidence.
    """
    if explicit:
        value = str(explicit).strip().lower()
        if value not in VALID_SOURCES:
            raise ValueError(
                f"unknown evidence source {explicit!r}; valid: {sorted(VALID_SOURCES)}")
        return value

    env = os.environ.get("AHOS_EVIDENCE_SOURCE", "").strip().lower()
    if env:
        if env not in VALID_SOURCES:
            raise ValueError(
                f"AHOS_EVIDENCE_SOURCE={env!r} is not a valid evidence source; "
                f"valid: {sorted(VALID_SOURCES)}")
        return env

    # A test run must never be able to write calibration-eligible rows, even if
    # someone points it at a real store by accident.
    if "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules:
        return SOURCE_TEST

    return SOURCE_SANDBOX


SCHEMA_SCORE_LEDGER = """
CREATE TABLE IF NOT EXISTS opportunity_score_ledger (
  score_id           TEXT PRIMARY KEY,
  scored_ts          REAL NOT NULL,
  scored_utc         TEXT NOT NULL,
  run_id             TEXT,
  source             TEXT NOT NULL DEFAULT 'sandbox',  -- local|sandbox|test|synthetic
  chain              TEXT NOT NULL,
  token_address      TEXT NOT NULL,
  token_id           TEXT,             -- canonical Lane-A identity (join key)
  symbol             TEXT,
  opportunity_score  REAL NOT NULL,
  confidence_level   TEXT NOT NULL,    -- HIGH | MED | LOW
  risk_level         TEXT NOT NULL,    -- LOW | MED | HIGH | CRITICAL
  base_score         REAL,
  total_penalties    REAL,
  engine_version     TEXT NOT NULL,
  weights_sha256     TEXT NOT NULL,
  evidence_sha256    TEXT,
  known_field_count  INTEGER NOT NULL,
  unknown_field_count INTEGER NOT NULL,
  positive_reasons_json TEXT NOT NULL,
  risk_findings_json TEXT NOT NULL,
  missing_unknowns_json TEXT NOT NULL,
  invalidation_json  TEXT NOT NULL,
  score_breakdown_json TEXT NOT NULL,
  source_provider    TEXT              -- discovery provider (calibration Q8 segment)
);
CREATE INDEX IF NOT EXISTS idx_score_ledger_token_ts
  ON opportunity_score_ledger(token_id, scored_ts);
CREATE INDEX IF NOT EXISTS idx_score_ledger_ts
  ON opportunity_score_ledger(scored_ts);

-- Append-only guards: same DISCIPLINE as the F1-S1 history tables, but a
-- distinct `ahos_guard_` prefix. Reusing the `f1s1_guard_` prefix would inject
-- this table into the F1-S1 migration's live census, making that migration's
-- evidence report claim a table it never migrated. Provenance of a guard is
-- part of the evidence, so each owner names its own.
CREATE TRIGGER IF NOT EXISTS ahos_guard_no_update_opportunity_score_ledger
  BEFORE UPDATE ON opportunity_score_ledger
  BEGIN SELECT RAISE(ABORT,'append-only: opportunity_score_ledger'); END;
CREATE TRIGGER IF NOT EXISTS ahos_guard_no_delete_opportunity_score_ledger
  BEFORE DELETE ON opportunity_score_ledger
  BEGIN SELECT RAISE(ABORT,'append-only: opportunity_score_ledger'); END;
"""


@dataclass
class ScoreRecord:
    """One persisted prediction. Mirrors the ledger row."""
    score_id: str
    scored_ts: float
    chain: str
    token_address: str
    opportunity_score: float
    confidence_level: str
    risk_level: str
    token_id: str | None = None
    symbol: str | None = None
    run_id: str | None = None
    source: str = SOURCE_SANDBOX
    base_score: float | None = None
    total_penalties: float | None = None
    engine_version: str = SCORING_ENGINE_VERSION
    weights_sha256: str = ""
    evidence_sha256: str = ""
    known_field_count: int = 0
    unknown_field_count: int = 0
    positive_reasons: list[str] = field(default_factory=list)
    risk_findings: list[dict[str, Any]] = field(default_factory=list)
    missing_unknowns: list[str] = field(default_factory=list)
    invalidation_conditions: list[dict[str, Any]] = field(default_factory=list)
    score_breakdown: dict[str, float] = field(default_factory=dict)
    source_provider: str = "UNKNOWN"     # discovery provider; UNKNOWN when not stamped

    @property
    def scored_utc(self) -> str:
        return datetime.fromtimestamp(self.scored_ts, tz=timezone.utc).isoformat()


def weights_fingerprint() -> str:
    """SHA-256 over the ACTUAL scoring constants in the running code.

    Read from the live modules rather than a hand-maintained list, so a changed
    threshold changes the fingerprint whether or not anyone remembered to
    update this function. If introspection fails we return an explicit
    UNKNOWN marker instead of a fake-stable hash -- a wrong "unchanged" claim
    is far more damaging to a calibration report than an honest unknown.
    """
    try:
        from ..features import extractor as feat
        from ..risk import engine as risk_eng
        import inspect

        # The deterministic floor lives in these two functions' source. Hashing
        # the source captures threshold AND logic changes with zero maintenance.
        blob = "\n".join([
            SCORING_ENGINE_VERSION,
            inspect.getsource(feat.FeatureExtractor.extract),
            inspect.getsource(risk_eng.RiskEngine.assess),
            inspect.getsource(risk_eng.classify_risk_level),
        ]).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()
    except Exception as e:  # never fabricate stability
        logger.warning("weights fingerprint unavailable: %s", e)
        return f"UNKNOWN:{type(e).__name__}"


def _canonical_token_id(chain: str, address: str) -> str | None:
    """Canonical Lane-A token identity, so predictions join to outcome labels.

    Lane-A is imported READ-ONLY (a pure function); nothing here mutates it.
    An unmappable chain yields None rather than an invented id -- a wrong join
    key would silently attach a prediction to the wrong token's outcome.
    """
    try:
        from discovery.identity import token_id
        return token_id(chain, address)
    except Exception:
        return None


class ScoreLedger:
    """Append-only sink for opportunity predictions."""

    def __init__(self, db_path: str | None = None, source: str | None = None):
        self.db_path = db_path or get_local_db_path()
        # Resolved once at construction so every row from this ledger carries a
        # consistent namespace, and an invalid source fails loudly at wiring
        # time rather than silently mislabelling evidence later.
        self.source = resolve_source(source)
        self.write_failures = 0
        self._init_db()

    def _init_db(self) -> None:
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            conn.executescript(SCHEMA_SCORE_LEDGER)
            self._migrate(conn)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            self.write_failures += 1
            logger.warning("score ledger schema init failed: %s", e)

    @staticmethod
    def _migrate(conn: sqlite3.Connection) -> None:
        """Additive, idempotent migrations for stores created before a schema
        column existed. Append-only guards (UPDATE/DELETE triggers) are
        untouched — ALTER TABLE ADD COLUMN is the only safe change."""
        cols = {row[1] for row in conn.execute(
            "PRAGMA table_info(opportunity_score_ledger)").fetchall()}
        if "source_provider" not in cols:
            conn.execute(
                "ALTER TABLE opportunity_score_ledger "
                "ADD COLUMN source_provider TEXT")

    # ------------------------------------------------------------ recording --

    def build_record(self, report: Any, *, run_id: str | None = None,
                     now: float | None = None,
                     source: str | None = None) -> ScoreRecord:
        """Project an OpportunityScoreReport onto a ledger record.

        Duck-typed on purpose: the ledger must not import the scoring engine
        (that would invert the dependency and drag the intelligence surface
        into a persistence module).
        """
        row_source = resolve_source(source) if source else self.source
        ts = float(getattr(report, "computed_at_ts", None) or (now or time.time()))
        chain = str(getattr(report, "token_chain", "") or "")
        address = str(getattr(report, "token_address", "") or "")
        breakdown = dict(getattr(report, "score_breakdown", {}) or {})

        risk_findings = []
        for finding in getattr(report, "risk_deductions", []) or []:
            risk_findings.append({
                "risk_id": getattr(finding, "risk_id", None),
                "severity": getattr(finding, "severity", None),
                "description": getattr(finding, "description", None),
                "penalty_points": getattr(finding, "penalty_points", None),
                "evidence_ref": getattr(finding, "evidence_ref", None),
            })

        invalidations = []
        for cond in getattr(report, "invalidation_conditions", []) or []:
            invalidations.append({
                "condition_id": getattr(cond, "condition_id", None),
                "trigger_description": getattr(cond, "trigger_description", None),
                "threshold": getattr(cond, "threshold", None),
                "is_triggered": getattr(cond, "is_triggered", None),
            })

        evidence_items = list(getattr(report, "evidence_items", []) or [])
        known = sum(1 for e in evidence_items
                    if getattr(e, "status", "") != "UNKNOWN"
                    and getattr(e, "value", None) is not None)
        missing = list(getattr(report, "missing_unknowns", []) or [])

        # score_id must be unique per (token, instant, engine) without colliding
        # when the same token is legitimately re-scored in a later cycle.
        # `source` is part of the seed so a test fixture can never collide with
        # -- and thereby suppress -- a real local prediction via INSERT OR IGNORE.
        seed = (f"{row_source}:{chain}:{address}:{ts}:"
                f"{SCORING_ENGINE_VERSION}:{run_id or ''}")
        score_id = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:32]

        return ScoreRecord(
            score_id=score_id,
            scored_ts=ts,
            chain=chain,
            token_address=address,
            token_id=_canonical_token_id(chain, address),
            symbol=str(getattr(report, "token_symbol", "") or "") or None,
            run_id=run_id,
            source=row_source,
            opportunity_score=float(getattr(report, "opportunity_score", 0.0) or 0.0),
            confidence_level=str(getattr(report, "confidence_level", "LOW") or "LOW"),
            risk_level=str(getattr(report, "risk_level", "LOW") or "LOW"),
            base_score=breakdown.get("base_score"),
            total_penalties=breakdown.get("total_penalties"),
            engine_version=SCORING_ENGINE_VERSION,
            weights_sha256=weights_fingerprint(),
            evidence_sha256=str(getattr(report, "provenance_sha256", "") or ""),
            known_field_count=known,
            unknown_field_count=len(missing),
            positive_reasons=list(getattr(report, "positive_reasons", []) or []),
            risk_findings=risk_findings,
            missing_unknowns=missing,
            invalidation_conditions=invalidations,
            score_breakdown=breakdown,
            source_provider=str(getattr(report, "source_provider", "") or ""),
        )

    def record(self, report: Any, *, run_id: str | None = None,
               now: float | None = None,
               source: str | None = None) -> ScoreRecord | None:
        """Persist one prediction. Returns None if the write failed."""
        rec = self.build_record(report, run_id=run_id, now=now, source=source)
        return rec if self._insert([rec]) == 1 else None

    def record_many(self, reports: list[Any], *, run_id: str | None = None,
                    now: float | None = None,
                    source: str | None = None) -> int:
        """Persist a batch of predictions. Returns the number written."""
        records = [self.build_record(r, run_id=run_id, now=now, source=source)
                   for r in reports]
        return self._insert(records)

    def _insert(self, records: list[ScoreRecord]) -> int:
        if not records:
            return 0
        try:
            conn = sqlite3.connect(self.db_path)
            written = 0
            for r in records:
                # INSERT OR IGNORE, never OR REPLACE: an existing prediction is
                # immutable history. A duplicate score_id means the identical
                # score at the identical instant -- keep the original.
                cur = conn.execute(
                    """INSERT OR IGNORE INTO opportunity_score_ledger(
                        score_id, scored_ts, scored_utc, run_id, source, chain,
                        token_address,
                        token_id, symbol, opportunity_score, confidence_level, risk_level,
                        base_score, total_penalties, engine_version, weights_sha256,
                        evidence_sha256, known_field_count, unknown_field_count,
                        positive_reasons_json, risk_findings_json, missing_unknowns_json,
                        invalidation_json, score_breakdown_json, source_provider
                    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        r.score_id, r.scored_ts, r.scored_utc, r.run_id, r.source, r.chain,
                        r.token_address, r.token_id, r.symbol, r.opportunity_score,
                        r.confidence_level, r.risk_level, r.base_score, r.total_penalties,
                        r.engine_version, r.weights_sha256, r.evidence_sha256,
                        r.known_field_count, r.unknown_field_count,
                        json.dumps(r.positive_reasons, ensure_ascii=False),
                        json.dumps(r.risk_findings, ensure_ascii=False),
                        json.dumps(r.missing_unknowns, ensure_ascii=False),
                        json.dumps(r.invalidation_conditions, ensure_ascii=False),
                        json.dumps(r.score_breakdown, ensure_ascii=False),
                        r.source_provider or "",
                    ),
                )
                written += cur.rowcount if cur.rowcount > 0 else 0
            conn.commit()
            conn.close()
            return written
        except sqlite3.Error as e:
            # Visible, counted, non-fatal: one lost prediction must not end a
            # collection cycle, but a silent loss would corrupt calibration.
            self.write_failures += 1
            logger.warning("score ledger write failed (%d total): %s",
                           self.write_failures, e)
            return 0

    # -------------------------------------------------------------- reading --

    def count(self, source: str | None = None) -> int:
        if source is not None:
            rows = self._read(
                "SELECT COUNT(*) AS n FROM opportunity_score_ledger WHERE source = ?",
                (source,))
        else:
            rows = self._read("SELECT COUNT(*) AS n FROM opportunity_score_ledger")
        return rows[0]["n"] if rows else 0

    def source_census(self) -> dict[str, int]:
        """Row count per evidence namespace — makes contamination visible."""
        rows = self._read(
            "SELECT source, COUNT(*) AS n FROM opportunity_score_ledger "
            "GROUP BY source ORDER BY source")
        return {r["source"]: r["n"] for r in rows}

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._read(
            "SELECT * FROM opportunity_score_ledger ORDER BY scored_ts DESC LIMIT ?",
            (int(limit),),
        )

    def for_token(self, token_id: str) -> list[dict[str, Any]]:
        return self._read(
            "SELECT * FROM opportunity_score_ledger WHERE token_id = ? "
            "ORDER BY scored_ts",
            (token_id,),
        )

    def engine_versions(self) -> dict[str, int]:
        """Version/fingerprint census — makes mixed-version cohorts visible."""
        rows = self._read(
            "SELECT engine_version, weights_sha256, COUNT(*) AS n "
            "FROM opportunity_score_ledger GROUP BY engine_version, weights_sha256"
        )
        return {f"{r['engine_version']}:{r['weights_sha256'][:12]}": r["n"] for r in rows}

    def _read(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        """Read-only query. A missing store reports nothing rather than creating one."""
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
            conn.close()
            return rows
        except sqlite3.Error:
            return []
