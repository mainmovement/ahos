#!/usr/bin/env python3
"""AHOS Versioned Claim & Evidence Store (Phase XXII - K-02).

Non-negotiable Laws:
  - Append-only: No claim version is ever mutated or deleted; changes bump the version integer.
  - Strict Partitioning: CANONICAL, RESEARCH, LENS, MODEL, HYPOTHESIS, and UNVERIFIED claims
    are strictly partitioned.
  - AI Isolation: AI-generated claims are marked AI_INTERPRETATION / HYPOTHESIS and cannot
    silently promote to CANONICAL without explicit human governance approval.
  - Contradiction Tracking: Contradiction edges are recorded as explicit causal graphs.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .contracts import (
    TrustClass,
    ClaimCategory,
    VersionedClaim,
    EvidenceLink
)
from config.paths import get_knowledge_db_path

SCHEMA_KNOWLEDGE = """
CREATE TABLE IF NOT EXISTS knowledge_claims (
  claim_id        TEXT NOT NULL,
  version         INTEGER NOT NULL,
  category        TEXT NOT NULL,
  statement       TEXT NOT NULL,
  trust_class     TEXT NOT NULL,
  author_source_id TEXT NOT NULL,
  evidence_links_json TEXT NOT NULL,
  contradictions_json TEXT NOT NULL,
  provenance_sha256 TEXT NOT NULL,
  created_ts      REAL NOT NULL,
  review_status   TEXT NOT NULL,
  confidence      REAL NOT NULL,
  meta_json       TEXT,
  PRIMARY KEY (claim_id, version)
);

CREATE TABLE IF NOT EXISTS claim_contradiction_edges (
  source_claim_id TEXT NOT NULL,
  target_claim_id TEXT NOT NULL,
  reason          TEXT NOT NULL,
  noted_ts        REAL NOT NULL,
  PRIMARY KEY (source_claim_id, target_claim_id)
);
"""


class VersionedClaimStore:
    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or get_knowledge_db_path()
        self._init_db()

    def _init_db(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.executescript(SCHEMA_KNOWLEDGE)
        conn.close()

    def store_claim(self, claim: VersionedClaim) -> str:
        # Integrity Law: Canonical claims cannot be authored by raw AI without human gate
        if claim.category == ClaimCategory.CANONICAL and claim.trust_class == TrustClass.AI_INTERPRETATION:
            raise PermissionError("EPISTEMIC VETO: AI_INTERPRETATION cannot author CANONICAL claim directly.")

        conn = sqlite3.connect(self.db_path)
        # Check current latest version
        cur = conn.cursor()
        cur.execute("SELECT MAX(version) FROM knowledge_claims WHERE claim_id=?", (claim.claim_id,))
        row = cur.fetchone()
        latest_ver = row[0] if (row and row[0] is not None) else 0

        # Calculate next version
        new_ver = latest_ver + 1
        claim.version = new_ver

        ev_list = []
        for e in claim.evidence_links:
            d = asdict(e)
            d["trust_class"] = e.trust_class.value if isinstance(e.trust_class, TrustClass) else str(e.trust_class)
            ev_list.append(d)
        ev_json = json.dumps(ev_list)
        contra_json = json.dumps(claim.contradiction_edges)

        conn.execute(
            """INSERT INTO knowledge_claims(
                claim_id, version, category, statement, trust_class, author_source_id,
                evidence_links_json, contradictions_json, provenance_sha256, created_ts,
                review_status, confidence, meta_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                claim.claim_id, claim.version, claim.category.value, claim.statement,
                claim.trust_class.value, claim.author_or_source_id, ev_json, contra_json,
                claim.provenance_sha256, claim.created_ts, claim.review_status,
                claim.confidence, json.dumps(claim.meta)
            )
        )

        # Store contradiction edges
        for edge in claim.contradiction_edges:
            target = edge.get("target_claim_id")
            reason = edge.get("reason", "Contradiction identified")
            if target:
                conn.execute(
                    """INSERT OR REPLACE INTO claim_contradiction_edges(source_claim_id, target_claim_id, reason, noted_ts)
                       VALUES (?,?,?,?)""",
                    (claim.claim_id, target, reason, claim.created_ts)
                )

        conn.commit()
        conn.close()
        return f"{claim.claim_id}:v{claim.version}"

    def get_latest_claim(self, claim_id: str) -> VersionedClaim | None:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        row = cur.execute(
            "SELECT * FROM knowledge_claims WHERE claim_id=? ORDER BY version DESC LIMIT 1",
            (claim_id,)
        ).fetchone()
        conn.close()
        if not row:
            return None
        return self._row_to_claim(row)

    def get_claim_version_history(self, claim_id: str) -> list[VersionedClaim]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM knowledge_claims WHERE claim_id=? ORDER BY version ASC",
            (claim_id,)
        ).fetchall()
        conn.close()
        return [self._row_to_claim(r) for r in rows]

    def find_contradictions_for_claim(self, claim_id: str) -> list[dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """SELECT * FROM claim_contradiction_edges
               WHERE source_claim_id=? OR target_claim_id=?""",
            (claim_id, claim_id)
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _row_to_claim(self, row: sqlite3.Row) -> VersionedClaim:
        ev_list_raw = json.loads(row["evidence_links_json"])
        evidence_links = [
            EvidenceLink(
                evidence_id=e["evidence_id"],
                source_id=e["source_id"],
                trust_class=TrustClass(e["trust_class"]),
                pointer=e["pointer"],
                description=e["description"],
                raw_sha256=e["raw_sha256"],
                retrieved_ts=e["retrieved_ts"]
            ) for e in ev_list_raw
        ]
        return VersionedClaim(
            claim_id=row["claim_id"],
            version=row["version"],
            category=ClaimCategory(row["category"]),
            statement=row["statement"],
            trust_class=TrustClass(row["trust_class"]),
            author_or_source_id=row["author_source_id"],
            evidence_links=evidence_links,
            contradicting_evidence_ids=[],
            contradiction_edges=json.loads(row["contradictions_json"]),
            provenance_sha256=row["provenance_sha256"],
            created_ts=row["created_ts"],
            review_status=row["review_status"],
            confidence=row["confidence"],
            meta=json.loads(row["meta_json"]) if row["meta_json"] else {}
        )
