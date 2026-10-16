"""Kian hash-chained audit store (M35.1) - simplified version.

Hash-chained audit of every Kian action under data/.
Sпах's conditions: append-only, chained sha256, no secrets redacted before writing.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class KianAuditRecord:
    """Kian action record with hash chain."""
    seq: int
    timestamp: float
    channel: str
    user_id_hash: str
    message_hash: str
    action_type: str
    tool_calls: List[str]
    content: str
    taint_labels: List[str]
    rate_limited: bool
    prev_hash: str
    entry_hash: str


class ChainIntegrityError(Exception):
    """Raised when chain integrity is violated."""
    pass


class AuditStoreError(Exception):
    """Raised when audit store operations fail."""
    pass


class KianAuditStore:
    """Hash-chained audit store for every Kian action."""

    GENESIS_HASH = "0" * 64
    GENESIS_PREV_HASH = "0" * 64

    def __init__(self, path: str | Path, auto_create_genesis: bool = True) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory state for O(1) performance
        self._last_hash = self.GENESIS_HASH
        self._last_seq = 0  # Will be 0 after genesis (seq=0 is genesis)
        self._init_timestamp = time.time()

        if auto_create_genesis:
            self._maybe_create_genesis()

    def _maybe_create_genesis(self) -> None:
        """Create genesis record if file doesn't exist."""
        if self.path.exists() and self.path.stat().st_size > 0:
            # File exists with content - load and verify genesis
            self._load_genesis()
        else:
            # Create genesis file
            self._write_genesis()

    def _content_hash(self, data: dict) -> str:
        """Compute SHA256 hash of a canonical JSON representation."""
        return hashlib.sha256(
            json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

    def _write_genesis(self) -> None:
        """Write genesis record to file."""
        genesis_dict = {
            "seq": 0,
            "timestamp": self._init_timestamp,
            "channel": "system",
            "user_id_hash": "genesis",
            "message_hash": "genesis",
            "action_type": "system",
            "tool_calls": [],
            "content": "genesis audit chain",
            "taint_labels": [],
            "rate_limited": False,
            "prev_hash": self.GENESIS_PREV_HASH,
        }

        entry_hash = self._content_hash(genesis_dict)
        genesis_dict["entry_hash"] = entry_hash

        # Track genesis state for chain integrity
        self._last_hash = entry_hash
        self._last_seq = 0

        try:
            with open(self.path, "w", encoding="utf-8", buffering=1) as f:
                f.write(json.dumps(genesis_dict, ensure_ascii=False) + "\n")
        except OSError as exc:
            raise AuditStoreError(f"Failed to write genesis: {exc}")

    def _load_genesis(self) -> None:
        """Load and verify genesis from existing file."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                line = f.readline().strip()
            data = json.loads(line)
            if data.get("seq") != 0:
                raise AuditStoreError("Invalid genesis record")
            self._last_hash = data["entry_hash"]
            self._last_seq = 0
            self._init_timestamp = data.get("timestamp", time.time())
        except Exception as exc:
            raise AuditStoreError(f"Failed to load genesis: {exc}")

    @property
    def last_seq(self) -> int:
        return self._last_seq

    def record_action(
        self,
        channel: str,
        user_id_hash: str,
        message_hash: str,
        action_type: str,
        tool_calls: List[str],
        content: str,
        taint_labels: List[str],
        rate_limited: bool = False,
    ) -> int:
        """Record a Kian action and return the sequence number."""
        if not self.path.exists():
            raise AuditStoreError("Audit store not initialized")

        seq = self._last_seq + 1
        now = time.time()

        record_dict = {
            "seq": seq,
            "timestamp": now,
            "channel": channel,
            "user_id_hash": user_id_hash,
            "message_hash": message_hash,
            "action_type": action_type,
            "tool_calls": tool_calls,
            "content": content,
            "taint_labels": taint_labels,
            "rate_limited": rate_limited,
            "prev_hash": self._last_hash,
        }

        entry_hash = self._content_hash(record_dict)
        record_dict["entry_hash"] = entry_hash

        try:
            with open(self.path, "a", encoding="utf-8", buffering=1) as f:
                f.write(json.dumps(record_dict, ensure_ascii=False) + "\n")
        except OSError as exc:
            raise AuditStoreError(f"Failed to write record: {exc}")

        self._last_hash = entry_hash
        self._last_seq = seq
        return seq

    def verify_chain(self) -> bool:
        """Verify the chain integrity by reading the file."""
        if not self.path.exists():
            return False

        try:
            with open(self.path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if not lines:
                return False

            records = [json.loads(line.strip()) for line in lines if line.strip()]

            if not records:
                return False

            # Genesis check
            genesis = records[0]
            if genesis.get("seq") != 0 or genesis.get("prev_hash") != self.GENESIS_PREV_HASH:
                return False

            # Chain integrity check
            for i in range(1, len(records)):
                if records[i]["prev_hash"] != records[i-1]["entry_hash"]:
                    return False

            # Check last hash matches
            if records[-1]["entry_hash"] != self._last_hash:
                return False

            return True
        except Exception:
            return False