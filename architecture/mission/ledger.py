"""Append-only, hash-chained mission/engineering ledger (GM-08).

What it is
----------
A local-first JSONL file (default ``<AHOS data dir>/mission_ledger/mission_ledger.jsonl``),
separate from every decision/evidence/paper SQLite store. Each line is a full
snapshot of one mission's state after a change. The state carries these fields:

    MISSION_ID, CURRENT_PHASE, CURRENT_TASK, TASK_STATUS, CURRENT_AGENT,
    LAST_EVIDENCE, LAST_TEST, LAST_VERIFICATION, LAST_COMMIT, CURRENT_BLOCKER,
    NEXT_ACTION, AI_PROVIDER, CHECKPOINT

Each line is linked to the previous one by ``prev_hash``/``entry_hash`` (sha256 over
canonical JSON, the same convention as ``ahos_org.audit``), so edits, deletions and
reordering are detected by ``verify()``.

What it is NOT
--------------
* Not a decision authority. It grants nothing, unlocks no gate, and is imported by
  no trading/decision code (pinned by tests).
* Not a secret store. Secret-looking strings are redacted before hashing, so they
  never reach disk. In ``strict`` mode they are rejected instead.
* There is deliberately no COMPLETED/DONE state. Work ends at COMPLETED_UNVERIFIED.
  Verification is recorded separately in LAST_VERIFICATION, by someone else.

Resume, never restart
---------------------
``start()`` refuses an existing mission id. ``resume()`` re-opens the latest
checkpoint (from PAUSED / WAIT_FOR_AI / BLOCKED, or RUNNING after a crash) and
returns it unchanged. A torn final line left by a crash mid-write is
detected. Appending is refused until ``recover_torn_tail()`` writes an explicit,
hashed recovery entry that names the torn line's sha256. Nothing is rewritten.

Single writer per file. Times are UTC ISO-8601.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Iterable

SCHEMA = "ahos.mission_ledger.v1"
GENESIS_HASH = "0" * 64
AGENT_TAXONOMY_REF = "docs/governance/agent_taxonomy_map.json"
MAX_CHECKPOINT_BYTES = 64 * 1024
MAX_TEXT_LEN = 4000

FIELDS = (
    "MISSION_ID",
    "CURRENT_PHASE",
    "CURRENT_TASK",
    "TASK_STATUS",
    "CURRENT_AGENT",
    "LAST_EVIDENCE",
    "LAST_TEST",
    "LAST_VERIFICATION",
    "LAST_COMMIT",
    "CURRENT_BLOCKER",
    "NEXT_ACTION",
    "AI_PROVIDER",
    "CHECKPOINT",
)
UPDATABLE = tuple(f for f in FIELDS if f not in ("MISSION_ID", "TASK_STATUS"))


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    WAIT_FOR_AI = "WAIT_FOR_AI"
    BLOCKED = "BLOCKED"
    RESUMED = "RESUMED"
    COMPLETED_UNVERIFIED = "COMPLETED_UNVERIFIED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


_S = TaskStatus
TERMINAL = frozenset({_S.COMPLETED_UNVERIFIED, _S.CANCELLED})
_INTERRUPTED = frozenset({_S.PAUSED, _S.WAIT_FOR_AI, _S.BLOCKED})
LEGAL_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    _S.PENDING: frozenset({_S.PENDING, _S.RUNNING, _S.BLOCKED, _S.CANCELLED}),
    _S.RUNNING: frozenset({_S.RUNNING, _S.PAUSED, _S.WAIT_FOR_AI, _S.BLOCKED,
                           _S.COMPLETED_UNVERIFIED, _S.FAILED, _S.CANCELLED,
                           _S.RESUMED}),                # RESUMED = crash recovery
    _S.PAUSED: frozenset({_S.PAUSED, _S.RESUMED, _S.CANCELLED}),
    _S.WAIT_FOR_AI: frozenset({_S.WAIT_FOR_AI, _S.RESUMED, _S.PAUSED, _S.CANCELLED}),
    _S.BLOCKED: frozenset({_S.BLOCKED, _S.RESUMED, _S.CANCELLED}),
    _S.RESUMED: frozenset({_S.RUNNING, _S.PAUSED, _S.WAIT_FOR_AI, _S.BLOCKED,
                           _S.CANCELLED}),
    _S.FAILED: frozenset({_S.RESUMED, _S.CANCELLED}),
    _S.COMPLETED_UNVERIFIED: frozenset(),
    _S.CANCELLED: frozenset(),
}


class LedgerError(Exception):
    pass


class LedgerTamperError(LedgerError):
    pass


class LedgerTransitionError(LedgerError):
    pass


class MissionExistsError(LedgerError):
    pass


class MissionNotFoundError(LedgerError):
    pass


class SecretRejectedError(LedgerError):
    pass


# ------------------------------------------------------------------ secrets --

_SECRET_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("PRIVATE_KEY_BLOCK", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?(-----END [A-Z0-9 ]*PRIVATE KEY-----|$)", re.S)),
    ("TELEGRAM_BOT_TOKEN", re.compile(r"\b\d{8,12}:[A-Za-z0-9_-]{30,50}\b")),
    ("ANTHROPIC_KEY", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{16,}")),
    ("OPENAI_STYLE_KEY", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{16,}")),
    ("XAI_KEY", re.compile(r"\bxai-[A-Za-z0-9]{16,}")),
    ("GROQ_KEY", re.compile(r"\bgsk_[A-Za-z0-9]{20,}")),
    ("GITHUB_TOKEN", re.compile(r"\b(?:ghp|gho|ghs|ghu|github_pat)_[A-Za-z0-9_]{20,}")),
    ("GOOGLE_API_KEY", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}")),
    ("AWS_ACCESS_KEY", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("SLACK_TOKEN", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
    ("EVM_PRIVATE_KEY", re.compile(r"\b0x[0-9a-fA-F]{64}\b")),
    ("URL_CREDENTIALS", re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)[^/\s:@]+:[^/\s@]+@")),
    ("BEARER", re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{12,}")),
    ("ASSIGNED_SECRET", re.compile(
        r"(?i)\b([A-Z0-9_]*(?:api[_-]?key|secret|token|passw(?:or)?d|pwd|private[_-]?key|access[_-]?key|credential)[A-Z0-9_]*)"
        r"(\s*[:=]\s*)(['\"]?)(?!\[REDACTED)([^\s'\",;]{6,})")),
)


def _redact_text(text: str) -> tuple[str, list[str]]:
    hits: list[str] = []
    out = text
    for kind, pat in _SECRET_RULES:
        def _sub(m: re.Match[str], kind: str = kind) -> str:
            hits.append(kind)
            if kind == "ASSIGNED_SECRET":
                return f"{m.group(1)}{m.group(2)}{m.group(3)}[REDACTED:{kind}]"
            if kind == "URL_CREDENTIALS":
                return f"{m.group(1)}[REDACTED:{kind}]@"
            return f"[REDACTED:{kind}]"
        out = pat.sub(_sub, out)
    return out, hits


def redact_secrets(value: Any) -> tuple[Any, list[str]]:
    """Recursively redact secret-looking substrings (keys and values). Returns (clean, kinds)."""
    kinds: list[str] = []

    def walk(v: Any) -> Any:
        if isinstance(v, str):
            clean, hits = _redact_text(v)
            kinds.extend(hits)
            return clean
        if isinstance(v, dict):
            out = {}
            for k, sub in v.items():
                ck, hits = _redact_text(str(k))
                kinds.extend(hits)
                out[ck] = walk(sub)
            return out
        if isinstance(v, (list, tuple)):
            return [walk(x) for x in v]
        return v

    return walk(value), kinds


# ------------------------------------------------------------------ helpers --

def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _acknowledges(next_line: str, line: str) -> bool:
    """True when next_line is a recovery entry naming `line` as the torn tail."""
    if '"TORN_TAIL_RECOVERED"' not in next_line:
        return False
    try:
        rec = json.loads(next_line)
    except ValueError:
        return False
    return (isinstance(rec, dict) and rec.get("kind") == "TORN_TAIL_RECOVERED"
            and rec.get("torn_line_sha256") == _sha(line))


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


_AGENT_RE = re.compile(r"^(engineering|agent\.org|agent|AG|AGENT|M0):[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_MISSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,79}$")


def validate_agent(agent: str | None) -> str | None:
    """CURRENT_AGENT must carry its taxonomy namespace (no bare 'agent 01')."""
    if agent in (None, ""):
        return None
    if not isinstance(agent, str) or not _AGENT_RE.match(agent):
        raise LedgerError(
            "CURRENT_AGENT must be '<namespace>:<id>' with namespace in "
            "engineering|agent|AG|AGENT|agent.org|M0 (see "
            f"{AGENT_TAXONOMY_REF}; taxonomies are reconciled, not merged)")
    return agent


def default_ledger_path(create: bool = False) -> Path:
    """<AHOS data dir>/mission_ledger/mission_ledger.jsonl (never an existing DB)."""
    try:
        from config.paths import get_data_dir
        base = Path(get_data_dir(create=create))
    except Exception:  # noqa: BLE001 - config optional for this tool
        base = Path(__file__).resolve().parents[2] / "data"
    return base / "mission_ledger" / "mission_ledger.jsonl"


# ------------------------------------------------------------------- ledger --

class MissionLedger:
    """Append-only mission ledger. Not an authority; see module docstring."""

    def __init__(self, path: str | Path, *, strict: bool = False,
                 clock: Callable[[], str] = _utc_now) -> None:
        self.path = Path(path)
        if self.path.suffix.lower() in (".sqlite", ".db", ".sqlite3"):
            raise LedgerError("mission ledger is JSONL; refusing a database path")
        self.strict = strict
        self._clock = clock

    # ---- reading -------------------------------------------------------
    def _read_lines(self) -> list[str]:
        if not self.path.is_file():
            return []
        data = self.path.read_bytes().decode("utf-8", errors="replace")
        return data.split("\n")

    def _scan(self) -> dict[str, Any]:
        """Parse + verify. Returns entries, torn tail info. Raises on tamper."""
        lines = self._read_lines()
        torn_tail = None
        if lines and lines[-1] != "":
            torn_tail = lines[-1]          # no trailing newline = interrupted write
        body = lines[:-1] if lines else []
        entries: list[dict[str, Any]] = []
        prev = GENESIS_HASH
        pending_torn: str | None = None
        for lineno, line in enumerate(body, start=1):
            if line == "":
                raise LedgerTamperError(f"line {lineno}: blank line inside ledger")
            if pending_torn is None and lineno < len(body) and _acknowledges(body[lineno], line):
                pending_torn = _sha(line)       # a complete-looking line cut before its newline
                continue
            try:
                rec = json.loads(line)
                if not isinstance(rec, dict):
                    raise ValueError("not an object")
            except ValueError:
                if pending_torn is not None:
                    raise LedgerTamperError(f"line {lineno}: unparseable line")
                pending_torn = _sha(line)
                continue
            if pending_torn is not None:
                if rec.get("kind") != "TORN_TAIL_RECOVERED" or rec.get("torn_line_sha256") != pending_torn:
                    raise LedgerTamperError(
                        f"line {lineno}: unparseable line before it is not an acknowledged torn tail")
                pending_torn = None
            if rec.get("schema") != SCHEMA:
                raise LedgerTamperError(f"line {lineno}: unknown schema")
            if rec.get("seq") != len(entries):
                raise LedgerTamperError(f"line {lineno}: sequence break (expected {len(entries)}, got {rec.get('seq')})")
            if rec.get("prev_hash") != prev:
                raise LedgerTamperError(f"line {lineno}: prev_hash mismatch (deleted, inserted or reordered entry)")
            claimed = rec.get("entry_hash")
            body_rec = {k: v for k, v in rec.items() if k != "entry_hash"}
            if claimed != _sha(canonical_json(body_rec)):
                raise LedgerTamperError(f"line {lineno}: entry_hash mismatch (entry was modified)")
            prev = claimed
            entries.append(rec)
        if pending_torn is not None:
            raise LedgerTamperError("unparseable line inside ledger without recovery entry")
        return {"entries": entries, "torn_tail": torn_tail, "head": prev}

    def verify(self, anchor_hash: str | None = None) -> dict[str, Any]:
        """Full chain verification. Raises LedgerTamperError on any break.

        A keyless hash chain detects edits, deletions and reordering, but someone who
        rewrites the WHOLE file can recompute every hash. Record ``head_hash``
        somewhere outside the file (handoff doc, commit message). Passing it back as
        ``anchor_hash`` proves that the history up to that point is unchanged.
        """
        s = self._scan()
        if anchor_hash is not None and anchor_hash not in {e["entry_hash"] for e in s["entries"]}:
            raise LedgerTamperError("anchor hash not found: history before the anchor was rewritten")
        return {
            "schema": SCHEMA,
            "path": str(self.path),
            "entries": len(s["entries"]),
            "head_hash": s["head"],
            "torn_tail": s["torn_tail"] is not None,
            "verdict": "CHAIN_INTACT_TORN_TAIL" if s["torn_tail"] is not None else "CHAIN_INTACT",
        }

    def entries(self) -> list[dict[str, Any]]:
        return self._scan()["entries"]

    def history(self, mission_id: str) -> list[dict[str, Any]]:
        return [e for e in self.entries() if e.get("kind") == "STATE" and e["state"]["MISSION_ID"] == mission_id]

    def latest(self, mission_id: str) -> dict[str, Any] | None:
        h = self.history(mission_id)
        return copy.deepcopy(h[-1]["state"]) if h else None

    def missions(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for e in self.entries():
            if e.get("kind") == "STATE":
                out[e["state"]["MISSION_ID"]] = e["state"]["TASK_STATUS"]
        return out

    # ---- writing -------------------------------------------------------
    def _append(self, record: dict[str, Any], *, _torn_recovery: bool = False) -> dict[str, Any]:
        s = self._scan()
        prefix = b""
        if s["torn_tail"] is not None:
            if not _torn_recovery:
                raise LedgerError("ledger has a torn final line (interrupted write); "
                                  "call recover_torn_tail() first - nothing is rewritten")
            prefix = b"\n"                    # terminate the torn line; never rewrite it
        record = {"schema": SCHEMA, "seq": len(s["entries"]), "ts": self._clock(),
                  **record, "prev_hash": s["head"]}
        record["entry_hash"] = _sha(canonical_json(record))
        line = prefix + (canonical_json(record) + "\n").encode("utf-8")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(self.path), os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0), 0o600)
        try:
            os.write(fd, line)
            os.fsync(fd)
        finally:
            os.close(fd)
        return record

    def recover_torn_tail(self, *, agent: str | None = None, note: str = "") -> dict[str, Any]:
        s = self._scan()
        if s["torn_tail"] is None:
            raise LedgerError("no torn tail to recover")
        clean_note, kinds = redact_secrets(note[:MAX_TEXT_LEN])
        return self._append({"kind": "TORN_TAIL_RECOVERED", "torn_line_sha256": _sha(s["torn_tail"]),
                             "agent": validate_agent(agent), "note": clean_note,
                             "redactions": sorted(set(kinds))}, _torn_recovery=True)

    def _clean(self, values: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
        clean, kinds = redact_secrets(values)
        if kinds and self.strict:
            raise SecretRejectedError(f"secret-looking content rejected ({sorted(set(kinds))}); nothing written")
        for k, v in clean.items():
            if isinstance(v, str) and len(v) > MAX_TEXT_LEN:
                clean[k] = v[:MAX_TEXT_LEN] + "...[TRUNCATED]"
        if "CHECKPOINT" in clean and clean["CHECKPOINT"] is not None:
            try:
                size = len(canonical_json(clean["CHECKPOINT"]))
            except (TypeError, ValueError) as exc:
                raise LedgerError(f"CHECKPOINT must be JSON-serialisable: {exc}") from exc
            if size > MAX_CHECKPOINT_BYTES:
                raise LedgerError(f"CHECKPOINT too large ({size} > {MAX_CHECKPOINT_BYTES} bytes)")
        return clean, kinds

    def _write_state(self, state: dict[str, Any], event: str, kinds: Iterable[str]) -> dict[str, Any]:
        rec = self._append({"kind": "STATE", "event": event, "state": state,
                            "agent_taxonomy_ref": AGENT_TAXONOMY_REF,
                            "redactions": sorted(set(kinds)), "authority": "NONE"})
        return copy.deepcopy(rec["state"])

    def start(self, mission_id: str, *, phase: str, task: str, agent: str,
              status: TaskStatus | str = TaskStatus.RUNNING, **fields: Any) -> dict[str, Any]:
        if not isinstance(mission_id, str) or not _MISSION_RE.match(mission_id):
            raise LedgerError("invalid MISSION_ID")
        if redact_secrets(mission_id)[1]:
            raise SecretRejectedError("MISSION_ID looks like a secret; refused")
        if self.latest(mission_id) is not None:
            raise MissionExistsError(f"{mission_id} already exists - resume() it, never restart from zero")
        status = TaskStatus(status)
        if status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            raise LedgerTransitionError("a mission starts PENDING or RUNNING")
        unknown = set(fields) - set(UPDATABLE)
        if unknown:
            raise LedgerError(f"unknown fields: {sorted(unknown)}")
        state = {f: None for f in FIELDS}
        state.update(fields)
        state.update({"MISSION_ID": mission_id, "CURRENT_PHASE": phase, "CURRENT_TASK": task,
                      "CURRENT_AGENT": validate_agent(agent), "TASK_STATUS": status.value})
        clean, kinds = self._clean(state)
        clean["MISSION_ID"] = mission_id
        return self._write_state(clean, "START", kinds)

    def update(self, mission_id: str, *, status: TaskStatus | str | None = None,
               event: str = "UPDATE", **fields: Any) -> dict[str, Any]:
        cur = self.latest(mission_id)
        if cur is None:
            raise MissionNotFoundError(mission_id)
        unknown = set(fields) - set(UPDATABLE)
        if unknown:
            raise LedgerError(f"unknown fields: {sorted(unknown)}")
        old = TaskStatus(cur["TASK_STATUS"])
        new = TaskStatus(status) if status is not None else old
        if new not in LEGAL_TRANSITIONS[old]:
            raise LedgerTransitionError(f"{old.value} -> {new.value} is not a legal transition")
        if "CURRENT_AGENT" in fields:
            validate_agent(fields["CURRENT_AGENT"])
        clean_fields, kinds = self._clean(dict(fields))   # only new input is scanned
        nxt = dict(cur)
        nxt.update(clean_fields)
        nxt["TASK_STATUS"] = new.value
        nxt["MISSION_ID"] = mission_id
        return self._write_state(nxt, event, kinds)

    def checkpoint(self, mission_id: str, checkpoint: Any, **fields: Any) -> dict[str, Any]:
        return self.update(mission_id, event="CHECKPOINT", CHECKPOINT=checkpoint, **fields)

    def pause(self, mission_id: str, *, status: TaskStatus | str = TaskStatus.PAUSED,
              checkpoint: Any = None, **fields: Any) -> dict[str, Any]:
        status = TaskStatus(status)
        if status not in _INTERRUPTED:
            raise LedgerTransitionError("pause() status must be PAUSED, WAIT_FOR_AI or BLOCKED")
        if checkpoint is not None:
            fields["CHECKPOINT"] = checkpoint
        return self.update(mission_id, status=status, event="PAUSE", **fields)

    def resume(self, mission_id: str, *, agent: str | None = None,
               crash_recovery: bool = False, **fields: Any) -> dict[str, Any]:
        """Re-open from the latest checkpoint (returned unchanged). Never restarts from zero."""
        cur = self.latest(mission_id)
        if cur is None:
            raise MissionNotFoundError(f"{mission_id}: nothing to resume")
        st = TaskStatus(cur["TASK_STATUS"])
        if st == TaskStatus.RUNNING and not crash_recovery:
            raise LedgerTransitionError("mission is RUNNING; pass crash_recovery=True after a crash")
        if st not in _INTERRUPTED | {TaskStatus.RUNNING, TaskStatus.FAILED}:
            raise LedgerTransitionError(f"cannot resume from {st.value}")
        if "CHECKPOINT" in fields:
            raise LedgerError("resume() keeps the stored CHECKPOINT; use checkpoint() afterwards")
        if agent is not None:
            fields["CURRENT_AGENT"] = agent
        return self.update(mission_id, status=TaskStatus.RESUMED,
                           event="CRASH_RECOVERY_RESUME" if crash_recovery else "RESUME", **fields)
