"""Kian one-time gate code service (M35.1).

A gate service that issues and verifies a one-time code. Kian cannot see or
approve the code — the code is issued by the gate service and verified by it.
The code is bound to the proposer's identity and expires after a TTL.

Design:
- Codes are 6-character alphanumeric (unambiguous alphabet)
- 5-minute TTL, single use
- Bound to the proposer's identity (channel + user_id_hash)
- Fail-closed: any failure → DENY
- No code is ever visible to Kian
"""
from __future__ import annotations

import hashlib
import secrets
import time
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

# Unambiguous alphabet: no 0/O, 1/I, 5/S, 8/B confusion
_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ2346789"
_CODE_LENGTH = 6
_DEFAULT_TTL_S = 300  # 5 minutes
_MAX_ATTEMPTS = 5


@dataclass(frozen=True)
class GateCode:
    """One-time gate code. Kian never sees this."""
    code_hash: str  # sha256 of the code, never the code itself
    proposer_id_hash: str
    action: str
    summary_fa: str
    created_at: float
    expires_at: float
    used: bool = False

    def is_expired(self, now: float | None = None) -> bool:
        return (now or time.time()) > self.expires_at


@dataclass
class GateService:
    """Issues and verifies one-time gate codes.

    Kian cannot see or approve the code — the code is issued by this service
    and verified by this service. The code is bound to the proposer's identity.
    """
    codes: Dict[str, GateCode] = field(default_factory=dict)
    ttl_s: int = _DEFAULT_TTL_S
    max_attempts: int = _MAX_ATTEMPTS
    _attempt_counts: Dict[str, int] = field(default_factory=dict)

    def issue(self, proposer_id_hash: str, action: str, summary_fa: str) -> GateCode:
        """Issue a new gate code. Returns the code object (without the raw code)."""
        code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))
        now = time.time()
        gate = GateCode(
            code_hash=hashlib.sha256(code.encode("utf-8")).hexdigest(),
            proposer_id_hash=proposer_id_hash,
            action=action,
            summary_fa=summary_fa,
            created_at=now,
            expires_at=now + self.ttl_s,
        )
        self.codes[gate.code_hash] = gate
        self._attempt_counts[gate.code_hash] = 0
        return gate

    def issue_with_code(
        self, proposer_id_hash: str, action: str, summary_fa: str
    ) -> Tuple[GateCode, str]:
        """Issue a new gate code. Returns both the code object and the raw code.

        This is a testing helper - Kian never sees the raw code.
        """
        code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))
        now = time.time()
        gate = GateCode(
            code_hash=hashlib.sha256(code.encode("utf-8")).hexdigest(),
            proposer_id_hash=proposer_id_hash,
            action=action,
            summary_fa=summary_fa,
            created_at=now,
            expires_at=now + self.ttl_s,
        )
        self.codes[gate.code_hash] = gate
        self._attempt_counts[gate.code_hash] = 0
        return gate, code

    def verify(self, code: str, proposer_id_hash: str) -> Tuple[bool, str, Optional[GateCode]]:
        """Verify a gate code. Returns (success, reason, gate_code).

        The code is hashed before lookup — the raw code is never stored.
        """
        if not code or not isinstance(code, str):
            return False, "INVALID_CODE", None

        code_hash = hashlib.sha256(code.strip().upper().encode("utf-8")).hexdigest()
        gate = self.codes.get(code_hash)

        if gate is None:
            return False, "CODE_NOT_FOUND", None

        # Check expiry
        if gate.is_expired():
            del self.codes[code_hash]
            return False, "EXPIRED", None

        # Check single use
        if gate.used:
            return False, "ALREADY_USED", None

        # Check identity binding
        if gate.proposer_id_hash != proposer_id_hash:
            self._attempt_counts[code_hash] = self._attempt_counts.get(code_hash, 0) + 1
            if self._attempt_counts[code_hash] >= self.max_attempts:
                del self.codes[code_hash]
                return False, "WRONG_IDENTITY_BURNED", None
            return False, "WRONG_IDENTITY", None

        # Success — mark as used
        used_gate = GateCode(
            code_hash=gate.code_hash,
            proposer_id_hash=gate.proposer_id_hash,
            action=gate.action,
            summary_fa=gate.summary_fa,
            created_at=gate.created_at,
            expires_at=gate.expires_at,
            used=True,
        )
        self.codes[code_hash] = used_gate
        return True, "OK", used_gate

    def cleanup_expired(self) -> int:
        """Remove expired codes. Returns count removed."""
        now = time.time()
        expired = [k for k, g in self.codes.items() if g.is_expired(now)]
        for k in expired:
            del self.codes[k]
        return len(expired)

    def count_active(self) -> int:
        """Count active (non-expired, non-used) codes."""
        now = time.time()
        return sum(1 for g in self.codes.values() if not g.is_expired(now) and not g.used)


class GateServiceError(Exception):
    """Raised when gate service operations fail."""
    pass