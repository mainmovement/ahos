#!/usr/bin/env python3
"""M42 — bind the frozen paper store into the single hash-chained ledger.

Vision M42 (:1269): *"extend ``architecture/mission/ledger.py`` and
``paper_trading/ledger.py`` (one ledger)"*. The paper store is Lane A and
frozen, so it cannot gain a ``prev_hash`` column — and it does not need one.
The store already refuses every UPDATE and DELETE by trigger
(``paper_trading/schema.sql:95-106``); what it lacks is a *witness*. This
module is that witness: it fingerprints the store's rows and records the
fingerprint on the single hash-chained ledger, so the store becomes a branch
of the one chain instead of a second, unchained one.

The fingerprint is deliberately *prefix-stable*. The store is append-only, so
an anchor binds the rows that existed when it was taken — the first ``n`` rows
of each table in rowid order, which is insertion order for a plain rowid
table. Rows appended afterwards extend the store and the next anchor covers
them; rows edited, deleted, reordered or inserted out of band change the
prefix and break the anchor. That is exactly the asymmetry an append-only
store wants: growth is normal, alteration is not.

Nothing here writes to the paper store and nothing imports Lane A. The store
is opened read-only with the same ``mode=ro`` uri idiom the lab itself uses
for the discovery store (``paper_trading/ledger.py:open_discovery_ro``); the
fingerprint is computed from ``SELECT *`` over a connection that cannot mutate
anything. The direction is one-way, as ``tests/test_mission_ledger.py``'s
import law requires: the chain binds the store, never the reverse.

Verdicts are fail-closed. A store with no anchor on record is ``UNANCHORED``,
not clean — an unchained store is not a chained one, and the reconcile that
reads this verdict says so rather than assuming the best.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from ..mission.ledger import KIND_ANCHOR, LedgerTamperError, MissionLedger

PAPER_STORE_ID = "paper_trading.sqlite"

ANCHORED_CLEAN = "ANCHORED_CLEAN"
ANCHORED_MISMATCH = "ANCHORED_MISMATCH"
UNANCHORED = "UNANCHORED"


@dataclass(frozen=True)
class StoreFingerprint:
    """A content-addressed snapshot of one store's anchored row set."""

    store: str
    tables: dict[str, int] = field(default_factory=dict)
    root_hash: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {"store": self.store, "tables": dict(self.tables),
                "root_hash": self.root_hash}


@dataclass(frozen=True)
class AnchorVerdict:
    """The result of re-witnessing a store against its last recorded anchor.

    ``findings`` are tamper findings only — tables added since the anchor are
    reported separately in ``extensions`` and never make a clean verdict dirty.
    Rows appended to an anchored table do not appear here at all: the anchor
    binds a row-count prefix, so append-only growth leaves that prefix
    untouched and stays clean by construction. That is the asymmetry an
    append-only store wants -- growth is silent, alteration is not.
    """

    state: str
    store: str
    findings: tuple[str, ...] = field(default_factory=tuple)
    extensions: tuple[str, ...] = field(default_factory=tuple)
    fingerprint: StoreFingerprint | None = None
    anchored: StoreFingerprint | None = None
    anchor_hash: str | None = None

    @property
    def clean(self) -> bool:
        return self.state == ANCHORED_CLEAN


# ------------------------------------------------------------------ reading --

def open_store_ro(path: str | Path) -> sqlite3.Connection:
    """Open a store read-only. A uri that cannot be opened raises; it never
    falls back to a writable connection, because an anchor taken through a
    writable handle is not evidence of an untouchable store."""
    conn = sqlite3.connect(f"file:{Path(path).as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _user_tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' AND name NOT LIKE '_meta%' "
        "ORDER BY name").fetchall()
    out: list[str] = []
    for r in rows:
        sql = (r["sql"] or "").upper()
        if "WITHOUT ROWID" in sql:
            # ORDER BY rowid is not defined for such a table, so its rows have
            # no insertion-order prefix to bind. Reported rather than guessed.
            raise ValueError(f"{r['name']}: WITHOUT ROWID tables cannot be anchored "
                             "by rowid prefix; add it to an explicit table list")
        out.append(r["name"])
    return out


def _row_hash(values: Iterable[Any]) -> str:
    body = json.dumps(list(values), sort_keys=True, separators=(",", ":"),
                      default=_json_default)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def _json_default(obj: Any) -> Any:
    if isinstance(obj, bytes):
        return {"__bytes_hex__": obj.hex()}
    if isinstance(obj, float) and obj != obj:          # NaN
        return {"__float__": "nan"}
    if isinstance(obj, float) and obj in (float("inf"), float("-inf")):
        return {"__float__": "inf" if obj > 0 else "-inf"}
    raise TypeError(f"unserialisable value of type {type(obj).__name__}")


def fingerprint_store(conn: sqlite3.Connection, *, store: str,
                      tables: Iterable[str] | None = None,
                      limits: dict[str, int] | None = None) -> StoreFingerprint:
    """Fingerprint ``conn``'s rows.

    ``limits`` pins the anchored prefix per table (``{table: n}``); without it
    the whole table is fingerprinted. The digest is a sha256 over the per-table
    digests in sorted table order, so adding a table later is a new anchor
    rather than a silent change of this one's meaning.
    """
    names = list(tables) if tables is not None else _user_tables(conn)
    limits = limits or {}
    per_table: dict[str, str] = {}
    counts: dict[str, int] = {}
    for name in sorted(names):
        n = limits.get(name)
        sql = f'SELECT * FROM "{name}" ORDER BY rowid'
        args: tuple[Any, ...] = ()
        if n is not None:
            sql += " LIMIT ?"
            args = (int(n),)
        try:
            cur = conn.execute(sql, args)
        except sqlite3.OperationalError as exc:
            raise ValueError(f"{name}: {exc}") from exc
        digester = hashlib.sha256()
        count = 0
        while True:
            rows = cur.fetchmany(4096)
            if not rows:
                break
            for row in rows:
                digester.update(_row_hash(tuple(row)).encode("ascii"))
                count += 1
        per_table[name] = digester.hexdigest()
        counts[name] = count
    root = hashlib.sha256(
        json.dumps({"store": store, "tables": per_table},
                   sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return StoreFingerprint(store=store, tables=counts, root_hash=root)


# ------------------------------------------------------------------ writing --

def anchor_store(ledger: MissionLedger, conn: sqlite3.Connection, *,
                 store: str, agent: str | None = None,
                 tables: Iterable[str] | None = None) -> StoreFingerprint:
    """Record the store's current fingerprint on the single ledger.

    The anchor is taken over the *whole* store, so the first anchor binds
    everything that exists; later anchors bind the extension, and
    ``verify_anchor`` checks the earlier prefix against the live rows.
    """
    fp = fingerprint_store(conn, store=store, tables=tables)
    ledger.record(KIND_ANCHOR, fp.to_payload(), agent=agent)
    return fp


def verify_anchor(ledger: MissionLedger, conn: sqlite3.Connection, *,
                  store: str) -> AnchorVerdict:
    """Re-witness the store against the last anchor recorded for it.

    Recomputes the fingerprint over the *anchored prefix* — the row counts the
    anchor recorded — and compares it with the recorded digest. A table the
    anchor covered that no longer exists is a mismatch, not a clean pass; a
    table added since is reported as an extension (it is growth, and the next
    anchor covers it).
    """
    try:
        rows = ledger.evidence(KIND_ANCHOR)
    except LedgerTamperError as exc:
        return AnchorVerdict(ANCHORED_MISMATCH, store,
                             findings=(f"the chain cannot be verified: {exc}",))
    last = None
    for row in rows:
        payload = row.get("payload") or {}
        if payload.get("store") == store:
            last = row
    if last is None:
        return AnchorVerdict(UNANCHORED, store,
                             findings=(f"no anchor on record for {store}; "
                                       "the store is not yet bound to the chain",))
    payload = last.get("payload") or {}
    anchored = StoreFingerprint(store=store, tables=dict(payload.get("tables") or {}),
                                root_hash=str(payload.get("root_hash") or ""))
    live_tables = _user_tables(conn)
    findings: list[str] = []
    for name, n in anchored.tables.items():
        if name not in live_tables:
            findings.append(f"table {name} was anchored with {n} rows and no longer exists")
    try:
        fp = fingerprint_store(conn, store=store, tables=sorted(anchored.tables),
                               limits=anchored.tables)
    except ValueError as exc:
        findings.append(str(exc))
        return AnchorVerdict(ANCHORED_MISMATCH, store, findings=tuple(findings),
                             anchored=anchored, anchor_hash=last.get("entry_hash"))
    if fp.root_hash != anchored.root_hash:
        for name in sorted(anchored.tables):
            live = fp.tables.get(name)
            if live is None:
                continue          # already reported as a missing table above
            if live != anchored.tables.get(name):
                findings.append(f"table {name}: the anchored prefix of "
                                f"{anchored.tables[name]} rows changed (now {live} rows "
                                "in that prefix — edited, deleted or reordered)")
        if not findings:
            findings.append(f"root hash mismatch: anchored {anchored.root_hash}, "
                            f"recomputed {fp.root_hash}")
    extensions = tuple(sorted(set(live_tables) - set(anchored.tables)))
    state = ANCHORED_CLEAN if not findings else ANCHORED_MISMATCH
    return AnchorVerdict(state, store, findings=tuple(findings), extensions=extensions,
                         fingerprint=fp, anchored=anchored,
                         anchor_hash=last.get("entry_hash"))


# ------------------------------------------------------------- the paper leg --

def open_paper_ro(path: str | Path | None = None) -> sqlite3.Connection:
    """The frozen paper store, opened read-only.

    ``path`` defaults to the store the lab itself uses, resolved through the
    project's own data dir so an ``AHOS_DATA_DIR`` override is honoured. Read
    only: the anchor never writes to Lane A.
    """
    if path is None:
        from config.paths import get_db_path
        path = get_db_path("paper_trading")
    return open_store_ro(path)


def anchor_paper_store(ledger: MissionLedger, *, agent: str | None = None,
                       path: str | Path | None = None) -> StoreFingerprint:
    conn = open_paper_ro(path)
    try:
        return anchor_store(ledger, conn, store=PAPER_STORE_ID, agent=agent)
    finally:
        conn.close()


def verify_paper_anchor(ledger: MissionLedger, *,
                        path: str | Path | None = None) -> AnchorVerdict:
    conn = open_paper_ro(path)
    try:
        return verify_anchor(ledger, conn, store=PAPER_STORE_ID)
    finally:
        conn.close()
