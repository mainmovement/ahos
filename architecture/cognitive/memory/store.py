"""Isolated Lane-B SQLite cognitive memory store.

Never opens e01_discovery / paper_trading / ahos_local / ahos_knowledge.
Append-only revisions. Contradictions are edges, not overwrites.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Iterable

from architecture.cognitive.memory.record import (
    EpistemicViolation,
    InvalidProvenanceError,
    MemoryRecord,
    compute_integrity_hash,
    validate_new_record,
)
from architecture.cognitive.memory.types import (
    FORBIDDEN_DB_NAMES,
    SCHEMA_VERSION,
    UNKNOWN,
    WORLD_MODEL_OBJECT_KINDS,
    ContradictionState,
    DecayState,
    EdgeRelation,
    EdgeResolution,
    EpistemicKind,
    MemoryType,
    SourceType,
)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memories (
  memory_id TEXT NOT NULL,
  revision INTEGER NOT NULL,
  memory_type TEXT NOT NULL,
  epistemic_kind TEXT NOT NULL,
  statement TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  created_at REAL NOT NULL,
  observed_at REAL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  source_location TEXT NOT NULL,
  producer TEXT NOT NULL,
  producer_version TEXT NOT NULL,
  domain TEXT NOT NULL,
  context TEXT NOT NULL,
  confidence REAL,
  valid_from REAL,
  valid_until REAL,
  status TEXT NOT NULL,
  contradiction_state TEXT NOT NULL,
  supersedes TEXT NOT NULL DEFAULT '',
  derived_from_json TEXT NOT NULL,
  outcome_link TEXT NOT NULL DEFAULT '',
  hypothesis_id TEXT NOT NULL DEFAULT '',
  experiment_id TEXT NOT NULL DEFAULT '',
  agent_id TEXT NOT NULL DEFAULT '',
  agent_namespace TEXT NOT NULL DEFAULT '',
  ttl_seconds REAL,
  session_id TEXT NOT NULL DEFAULT '',
  task_id TEXT NOT NULL DEFAULT '',
  priority INTEGER NOT NULL DEFAULT 0,
  expires_at REAL,
  integrity_hash TEXT NOT NULL,
  correction_reason TEXT NOT NULL DEFAULT '',
  prediction_id TEXT NOT NULL DEFAULT '',
  capability_gap_id TEXT NOT NULL DEFAULT '',
  proposal_id TEXT NOT NULL DEFAULT '',
  PRIMARY KEY (memory_id, revision)
);

CREATE INDEX IF NOT EXISTS idx_mem_type ON memories(memory_type);
CREATE INDEX IF NOT EXISTS idx_mem_source ON memories(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_mem_domain ON memories(domain);
CREATE INDEX IF NOT EXISTS idx_mem_hyp ON memories(hypothesis_id);
CREATE INDEX IF NOT EXISTS idx_mem_exp ON memories(experiment_id);
CREATE INDEX IF NOT EXISTS idx_mem_agent ON memories(agent_namespace, agent_id);
CREATE INDEX IF NOT EXISTS idx_mem_created ON memories(created_at);
CREATE INDEX IF NOT EXISTS idx_mem_observed ON memories(observed_at);
CREATE INDEX IF NOT EXISTS idx_mem_status ON memories(status);
CREATE INDEX IF NOT EXISTS idx_mem_kind ON memories(epistemic_kind);
CREATE INDEX IF NOT EXISTS idx_mem_pred ON memories(prediction_id);

CREATE TABLE IF NOT EXISTS memory_edges (
  edge_id TEXT PRIMARY KEY,
  from_id TEXT NOT NULL,
  to_id TEXT NOT NULL,
  relation TEXT NOT NULL,
  reason TEXT NOT NULL,
  created_at REAL NOT NULL,
  resolution TEXT NOT NULL,
  resolved_at REAL,
  resolver TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_edge_from ON memory_edges(from_id, relation);
CREATE INDEX IF NOT EXISTS idx_edge_to ON memory_edges(to_id, relation);

CREATE TABLE IF NOT EXISTS failure_stats (
  fingerprint TEXT PRIMARY KEY,
  failure_type TEXT NOT NULL,
  component TEXT NOT NULL,
  recurrence_count INTEGER NOT NULL,
  first_memory_id TEXT NOT NULL,
  last_memory_id TEXT NOT NULL,
  last_occurrence REAL NOT NULL
);
"""


class SoakBoundaryError(RuntimeError):
    pass


class IntegrityError(RuntimeError):
    pass


class MemoryAuthorizationError(PermissionError):
    pass


def assert_not_soak_db(path: Path) -> None:
    name = path.name.lower()
    if name in FORBIDDEN_DB_NAMES:
        raise SoakBoundaryError(
            f"Refusing to open {path.name}: cognitive memory must not use soak/Lane-A/knowledge DBs"
        )


def default_memory_db_path() -> Path:
    from config.paths import get_cognitive_memory_db_path

    return Path(get_cognitive_memory_db_path(create_dir=True))


def _row_to_record(row: sqlite3.Row) -> MemoryRecord:
    rec = MemoryRecord(
        memory_id=row["memory_id"],
        revision=int(row["revision"]),
        memory_type=row["memory_type"],
        epistemic_kind=row["epistemic_kind"],
        statement=row["statement"],
        created_at=float(row["created_at"]),
        observed_at=None if row["observed_at"] is None else float(row["observed_at"]),
        source_type=row["source_type"],
        source_id=row["source_id"],
        source_location=row["source_location"],
        producer=row["producer"],
        producer_version=row["producer_version"],
        domain=row["domain"],
        context=row["context"],
        confidence=None if row["confidence"] is None else float(row["confidence"]),
        valid_from=None if row["valid_from"] is None else float(row["valid_from"]),
        valid_until=None if row["valid_until"] is None else float(row["valid_until"]),
        status=row["status"],
        contradiction_state=row["contradiction_state"],
        integrity_hash=row["integrity_hash"],
        payload=json.loads(row["payload_json"] or "{}"),
        supersedes=row["supersedes"] or "",
        derived_from=json.loads(row["derived_from_json"] or "[]"),
        outcome_link=row["outcome_link"] or "",
        hypothesis_id=row["hypothesis_id"] or "",
        experiment_id=row["experiment_id"] or "",
        agent_id=row["agent_id"] or "",
        agent_namespace=row["agent_namespace"] or "",
        ttl_seconds=None if row["ttl_seconds"] is None else float(row["ttl_seconds"]),
        session_id=row["session_id"] or "",
        task_id=row["task_id"] or "",
        priority=int(row["priority"] or 0),
        expires_at=None if row["expires_at"] is None else float(row["expires_at"]),
        correction_reason=row["correction_reason"] or "",
        prediction_id=row["prediction_id"] or "",
        capability_gap_id=row["capability_gap_id"] or "",
        proposal_id=row["proposal_id"] or "",
    )
    expected = compute_integrity_hash(rec)
    if expected != rec.integrity_hash:
        raise IntegrityError(
            f"integrity mismatch for {rec.memory_id}:v{rec.revision}"
        )
    return rec


INSERT_SQL = """
INSERT INTO memories(
  memory_id, revision, memory_type, epistemic_kind, statement, payload_json,
  created_at, observed_at, source_type, source_id, source_location, producer,
  producer_version, domain, context, confidence, valid_from, valid_until,
  status, contradiction_state, supersedes, derived_from_json, outcome_link,
  hypothesis_id, experiment_id, agent_id, agent_namespace, ttl_seconds,
  session_id, task_id, priority, expires_at, integrity_hash, correction_reason,
  prediction_id, capability_gap_id, proposal_id
) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
"""


def _insert_params(rec: MemoryRecord) -> tuple[Any, ...]:
    return (
        rec.memory_id,
        rec.revision,
        rec.memory_type,
        rec.epistemic_kind,
        rec.statement,
        json.dumps(rec.payload, sort_keys=True),
        rec.created_at,
        rec.observed_at,
        rec.source_type,
        rec.source_id,
        rec.source_location,
        rec.producer,
        rec.producer_version,
        rec.domain,
        rec.context,
        rec.confidence,
        rec.valid_from,
        rec.valid_until,
        rec.status,
        rec.contradiction_state,
        rec.supersedes,
        json.dumps(list(rec.derived_from), sort_keys=True),
        rec.outcome_link,
        rec.hypothesis_id,
        rec.experiment_id,
        rec.agent_id,
        rec.agent_namespace,
        rec.ttl_seconds,
        rec.session_id,
        rec.task_id,
        rec.priority,
        rec.expires_at,
        rec.integrity_hash,
        rec.correction_reason,
        rec.prediction_id,
        rec.capability_gap_id,
        rec.proposal_id,
    )


@dataclass(frozen=True)
class MemoryEdge:
    edge_id: str
    from_id: str
    to_id: str
    relation: str
    reason: str
    created_at: float
    resolution: str
    resolved_at: float | None = None
    resolver: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "from_id": self.from_id,
            "to_id": self.to_id,
            "relation": self.relation,
            "reason": self.reason,
            "created_at": self.created_at,
            "resolution": self.resolution,
            "resolved_at": self.resolved_at,
            "resolver": self.resolver,
        }


class CognitiveMemoryStore:
    """Append-oriented Lane-B memory. Caller supplies the DB path in tests."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.path = Path(db_path) if db_path is not None else default_memory_db_path()
        assert_not_soak_db(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA_SQL)
            row = conn.execute(
                "SELECT value FROM schema_meta WHERE key='schema_version'"
            ).fetchone()
            if row is None:
                conn.execute(
                    "INSERT INTO schema_meta(key, value) VALUES ('schema_version', ?)",
                    (str(SCHEMA_VERSION),),
                )
            else:
                found = int(row["value"])
                if found > SCHEMA_VERSION:
                    raise RuntimeError(
                        f"cognitive memory schema {found} newer than code {SCHEMA_VERSION}"
                    )
            conn.commit()

    def integrity_check(self) -> str:
        with self._connect() as conn:
            row = conn.execute("PRAGMA integrity_check").fetchone()
            return str(row[0]) if row else UNKNOWN

    def _next_id(self, conn: sqlite3.Connection) -> str:
        row = conn.execute("SELECT COUNT(DISTINCT memory_id) AS n FROM memories").fetchone()
        n = int(row["n"] if row else 0) + 1
        return f"MEM-{n:06d}"

    def _latest_row(self, conn: sqlite3.Connection, memory_id: str) -> sqlite3.Row | None:
        return conn.execute(
            "SELECT * FROM memories WHERE memory_id=? ORDER BY revision DESC LIMIT 1",
            (memory_id,),
        ).fetchone()

    def remember(
        self,
        *,
        memory_type: MemoryType | str,
        epistemic_kind: EpistemicKind | str,
        statement: str,
        source_type: SourceType | str = SourceType.UNKNOWN,
        source_id: str = UNKNOWN,
        source_location: str = UNKNOWN,
        producer: str = UNKNOWN,
        producer_version: str = UNKNOWN,
        domain: str = "COGNITIVE_CORE",
        context: str = UNKNOWN,
        confidence: float | None = None,
        created_at: float | None = None,
        observed_at: float | None = None,
        valid_from: float | None = None,
        valid_until: float | None = None,
        payload: dict[str, Any] | None = None,
        hypothesis_id: str = "",
        experiment_id: str = "",
        outcome_link: str = "",
        agent_id: str = "",
        agent_namespace: str = "",
        ttl_seconds: float | None = None,
        session_id: str = "",
        task_id: str = "",
        priority: int = 0,
        prediction_id: str = "",
        capability_gap_id: str = "",
        proposal_id: str = "",
        derived_from: Iterable[str] = (),
        supersedes: str = "",
        memory_id: str | None = None,
    ) -> MemoryRecord:
        now = float(time.time() if created_at is None else created_at)
        mtype = MemoryType(memory_type).value
        kind = EpistemicKind(epistemic_kind).value
        src = SourceType(source_type).value
        ttl = float(ttl_seconds) if ttl_seconds is not None else None
        expires_at = None
        if mtype == MemoryType.WORKING.value and ttl is not None:
            expires_at = now + ttl
        ns = agent_namespace or agent_id
        rec = MemoryRecord(
            memory_id=memory_id or "PENDING",
            revision=1,
            memory_type=mtype,
            epistemic_kind=kind,
            statement=statement.strip(),
            created_at=now,
            observed_at=None if observed_at is None else float(observed_at),
            source_type=src,
            source_id=source_id,
            source_location=source_location,
            producer=producer,
            producer_version=producer_version,
            domain=domain,
            context=context,
            confidence=None if confidence is None else float(confidence),
            valid_from=None if valid_from is None else float(valid_from),
            valid_until=None if valid_until is None else float(valid_until),
            status=DecayState.ACTIVE.value,
            contradiction_state=ContradictionState.UNCONTESTED.value,
            integrity_hash="",
            payload=dict(payload or {}),
            supersedes=supersedes,
            derived_from=list(derived_from),
            outcome_link=outcome_link,
            hypothesis_id=hypothesis_id,
            experiment_id=experiment_id,
            agent_id=agent_id,
            agent_namespace=ns,
            ttl_seconds=ttl,
            session_id=session_id,
            task_id=task_id,
            priority=priority,
            expires_at=expires_at,
            prediction_id=prediction_id,
            capability_gap_id=capability_gap_id,
            proposal_id=proposal_id,
        )
        validate_new_record(rec)
        with self._connect() as conn:
            if memory_id:
                existing = self._latest_row(conn, memory_id)
                if existing is not None:
                    raise ValueError(
                        f"{memory_id} already exists; use revise() for a new revision"
                    )
            else:
                rec.memory_id = self._next_id(conn)
            rec.integrity_hash = compute_integrity_hash(rec)
            conn.execute(INSERT_SQL, _insert_params(rec))
            for parent in rec.derived_from:
                self._insert_edge(
                    conn,
                    from_id=rec.memory_id,
                    to_id=parent,
                    relation=EdgeRelation.DERIVED_FROM,
                    reason="derived_from",
                    created_at=now,
                )
            conn.commit()
        return rec

    def _insert_edge(
        self,
        conn: sqlite3.Connection,
        *,
        from_id: str,
        to_id: str,
        relation: EdgeRelation | str,
        reason: str,
        created_at: float,
    ) -> MemoryEdge:
        rel = EdgeRelation(relation).value
        edge_id = hashlib.sha256(
            f"{from_id}|{to_id}|{rel}|{created_at}|{reason}".encode("utf-8")
        ).hexdigest()[:16]
        conn.execute(
            """INSERT OR IGNORE INTO memory_edges(
                 edge_id, from_id, to_id, relation, reason, created_at, resolution, resolved_at, resolver
               ) VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                edge_id,
                from_id,
                to_id,
                rel,
                reason,
                created_at,
                EdgeResolution.OPEN.value,
                None,
                "",
            ),
        )
        return MemoryEdge(
            edge_id=edge_id,
            from_id=from_id,
            to_id=to_id,
            relation=rel,
            reason=reason,
            created_at=created_at,
            resolution=EdgeResolution.OPEN.value,
        )

    def get(self, memory_id: str, revision: int | None = None) -> MemoryRecord | None:
        with self._connect() as conn:
            if revision is None:
                row = self._latest_row(conn, memory_id)
            else:
                row = conn.execute(
                    "SELECT * FROM memories WHERE memory_id=? AND revision=?",
                    (memory_id, revision),
                ).fetchone()
            if row is None:
                return None
            return _row_to_record(row)

    def history(self, memory_id: str) -> list[MemoryRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM memories WHERE memory_id=? ORDER BY revision ASC",
                (memory_id,),
            ).fetchall()
            return [_row_to_record(r) for r in rows]

    def revise(
        self,
        memory_id: str,
        *,
        statement: str | None = None,
        status: DecayState | str | None = None,
        contradiction_state: ContradictionState | str | None = None,
        correction_reason: str = "",
        confidence: float | None | object = ...,
        outcome_link: str | None = None,
        experiment_id: str | None = None,
        now: float | None = None,
    ) -> MemoryRecord:
        """Append a revision. Does not mutate prior rows."""
        ts = time.time() if now is None else now
        with self._connect() as conn:
            row = self._latest_row(conn, memory_id)
            if row is None:
                raise KeyError(memory_id)
            prev = _row_to_record(row)
            new_statement = prev.statement if statement is None else statement.strip()
            payload = dict(prev.payload)
            if new_statement != prev.statement:
                payload.pop("observation_grant", None)
            nxt = replace(
                prev,
                revision=prev.revision + 1,
                created_at=ts,
                statement=new_statement,
                payload=payload,
                status=prev.status if status is None else DecayState(status).value,
                contradiction_state=(
                    prev.contradiction_state
                    if contradiction_state is None
                    else ContradictionState(contradiction_state).value
                ),
                correction_reason=correction_reason or prev.correction_reason,
                outcome_link=prev.outcome_link if outcome_link is None else outcome_link,
                experiment_id=prev.experiment_id if experiment_id is None else experiment_id,
                integrity_hash="",
            )
            if confidence is not ...:
                nxt.confidence = confidence  # type: ignore[assignment]
            nxt.integrity_hash = compute_integrity_hash(nxt)
            conn.execute(INSERT_SQL, _insert_params(nxt))
            conn.commit()
            return nxt

    def _latest_all(self, conn: sqlite3.Connection) -> list[MemoryRecord]:
        rows = conn.execute(
            """
            SELECT m.* FROM memories m
            INNER JOIN (
              SELECT memory_id, MAX(revision) AS rev FROM memories GROUP BY memory_id
            ) t ON m.memory_id = t.memory_id AND m.revision = t.rev
            ORDER BY m.memory_id ASC
            """
        ).fetchall()
        return [_row_to_record(r) for r in rows]

    def find_by_type(self, memory_type: MemoryType | str) -> list[MemoryRecord]:
        want = MemoryType(memory_type).value
        with self._connect() as conn:
            return [r for r in self._latest_all(conn) if r.memory_type == want]

    def find_by_source(self, source_id: str) -> list[MemoryRecord]:
        with self._connect() as conn:
            return [r for r in self._latest_all(conn) if r.source_id == source_id]

    def find_by_domain(self, domain: str) -> list[MemoryRecord]:
        with self._connect() as conn:
            return [r for r in self._latest_all(conn) if r.domain == domain]

    def find_by_time_range(
        self, *, start: float, end: float, field: str = "observed_at"
    ) -> list[MemoryRecord]:
        if field not in {"observed_at", "created_at"}:
            raise ValueError("field must be observed_at or created_at")
        with self._connect() as conn:
            out = []
            for r in self._latest_all(conn):
                ts = r.observed_at if field == "observed_at" else r.created_at
                if ts is None:
                    continue
                if start <= ts <= end:
                    out.append(r)
            return out

    def find_by_hypothesis(self, hypothesis_id: str) -> list[MemoryRecord]:
        with self._connect() as conn:
            return [r for r in self._latest_all(conn) if r.hypothesis_id == hypothesis_id]

    def find_by_experiment(self, experiment_id: str) -> list[MemoryRecord]:
        with self._connect() as conn:
            return [r for r in self._latest_all(conn) if r.experiment_id == experiment_id]

    def find_by_agent(
        self, agent_id: str, *, allow_cross_namespace: bool = False
    ) -> list[MemoryRecord]:
        """Default: only that agent's namespace. Shared (empty ns) is not included."""
        with self._connect() as conn:
            rows = self._latest_all(conn)
            if allow_cross_namespace:
                return list(rows)
            return [r for r in rows if r.agent_namespace == agent_id]

    def find_failures(
        self,
        *,
        failure_type: str | None = None,
        component: str | None = None,
        fingerprint: str | None = None,
    ) -> list[MemoryRecord]:
        with self._connect() as conn:
            rows = [r for r in self._latest_all(conn) if r.memory_type == MemoryType.FAILURE.value]
            if fingerprint:
                rows = [r for r in rows if r.payload.get("fingerprint") == fingerprint]
            if failure_type:
                rows = [r for r in rows if r.payload.get("failure_type") == failure_type]
            if component:
                rows = [r for r in rows if r.payload.get("component") == component]
            return rows

    def failure_stats(self, fingerprint: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM failure_stats WHERE fingerprint=?", (fingerprint,)
            ).fetchone()
            return dict(row) if row else None

    def find_contradictions(self, memory_id: str | None = None) -> list[MemoryEdge]:
        with self._connect() as conn:
            if memory_id:
                rows = conn.execute(
                    """SELECT * FROM memory_edges
                       WHERE relation=? AND (from_id=? OR to_id=?)""",
                    (EdgeRelation.CONTRADICTS.value, memory_id, memory_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM memory_edges WHERE relation=?",
                    (EdgeRelation.CONTRADICTS.value,),
                ).fetchall()
            return [
                MemoryEdge(
                    edge_id=r["edge_id"],
                    from_id=r["from_id"],
                    to_id=r["to_id"],
                    relation=r["relation"],
                    reason=r["reason"],
                    created_at=float(r["created_at"]),
                    resolution=r["resolution"],
                    resolved_at=None if r["resolved_at"] is None else float(r["resolved_at"]),
                    resolver=r["resolver"] or "",
                )
                for r in rows
            ]

    def find_supporting_memories(self, memory_id: str) -> list[MemoryRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT from_id, to_id FROM memory_edges WHERE relation=? AND (from_id=? OR to_id=?)",
                (EdgeRelation.SUPPORTS.value, memory_id, memory_id),
            ).fetchall()
            ids: set[str] = set()
            for r in rows:
                ids.add(r["from_id"])
                ids.add(r["to_id"])
            ids.discard(memory_id)
        out: list[MemoryRecord] = []
        for i in sorted(ids):
            rec = self.get(i)
            if rec is not None:
                out.append(rec)
        return out

    def find_related_memories(self, memory_id: str) -> list[MemoryRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT from_id, to_id FROM memory_edges WHERE from_id=? OR to_id=?",
                (memory_id, memory_id),
            ).fetchall()
            ids: set[str] = set()
            for r in rows:
                ids.add(r["from_id"])
                ids.add(r["to_id"])
            ids.discard(memory_id)
        out: list[MemoryRecord] = []
        for i in sorted(ids):
            rec = self.get(i)
            if rec is not None:
                out.append(rec)
        return out

    def recent(self, limit: int = 20) -> list[MemoryRecord]:
        with self._connect() as conn:
            rows = self._latest_all(conn)
            rows.sort(key=lambda r: (r.created_at, r.memory_id), reverse=True)
            return rows[: max(0, int(limit))]

    def relevant_context(
        self,
        *,
        session_id: str = "",
        hypothesis_id: str = "",
        experiment_id: str = "",
        agent_id: str = "",
        limit: int = 20,
        now: float | None = None,
    ) -> list[MemoryRecord]:
        """Deterministic context assembly. Not embedding similarity."""
        ts = time.time() if now is None else now
        with self._connect() as conn:
            rows = self._latest_all(conn)
        scored: list[tuple[int, str, MemoryRecord]] = []
        for r in rows:
            if agent_id and r.agent_namespace and r.agent_namespace != agent_id:
                continue
            rank = 0
            if session_id and r.session_id == session_id:
                rank += 8
                if r.memory_type == MemoryType.WORKING.value:
                    rank += 4
                    if r.expires_at is not None and r.expires_at < ts:
                        rank -= 3
            if hypothesis_id and r.hypothesis_id == hypothesis_id:
                rank += 6
            if experiment_id and r.experiment_id == experiment_id:
                rank += 5
            if r.memory_type == MemoryType.FAILURE.value:
                rank += 2
            if rank <= 0:
                continue
            scored.append((rank, r.memory_id, r))
        scored.sort(key=lambda t: (-t[0], t[1]))
        return [t[2] for t in scored[: max(0, int(limit))]]

    def contradict(
        self, a_id: str, b_id: str, *, reason: str, now: float | None = None
    ) -> MemoryEdge:
        if a_id == b_id:
            raise ValueError("a memory cannot contradict itself")
        if self.get(a_id) is None or self.get(b_id) is None:
            raise KeyError("both memory ids must exist")
        ts = time.time() if now is None else now
        with self._connect() as conn:
            edge = self._insert_edge(
                conn,
                from_id=a_id,
                to_id=b_id,
                relation=EdgeRelation.CONTRADICTS,
                reason=reason,
                created_at=ts,
            )
            conn.commit()
        self.revise(
            a_id,
            contradiction_state=ContradictionState.CONTESTED,
            correction_reason="contradiction_edge",
            now=ts,
        )
        self.revise(
            b_id,
            contradiction_state=ContradictionState.CONTESTED,
            correction_reason="contradiction_edge",
            now=ts,
        )
        return edge

    def support(
        self, a_id: str, b_id: str, *, reason: str, now: float | None = None
    ) -> MemoryEdge:
        ts = time.time() if now is None else now
        with self._connect() as conn:
            edge = self._insert_edge(
                conn,
                from_id=a_id,
                to_id=b_id,
                relation=EdgeRelation.SUPPORTS,
                reason=reason,
                created_at=ts,
            )
            conn.commit()
        self.revise(
            a_id,
            contradiction_state=ContradictionState.SUPPORTED,
            correction_reason="support_edge",
            now=ts,
        )
        return edge

    def resolve_contradiction(
        self,
        edge_id: str,
        *,
        resolver: str,
        now: float | None = None,
    ) -> MemoryEdge:
        """Mark the conflict resolved. Does not delete either memory."""
        ts = time.time() if now is None else now
        if not resolver.strip() or resolver.strip().upper() == UNKNOWN:
            raise InvalidProvenanceError("resolver required (not UNKNOWN)")
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM memory_edges WHERE edge_id=?", (edge_id,)
            ).fetchone()
            if row is None:
                raise KeyError(edge_id)
            conn.execute(
                """UPDATE memory_edges
                   SET resolution=?, resolved_at=?, resolver=?
                   WHERE edge_id=?""",
                (EdgeResolution.RESOLVED.value, ts, resolver, edge_id),
            )
            conn.commit()
            a_id, b_id = row["from_id"], row["to_id"]
        self.revise(
            a_id,
            contradiction_state=ContradictionState.RESOLVED,
            correction_reason=f"resolved:{edge_id}",
            now=ts,
        )
        self.revise(
            b_id,
            contradiction_state=ContradictionState.RESOLVED,
            correction_reason=f"resolved:{edge_id}",
            now=ts,
        )
        latest = self.find_contradictions()
        return next(e for e in latest if e.edge_id == edge_id)

    def supersede(
        self,
        old_id: str,
        *,
        statement: str,
        correction_reason: str,
        producer: str,
        now: float | None = None,
        epistemic_kind: EpistemicKind | str | None = None,
    ) -> MemoryRecord:
        """New memory supersedes old. Old remains queryable as SUPERSEDED."""
        ts = time.time() if now is None else now
        old = self.get(old_id)
        if old is None:
            raise KeyError(old_id)
        kind = epistemic_kind or old.epistemic_kind
        payload = dict(old.payload)
        payload.pop("observation_grant", None)
        successor = self.remember(
            memory_type=old.memory_type,
            epistemic_kind=kind,
            statement=statement,
            source_type=old.source_type,
            source_id=old.source_id,
            source_location=old.source_location,
            producer=producer,
            producer_version=old.producer_version,
            domain=old.domain,
            context=old.context,
            confidence=old.confidence,
            observed_at=old.observed_at,
            created_at=ts,
            payload=payload,
            hypothesis_id=old.hypothesis_id,
            experiment_id=old.experiment_id,
            outcome_link=old.outcome_link,
            agent_id=old.agent_id,
            agent_namespace=old.agent_namespace,
            prediction_id=old.prediction_id,
            derived_from=[old_id],
            supersedes=old_id,
        )
        self.revise(
            old_id,
            status=DecayState.SUPERSEDED,
            contradiction_state=ContradictionState.SUPERSEDED,
            correction_reason=correction_reason,
            now=ts,
        )
        with self._connect() as conn:
            self._insert_edge(
                conn,
                from_id=successor.memory_id,
                to_id=old_id,
                relation=EdgeRelation.SUPERSEDES,
                reason=correction_reason,
                created_at=ts,
            )
            conn.commit()
        return successor

    def apply_decay(self, *, now: float | None = None) -> list[str]:
        """Mark AGING/STALE. Never deletes historical rows."""
        ts = time.time() if now is None else now
        changed: list[str] = []
        with self._connect() as conn:
            latest = self._latest_all(conn)
        for rec in latest:
            if rec.status in {DecayState.SUPERSEDED.value, DecayState.ARCHIVED.value}:
                continue
            new_status = None
            if rec.expires_at is not None and ts >= rec.expires_at:
                new_status = DecayState.STALE
            elif rec.valid_until is not None and ts >= rec.valid_until:
                new_status = DecayState.STALE
            elif rec.valid_until is not None and ts >= rec.valid_until - max(
                1.0, (rec.valid_until - (rec.valid_from or rec.created_at)) * 0.2
            ):
                new_status = DecayState.AGING
            if new_status and rec.status != new_status.value:
                self.revise(rec.memory_id, status=new_status, correction_reason="decay_policy", now=ts)
                changed.append(rec.memory_id)
        return changed

    def record_failure(
        self,
        *,
        failure_type: str,
        component: str,
        attempted_action: str,
        observed_failure: str,
        probable_cause: str = UNKNOWN,
        confidence: float | None = None,
        recovery: str = UNKNOWN,
        recovery_worked: bool | None = None,
        hypothesis_id: str = "",
        experiment_id: str = "",
        agent_id: str = "",
        now: float | None = None,
        producer: str = "architecture.cognitive.memory",
    ) -> MemoryRecord:
        ts = time.time() if now is None else now
        fp = hashlib.sha256(
            f"{failure_type}|{component}|{observed_failure}".encode("utf-8")
        ).hexdigest()[:16]
        rec = self.remember(
            memory_type=MemoryType.FAILURE,
            epistemic_kind=EpistemicKind.OBSERVED_FACT,
            statement=observed_failure,
            source_type=SourceType.SYSTEM,
            source_id=component or UNKNOWN,
            source_location="architecture.cognitive.memory.record_failure",
            producer=producer,
            producer_version="p2-v1",
            domain="COGNITIVE_CORE",
            context=attempted_action or UNKNOWN,
            confidence=confidence,
            created_at=ts,
            observed_at=ts,
            hypothesis_id=hypothesis_id,
            experiment_id=experiment_id,
            agent_id=agent_id,
            agent_namespace=agent_id,
            payload={
                "failure_type": failure_type,
                "component": component,
                "attempted_action": attempted_action,
                "observed_failure": observed_failure,
                "probable_cause": probable_cause or UNKNOWN,
                "recovery": recovery or UNKNOWN,
                "recovery_worked": recovery_worked,
                "fingerprint": fp,
            },
        )
        with self._connect() as conn:
            existing = conn.execute(
                "SELECT * FROM failure_stats WHERE fingerprint=?", (fp,)
            ).fetchone()
            if existing is None:
                conn.execute(
                    """INSERT INTO failure_stats(
                         fingerprint, failure_type, component, recurrence_count,
                         first_memory_id, last_memory_id, last_occurrence
                       ) VALUES (?,?,?,?,?,?,?)""",
                    (fp, failure_type, component, 1, rec.memory_id, rec.memory_id, ts),
                )
            else:
                conn.execute(
                    """UPDATE failure_stats SET recurrence_count=?, last_memory_id=?, last_occurrence=?
                       WHERE fingerprint=?""",
                    (int(existing["recurrence_count"]) + 1, rec.memory_id, ts, fp),
                )
            conn.commit()
        return rec

    def record_world_model_object(
        self,
        *,
        object_kind: str,
        statement: str,
        epistemic_kind: EpistemicKind | str = EpistemicKind.INFERENCE,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> MemoryRecord:
        kind = str(object_kind).strip().upper()
        if kind not in WORLD_MODEL_OBJECT_KINDS:
            raise ValueError(f"unknown world-model object kind {object_kind!r}")
        resolved = EpistemicKind(epistemic_kind).value
        if resolved == EpistemicKind.OBSERVED_FACT.value:
            raise ValueError(
                "record_world_model_object cannot persist OBSERVED_FACT"
            )
        body = dict(payload or {})
        body["object_kind"] = kind
        return self.remember(
            memory_type=MemoryType.WORLD_MODEL,
            epistemic_kind=epistemic_kind,
            statement=statement,
            payload=body,
            **kwargs,
        )

    def authorize_execution(self, *_args: Any, **_kwargs: Any) -> None:
        raise MemoryAuthorizationError(
            "Cognitive memory cannot authorize execution, trading, or self-modification"
        )

    def authorize_trading(self, *_args: Any, **_kwargs: Any) -> None:
        self.authorize_execution()

    def elevate_autonomy(self, *_args: Any, **_kwargs: Any) -> None:
        raise MemoryAuthorizationError("Cognitive memory cannot elevate autonomy")
