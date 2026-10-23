"""Kian owner_dialogue thread in long-term memory (M35.1).

One owner_dialogue thread in the long-term memory (vision §14.4).
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

# Memory directory under data/
_MEMORY_DIR = Path("data/memory")
_OWNER_DIALOGUE_FILE = _MEMORY_DIR / "owner_dialogue.jsonl"


@dataclass
class OwnerDialogueMessage:
    """A message in the owner dialogue thread."""
    seq: int
    timestamp: float
    channel: str
    user_id_hash: str
    role: str  # user | kian | system
    content: str  # redacted before writing
    response_to_seq: Optional[int] = None
    summary_fa: Optional[str] = None


@dataclass
class OwnerDialogueThread:
    """The owner dialogue thread."""
    messages: List[OwnerDialogueMessage] = field(default_factory=list)
    last_seq: int = 0
    ttl_seconds: int = 86400  # 24 hours in memory


class OwnerDialogueMemory:
    """Long-term memory for the owner dialogue thread.

    Stored as append-only JSONL under data/memory/owner_dialogue.jsonl.
    Text is redacted before writing.
    """

    # Sensitive patterns to redact
    REDACTION_PATTERNS = [
        r"(?:API_KEY|SECRET_KEY|PRIVATE_KEY|BEARER_TOKEN)[^\s]*",
        r"\b[A-Za-z0-9+/]{40,}\b",  # long base64 strings
        r"\b[A-Fa-f0-9]{64}\b",  # hex hashes
        r"address: [0-9xXa-fA-F]+",
        r"[A-Za-z0-9]{32,}@[A-Za-z0-9]+\.[A-Za-z]+",  # email patterns
        r"sk-[A-Za-z0-9]+",  # Stripe/OpenAI-like keys
    ]

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else _OWNER_DIALOGUE_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize message storage
        self.messages: List[OwnerDialogueMessage] = []
        self.last_seq: int = 0

        # Load existing messages from disk
        self._load_from_disk()

    def _redact_text(self, text: str) -> str:
        """Remove sensitive patterns from text before writing."""
        import re
        redacted = text
        for pattern in self.REDACTION_PATTERNS:
            redacted = re.sub(pattern, "[REDACTED]", redacted, flags=re.IGNORECASE)
        return redacted

    def _load_from_disk(self) -> None:
        """Load messages from disk. Limited to last 1000 entries for memory efficiency."""
        if not self.path.exists():
            return

        from collections import deque
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                tail_lines = deque((line.strip() for line in f if line.strip()), maxlen=1000)
            for line in tail_lines:
                data = json.loads(line)
                msg = OwnerDialogueMessage(
                    seq=data["seq"],
                    timestamp=data["timestamp"],
                    channel=data["channel"],
                    user_id_hash=data["user_id_hash"],
                    role=data["role"],
                    content=data["content"],
                    response_to_seq=data.get("response_to_seq"),
                    summary_fa=data.get("summary_fa"),
                )
                self.messages.append(msg)
                self.last_seq = max(self.last_seq, msg.seq)
        except (json.JSONDecodeError, KeyError) as e:
            raise RuntimeError(f"Failed to load owner dialogue: {e}")

    def _append_one_to_disk(self, msg: OwnerDialogueMessage) -> None:
        """Append a single new message to disk."""
        try:
            with open(self.path, "a", encoding="utf-8", buffering=1) as f:
                content_dict = {
                    "seq": msg.seq,
                    "timestamp": msg.timestamp,
                    "channel": msg.channel,
                    "user_id_hash": msg.user_id_hash,
                    "role": msg.role,
                    "content": msg.content,
                    "response_to_seq": msg.response_to_seq,
                    "summary_fa": msg.summary_fa,
                }
                f.write(json.dumps(content_dict, ensure_ascii=False) + "\n")
        except OSError as e:
            raise RuntimeError(f"Failed to append owner dialogue: {e}")

    def save_to_disk(self) -> None:
        """Write current bounded messages to disk without duplicating history."""
        if not self.messages:
            return

        try:
            with open(self.path, "w", encoding="utf-8", buffering=1) as f:
                for msg in self.messages[-1000:]:
                    content_dict = {
                        "seq": msg.seq,
                        "timestamp": msg.timestamp,
                        "channel": msg.channel,
                        "user_id_hash": msg.user_id_hash,
                        "role": msg.role,
                        "content": msg.content,
                        "response_to_seq": msg.response_to_seq,
                        "summary_fa": msg.summary_fa,
                    }
                    f.write(json.dumps(content_dict, ensure_ascii=False) + "\n")
        except OSError as e:
            raise RuntimeError(f"Failed to save owner dialogue: {e}")

    def add_message(
        self,
        channel: str,
        user_id_hash: str,
        role: str,
        content: str,
        response_to_seq: Optional[int] = None,
        summary_fa: Optional[str] = None,
    ) -> OwnerDialogueMessage:
        """Add a message to the thread. Text is redacted before writing."""
        safe_content = self._redact_text(content)

        msg = OwnerDialogueMessage(
            seq=self.last_seq + 1,
            timestamp=time.time(),
            channel=channel,
            user_id_hash=user_id_hash,
            role=role,
            content=safe_content,
            response_to_seq=response_to_seq,
            summary_fa=summary_fa,
        )

        self.messages.append(msg)
        self.last_seq = msg.seq

        # Append single new message to disk
        self._append_one_to_disk(msg)

        # Prune old messages (keep last 1000)
        if len(self.messages) > 1000:
            self.messages = self.messages[-1000:]
            self.last_seq = self.messages[-1].seq

        return msg

    def get_context(
        self,
        limit: int = 10,
        include_response_to: bool = True,
    ) -> str:
        """Get the recent conversation context for Kian."""
        recent = self.messages[-limit:] if self.messages else []

        lines = []
        for msg in recent:
            role_label = {
                "user": "Owner",
                "kian": "Kian",
                "system": "System",
            }.get(msg.role, msg.role)

            header = f"[{role_label}] #{msg.seq}"
            if msg.summary_fa:
                header += f" — {msg.summary_fa}"

            content = msg.content
            if not include_response_to and msg.response_to_seq:
                # Truncate the original message that was being responded to
                content = content[:50] + "..."

            lines.append(f"{header}: {content}")

        return "\n".join(lines)

    def get_recent_messages(
        self,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get recent messages as dictionaries."""
        recent = self.messages[-limit:] if self.messages else []
        return [
            {
                "seq": m.seq,
                "timestamp": m.timestamp,
                "channel": m.channel,
                "user_id_hash": m.user_id_hash,
                "role": m.role,
                "content": m.content,
                "summary_fa": m.summary_fa,
            }
            for m in recent
        ]


class OwnerDialogueMemoryError(Exception):
    """Raised when memory operations fail."""
    pass
